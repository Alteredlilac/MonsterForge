"""
GET/POST /convert -- collect a raw D&D 3.x attack and classify it.

A cache hit (the fingerprint already has an active, non-rejected
classification event) skips the LLM call entirely and serves the
already-saved card via responses.serve_cached_card(). Otherwise this
classifies, then either shows the review form (low confidence / forced
review) or builds and persists the card directly.
"""
import dataclasses
from typing import Literal

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from monsterforge.config import validation_settings
from monsterforge.db.pipeline import ClassificationEvent
from monsterforge.db.session import get_db_session
from monsterforge.entrypoints.sample_attacks_web_seed import SAMPLE_ATTACKS_WEB_SEED
from monsterforge.llm.client import get_llm_client
from monsterforge.llm.clients.gemini import ModelUnavailableError
from monsterforge.llm.semantic_classification.attacks import (
    ATTACK_PROMPT_TEMPLATE,
    ATTACK_PROMPT_TEMPLATE_OPTIONS,
    classify_attack,
    range_context_note,
)
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import (
    ATTACK_TYPE_OPTIONS,
    UnknownAttackRange,
    is_melee,
)
from monsterforge.pipeline.attack_pipeline import is_blank_attack
from monsterforge.pipeline.attack_repository import compute_fingerprint, get_or_create_raw_field, record_llm_run
from monsterforge.pipeline.attack_repository_queries import InconsistentActiveClassificationError
from monsterforge.pipeline.reference_lookups import get_default_game, get_llm_actor
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype, UnitSystem
from monsterforge.ui.context import parse_positive_range, semantic_context_from_form
from monsterforge.ui.jinja_templating import templates
from monsterforge.ui.responses import message_page, render_card, review_form_context, serve_cached_card
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import needs_review

router = APIRouter()


@router.get("/convert", response_class=HTMLResponse)
def show_convert_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "convert_form.html.jinja2", {
        "creature_subtypes": [subtype.value for subtype in CreatureSubtype],
        "attack_types": ATTACK_TYPE_OPTIONS,
        "unit_systems": [unit.value for unit in UnitSystem],
        "prompt_templates": ATTACK_PROMPT_TEMPLATE_OPTIONS,
        "sample_attacks": SAMPLE_ATTACKS_WEB_SEED,
    })


@router.post("/convert", response_class=HTMLResponse)
def convert(
        request: Request,
        name: str = Form(...),
        modifier: str = Form(""),
        attack_type: Literal["", *ATTACK_TYPE_OPTIONS] = Form(""),
        attack_effect: str = Form(""),
        additional_description: str = Form(""),
        creature_description: str = Form(""),
        creature_subtype: str = Form(""),
        image_uri: str = Form(""),
        force_review: bool = Form(False),
        range_value: str = Form(""),
        range_unit: str = Form(""),
        template_name: str = Form(ATTACK_PROMPT_TEMPLATE),
        session: Session = Depends(get_db_session),
        ) -> HTMLResponse:
    raw_attack = RawAttack(name=name, modifier=modifier, attack_type=attack_type, attack_effect=attack_effect)

    if is_blank_attack(raw_attack):
        return message_page("No card produced: the submitted attack was blank.")

    # NOTE:
    # Not a Literal[...] like attack_type — that would duplicate the
    # path list ATTACK_PROMPT_TEMPLATE_OPTIONS already exists to be the
    # single source of. Checked against the option paths directly instead.
    if template_name not in {option.path for option in ATTACK_PROMPT_TEMPLATE_OPTIONS}:
        return message_page(f"Unknown prompt template: {template_name!r}.", status_code=422)

    # NOTE:
    # A ranged/ranged touch attack needs to resolve a distance somehow —
    # either from an explicit range value/unit here, or from prose in
    # additional_description (the existing, already-reliable path for
    # most real attacks). Only required as a last resort, when neither
    # is present, rather than forcing structured input on attacks that
    # already work fine from context alone.
    if (attack_type in ("ranged", "ranged touch")
            and not additional_description.strip()
            and not (range_value.strip() and range_unit.strip())):
        return message_page(
            "A ranged attack needs either a range value and unit, or a description "
            "mentioning its range — neither was provided.",
            status_code=422,
        )

    try:
        explicit_range = None if is_melee(raw_attack) else parse_positive_range(range_value, range_unit)
    except ValueError as exc:
        return message_page(f"Invalid range value: {exc}", status_code=422)

    semantic_context = semantic_context_from_form(additional_description, creature_description, creature_subtype)

    if explicit_range is not None:
        range_note = range_context_note(explicit_range)
        semantic_context = dataclasses.replace(
            semantic_context,
            additional_description=(
                f"{range_note} {semantic_context.additional_description}"
                if semantic_context.additional_description else range_note
            ),
        )

    # NOTE:
    # get_or_create_raw_field() is always called, never conditioned on a
    # separate "does an active result exist?" check first — see its own
    # docstring for why (a raw_field can already exist for this
    # fingerprint with no active event yet, and checking a different way
    # around risks an IntegrityError on fingerprint's UNIQUE constraint).
    fingerprint = compute_fingerprint(raw_attack, semantic_context.creature_subtype, explicit_range)
    raw_field = get_or_create_raw_field(
        session, game_id=get_default_game(session).id, raw_attack=raw_attack,
        semantic_context=semantic_context, fingerprint=fingerprint,
    )

    if raw_field.current_classification_event_id is not None:
        active_event = session.get(ClassificationEvent, raw_field.current_classification_event_id)
        if active_event.decision == ValidationStatus.REJECTED:
            return message_page("This attack was previously rejected.", status_code=422)
        try:
            return serve_cached_card(session, raw_field, active_event, template_name, image_uri)
        except InconsistentActiveClassificationError as exc:
            return message_page(f"Could not load the saved card: {exc}", status_code=500)

    try:
        semantic_result = classify_attack(
            raw_attack=raw_attack,
            additional_description=semantic_context.additional_description,
            creature_description=semantic_context.creature_description,
            creature_subtype=semantic_context.creature_subtype,
            template_name=template_name,
        )
    except ModelUnavailableError as exc:
        return message_page(f"The configured LLM model is unavailable: {exc}", status_code=503)
    except Exception as exc:
        return message_page(f"Classification failed: {exc}", status_code=502)

    if explicit_range is not None:
        # The form's own range/unit is trusted over whatever the LLM
        # returned for move_range — it was already handed to the LLM as
        # context above (so confidence reflects that it had the value),
        # but the actual domain value used downstream comes from the
        # deterministic form input, not the LLM's own reconstruction of it.
        semantic_result = dataclasses.replace(semantic_result, move_range=explicit_range)

    # NOTE:
    # force_review is a per-request local value, never written to
    # config.validation_settings.ALWAYS_ON — that setting is shared,
    # process-wide, mutable state, safe for a single sequential batch
    # script (see entrypoints/collect_real_pipeline_conversions_with_simulated_review.py)
    # but not for a web server handling concurrent requests: mutating it
    # here could leak "always review" into an unrelated request that
    # never asked for it.
    requires_review = force_review or needs_review(confidence=semantic_result.confidence)

    # decision is resolved here, before the row is even written, and
    # never changed afterward — classification_events' append-only rule
    # (see db/pipeline.py) allows only `status` to change post-write.
    llm_event = record_llm_run(
        session, raw_field=raw_field, semantic_result=semantic_result, actor=get_llm_actor(session),
        prompt_name=template_name, model_name=get_llm_client().model_name,
        confidence_threshold=validation_settings.CONFIDENCE_THRESHOLD,
        decision=None if requires_review else ValidationStatus.AUTO_APPROVED,
    )

    if requires_review:
        # Deliberately not activated: PENDING until a human decides, in
        # /review — activating an unresolved event here would make an
        # unreviewed result look like the raw_field's current one.
        return templates.TemplateResponse(
            request, "review_form.html.jinja2",
            review_form_context(
                raw_attack, semantic_context, semantic_result, template_name, image_uri,
                raw_field_id=raw_field.id, classification_event_id=llm_event.id,
            ),
        )

    try:
        return render_card(
            session, raw_field, llm_event, raw_attack, semantic_result, semantic_context,
            template_name, image_uri,
        )
    except UnknownAttackRange as exc:
        return templates.TemplateResponse(
            request, "review_form.html.jinja2",
            review_form_context(
                raw_attack, semantic_context, semantic_result, template_name, image_uri,
                raw_field_id=raw_field.id, classification_event_id=llm_event.id,
                error_message=f"Could not build the card: {exc} Provide a range below and try again.",
            ),
        )
