"""
FastAPI web app for MVP 1: the same conversion + human review flow MVP
0.5 built for the CLI (entrypoints/convert_attack_cli.py,
entrypoints/_review_input.py), exposed over HTTP instead of a terminal
prompt.

Rerun is deliberately not included in this first web pass — it's left
as a later increment, once experience with the plain review flow here
shows what it should actually need. Correction otherwise has full
parity with the CLI: free text for description and the range's numeric
value, constrained dropdowns for move_type and the range's unit,
assigned_llm_score/edit_note on every decision.

No server-side session state, matching MVP 0.5's own statelessness:
raw_attack and the original classification travel from GET/POST
/convert to POST /review as hidden form fields, not stored anywhere
between requests.

Model-availability handling (ensure_model_available()/
call_llm_with_model_fallback() in entrypoints/_llm_model_selection.py)
is deliberately NOT reused here — it's interactive, built around
input() to ask a human which model to use, which has no meaning inside
an HTTP request/response cycle. A ModelUnavailableError here is caught
and reported as a plain error response instead.
"""
import dataclasses
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
import jinja2
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from monsterforge.config import validation_settings
from monsterforge.db.enums import CardType
from monsterforge.db.pipeline import ClassificationEvent, RawField
from monsterforge.db.seed import seed_reference_data
from monsterforge.db.session import create_all_tables, get_session
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import (
    UnknownAttackRange,
    is_melee,
    raw_to_structured_attack,
)
from monsterforge.transformation.dnd.v3x.converters.attacks_converter import attack_converter
from monsterforge.entrypoints.sample_attacks_web_seed import SAMPLE_ATTACKS_WEB_SEED
from monsterforge.pipeline.attack_pipeline import is_blank_attack
from monsterforge.pipeline.attack_repository import (
    InconsistentActiveClassificationError,
    activate_classification_event,
    compute_fingerprint,
    find_existing_card,
    get_default_game,
    get_human_actor,
    get_llm_actor,
    get_or_create_raw_field,
    record_human_review,
    record_llm_run,
    save_card,
    save_structured_data,
)
from monsterforge.llm.client import get_llm_client
from monsterforge.llm.clients.gemini import ModelUnavailableError
from monsterforge.llm.semantic_classification.attacks import (
    ATTACK_PROMPT_TEMPLATE,
    ATTACK_PROMPT_TEMPLATE_OPTIONS,
    AttackSemanticResult,
    SemanticContextInput,
    classify_attack,
    semantic_result_to_dict,
)
from monsterforge.rendering.move_card_renderer import render_move_card_html_with_edit
from monsterforge.serialization.domain_to_json import card_to_json
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype, MoveType, UnitSystem
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import HumanReview, needs_review

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create the database tables and seed reference rows once, at
    startup — this project has no migration tool, so table creation
    must be triggered explicitly rather than happening on import (see
    db/session.py::create_all_tables())."""
    create_all_tables()
    session = get_session()
    try:
        seed_reference_data(session)
    finally:
        session.close()
    yield


def get_db_session():
    """FastAPI dependency: yields a session scoped to one request, always
    closed afterward. Overridden in tests (tests/ui/conftest.py) to
    yield an isolated in-memory session instead of the real database."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()


app = FastAPI(lifespan=lifespan)
# NOTE:
# Jinja2Templates(directory=...) hardcodes autoescape=jinja2.select_autoescape(),
# whose extension check never matches "*.html.jinja2" (every template in
# this project) — the same silent-autoescape-off gap already found in
# rendering/move_card_renderer.py, undiscovered here until a rationale
# containing an apostrophe broke the hidden semantic_result_json field.
# Passing an explicit env= with autoescape=True is the only way to
# override that default.
templates = Jinja2Templates(env=jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=True,
))

# NOTE:
# raw_fields.Attack.attack_type is deliberately an unconstrained str
# (see parsing/dnd/v3x/raw_fields/attacks.py), not an enum — but
# is_melee()/is_touch() in attacks_converter.py only recognize these
# exact English substrings ("melee" in attack_type.lower(), etc.). A
# free-text web input let a value like "mischia" (not matching any of
# them) silently fall through to "ranged", triggering an LLM range
# lookup for what was actually a melee attack. Constrained to a
# dropdown here for that reason — the CLI keeps free text, since a
# person typing at a terminal is already expected to match the
# parser's vocabulary.
ATTACK_TYPE_OPTIONS = ("melee", "melee touch", "ranged", "ranged touch")


# =====================
# SEMANTIC RESULT (DE)SERIALIZATION
# =====================
def _semantic_result_to_json(result: AttackSemanticResult) -> str:
    """Serialize an AttackSemanticResult for a hidden form field, to
    survive the round trip from POST /convert to POST /review — there's
    no server-side session to hold onto it instead."""
    return json.dumps(semantic_result_to_dict(result))


def _semantic_result_from_json(text: str) -> AttackSemanticResult:
    data = json.loads(text)
    move_range = None

    if data["move_range"]:
        move_range = EffectRange(
            effect_range=data["move_range"]["effect_range"],
            range_unit_system=UnitSystem(data["move_range"]["range_unit_system"]),
        )

    return AttackSemanticResult(
        description=data["description"],
        move_type=MoveType(data["move_type"]),
        move_range=move_range,
        confidence=data["confidence"],
        rationale=data["rationale"],
    )


# =====================
# RANGE CONTEXT HELPERS
# =====================
def _parse_positive_range(range_value: str, range_unit: str) -> EffectRange | None:
    """
    Build an EffectRange from raw form input, deterministically — a
    numeric value plus a unit dropdown is already fixed, structured
    data, so it's built directly rather than round-tripped through the
    LLM's own free-text interpretation of it.

    Returns None if no range value was given (range is optional unless
    the caller has already required it). Raises ValueError if a range
    value is given but isn't a positive integer, or if the unit is
    missing/invalid — a negative or zero range has no real meaning.
    """
    if not range_value.strip():
        return None

    value = int(range_value)
    if value < 1:
        raise ValueError(f"range value must be positive, got {value}.")

    return EffectRange(effect_range=value, range_unit_system=UnitSystem(range_unit))


def _range_context_note(effect_range: EffectRange) -> str:
    """Render an EffectRange as a short sentence to prepend to the LLM's
    additional_description context, so its own confidence reflects that
    the range is already known rather than guessed."""
    unit = "feet" if effect_range.range_unit_system == UnitSystem.IMPERIAL else "meters"
    return f"Range: {effect_range.effect_range} {unit}."


# =====================
# SEMANTIC CONTEXT HELPERS
# =====================
def _semantic_context_from_form(
        additional_description: str,
        creature_description: str,
        creature_subtype: str) -> SemanticContextInput:
    return SemanticContextInput(
        additional_description=additional_description or None,
        creature_description=creature_description or None,
        creature_subtype=CreatureSubtype(creature_subtype) if creature_subtype else None,
    )


def _review_form_context(
        raw_attack: RawAttack,
        semantic_context: SemanticContextInput,
        semantic_result: AttackSemanticResult,
        template_name: str,
        image_uri: str,
        raw_field_id: str,
        classification_event_id: str,
        error_message: str | None = None) -> dict:
    """Shared template context for review_form.html.jinja2, built by
    a fresh /convert classification, a revisit via /review/edit, or a
    bounce-back from a failed card build (error_message set — see
    UnknownAttackRange handling in convert()/review()).

    raw_field_id/classification_event_id identify which raw_fields row
    and which specific LLM_RUN classification_events row a decision
    made on this form is about — carried as hidden fields the same way
    raw_attack/semantic_result already are, since there's no
    server-side session to hold onto them instead."""
    return {
        "raw_attack": raw_attack,
        "semantic_context": semantic_context,
        "semantic_result": semantic_result,
        "semantic_result_json": _semantic_result_to_json(semantic_result),
        "template_name": template_name,
        "image_uri": image_uri,
        "raw_field_id": raw_field_id,
        "classification_event_id": classification_event_id,
        "move_types": [move_type.value for move_type in MoveType],
        "unit_systems": [unit.value for unit in UnitSystem],
        "prompt_templates": ATTACK_PROMPT_TEMPLATE_OPTIONS,
        "is_melee": is_melee(raw_attack),
        "error_message": error_message,
    }


# =====================
# DEAD-END RESPONSES
# =====================
def _message_page(message: str, status_code: int = 200) -> HTMLResponse:
    """A plain response for an outcome that produces no card (blank
    input, a classification failure, a rejected review) — always with a
    way back to /convert, rather than a bare dead-end message."""
    return HTMLResponse(f'<p>{message}</p><p><a href="/convert">Home</a></p>', status_code=status_code)


# =====================
# CARD RENDERING
# =====================
def _render_card(
        session: Session,
        raw_field: RawField,
        classification_event: ClassificationEvent,
        raw_attack: RawAttack,
        semantic_result: AttackSemanticResult,
        semantic_context: SemanticContextInput,
        template_name: str,
        image_uri: str) -> HTMLResponse:
    """Build the final card, persist it as structured_data/cards for
    `classification_event`, and activate that event — all three only on
    success. Activation happens here, after the save, deliberately not
    left to the caller: if it happened before (or the caller activated
    it up front), a mid-build failure like UnknownAttackRange would
    leave raw_field pointing at an ACTIVE event with no saved card, the
    exact anomaly find_existing_card() exists to catch on a later
    fingerprint hit."""
    try:
        structured_attack = raw_to_structured_attack(raw_attack, semantic_result)
        move_card = attack_converter(structured_attack, attack_image_uri=image_uri or None)
    except UnknownAttackRange:
        # Re-raised rather than turned into a dead end here: the caller
        # (convert()/review()) has the raw_attack/semantic_result/context
        # needed to send the reviewer back to the correction form
        # instead, where the range fields this error is actually about
        # are right there to fill in.
        raise
    except Exception as exc:
        # NOTE:
        # Deliberately broad: raw_to_structured_attack()/attack_converter()
        # are deterministic regex/rule-based parsing over free-typed input
        # (e.g. an attack_effect like "2d80" or another malformed dice
        # expression) — without this, any parsing failure here reaches
        # the browser as FastAPI's generic, contextless 500 error page,
        # with the actual exception visible only in the server's own
        # terminal, not to whoever is using the form.
        return _message_page(f"Could not build the card: {exc}", status_code=422)

    card_data = json.loads(card_to_json(move_card))

    structured_data = save_structured_data(
        session, raw_field=raw_field, classification_event=classification_event,
        structured_attack=structured_attack,
    )
    save_card(session, structured_data=structured_data, card_data=card_data, card_type=CardType.MOVE_CARD)
    activate_classification_event(session, raw_field=raw_field, event=classification_event)

    edit_form_fields = {
        "raw_attack_name": raw_attack.name,
        "raw_attack_modifier": raw_attack.modifier,
        "raw_attack_attack_type": raw_attack.attack_type,
        "raw_attack_attack_effect": raw_attack.attack_effect,
        "additional_description": semantic_context.additional_description or "",
        "creature_description": semantic_context.creature_description or "",
        "creature_subtype": semantic_context.creature_subtype.value if semantic_context.creature_subtype else "",
        "template_name": template_name,
        "image_uri": image_uri,
        "raw_field_id": raw_field.id,
        "classification_event_id": classification_event.id,
        "semantic_result_json": _semantic_result_to_json(semantic_result),
    }

    return HTMLResponse(render_move_card_html_with_edit(card_data, "/review/edit", edit_form_fields))


def _serve_cached_card(
        session: Session,
        raw_field: RawField,
        active_event: ClassificationEvent,
        template_name: str,
        image_uri: str) -> HTMLResponse:
    """Serve an already-saved card for `raw_field`'s active event —
    the fingerprint cache hit path. No LLM call, no new database row,
    no raw_to_structured_attack()/attack_converter() recomputation: the
    saved card content is passed straight to the renderer as-is.

    Raises:
        InconsistentActiveClassificationError:
            Propagated from find_existing_card() if the active event has
            no saved card — the caller reports this as an error rather
            than silently reclassifying.
    """
    _structured_data, card = find_existing_card(session, active_event)

    edit_form_fields = {
        "raw_attack_name": raw_field.data["name"],
        "raw_attack_modifier": raw_field.data["modifier"],
        "raw_attack_attack_type": raw_field.data["attack_type"],
        "raw_attack_attack_effect": raw_field.data["attack_effect"],
        "additional_description": raw_field.data.get("additional_description") or "",
        "creature_description": raw_field.data.get("creature_description") or "",
        "creature_subtype": raw_field.data.get("creature_subtype") or "",
        "template_name": template_name,
        "image_uri": image_uri,
        "raw_field_id": raw_field.id,
        "classification_event_id": active_event.id,
        "semantic_result_json": json.dumps(active_event.result),
    }

    return HTMLResponse(render_move_card_html_with_edit(card.content, "/review/edit", edit_form_fields))


# =====================
# ROUTES
# =====================
FAVICON_PATH = Path(__file__).resolve().parents[1] / "docs" / "images" / "Web" / "favicon.png"


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(FAVICON_PATH)


@app.get("/convert", response_class=HTMLResponse)
def show_convert_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "convert_form.html.jinja2", {
        "creature_subtypes": [subtype.value for subtype in CreatureSubtype],
        "attack_types": ATTACK_TYPE_OPTIONS,
        "unit_systems": [unit.value for unit in UnitSystem],
        "prompt_templates": ATTACK_PROMPT_TEMPLATE_OPTIONS,
        "sample_attacks": SAMPLE_ATTACKS_WEB_SEED,
    })


@app.post("/convert", response_class=HTMLResponse)
def convert(
        request: Request,
        name: str = Form(...),
        modifier: str = Form(""),
        attack_type: Literal["", "melee", "melee touch", "ranged", "ranged touch"] = Form(""),
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
        return _message_page("No card produced: the submitted attack was blank.")

    # NOTE:
    # Not a Literal[...] like attack_type — that would duplicate the
    # path list ATTACK_PROMPT_TEMPLATE_OPTIONS already exists to be the
    # single source of. Checked against the option paths directly instead.
    if template_name not in {option.path for option in ATTACK_PROMPT_TEMPLATE_OPTIONS}:
        return _message_page(f"Unknown prompt template: {template_name!r}.", status_code=422)

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
        return _message_page(
            "A ranged attack needs either a range value and unit, or a description "
            "mentioning its range — neither was provided.",
            status_code=422,
        )

    try:
        explicit_range = None if is_melee(raw_attack) else _parse_positive_range(range_value, range_unit)
    except ValueError as exc:
        return _message_page(f"Invalid range value: {exc}", status_code=422)

    semantic_context = _semantic_context_from_form(additional_description, creature_description, creature_subtype)

    if explicit_range is not None:
        range_note = _range_context_note(explicit_range)
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
            return _message_page("This attack was previously rejected.", status_code=422)
        try:
            return _serve_cached_card(session, raw_field, active_event, template_name, image_uri)
        except InconsistentActiveClassificationError as exc:
            return _message_page(f"Could not load the saved card: {exc}", status_code=500)

    try:
        semantic_result = classify_attack(
            raw_attack=raw_attack,
            additional_description=semantic_context.additional_description,
            creature_description=semantic_context.creature_description,
            creature_subtype=semantic_context.creature_subtype,
            template_name=template_name,
        )
    except ModelUnavailableError as exc:
        return _message_page(f"The configured LLM model is unavailable: {exc}", status_code=503)
    except Exception as exc:
        return _message_page(f"Classification failed: {exc}", status_code=502)

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
            _review_form_context(
                raw_attack, semantic_context, semantic_result, template_name, image_uri,
                raw_field_id=raw_field.id, classification_event_id=llm_event.id,
            ),
        )

    try:
        return _render_card(
            session, raw_field, llm_event, raw_attack, semantic_result, semantic_context,
            template_name, image_uri,
        )
    except UnknownAttackRange as exc:
        return templates.TemplateResponse(
            request, "review_form.html.jinja2",
            _review_form_context(
                raw_attack, semantic_context, semantic_result, template_name, image_uri,
                raw_field_id=raw_field.id, classification_event_id=llm_event.id,
                error_message=f"Could not build the card: {exc} Provide a range below and try again.",
            ),
        )


@app.post("/review/edit", response_class=HTMLResponse)
def edit_review(
        request: Request,
        raw_attack_name: str = Form(""),
        raw_attack_modifier: str = Form(""),
        raw_attack_attack_type: str = Form(""),
        raw_attack_attack_effect: str = Form(""),
        additional_description: str = Form(""),
        creature_description: str = Form(""),
        creature_subtype: str = Form(""),
        image_uri: str = Form(""),
        raw_field_id: str = Form(...),
        classification_event_id: str = Form(...),
        semantic_result_json: str = Form(...),
        template_name: str = Form(...),
        ) -> HTMLResponse:
    """
    Reopens the review form for an already-produced card — reachable
    from the "Edit this classification" button render_move_card_html_
    with_edit() adds to every rendered card, not just ones that already
    went through review. No LLM call here: the classification is the
    one already carried in semantic_result_json, not reclassified.
    """
    raw_attack = RawAttack(
        name=raw_attack_name,
        modifier=raw_attack_modifier,
        attack_type=raw_attack_attack_type,
        attack_effect=raw_attack_attack_effect,
    )
    semantic_context = _semantic_context_from_form(additional_description, creature_description, creature_subtype)
    semantic_result = _semantic_result_from_json(semantic_result_json)

    return templates.TemplateResponse(
        request, "review_form.html.jinja2",
        _review_form_context(
            raw_attack, semantic_context, semantic_result, template_name, image_uri,
            raw_field_id=raw_field_id, classification_event_id=classification_event_id,
        ),
    )


def _parse_assigned_llm_score(raw_value: str) -> float | None:
    return float(raw_value) if raw_value.strip() else None


@app.post("/review", response_class=HTMLResponse)
def review(
        request: Request,
        # NOTE:
        # These four carry the original raw attack through the hidden
        # form fields, unchanged since /convert. They default to "" (not
        # required) rather than Form(...): FastAPI treats an empty
        # string on a required Form field as if it weren't sent at all,
        # which turned a legitimately blank modifier into a hard 422
        # ("Field required") instead of the empty value it actually is.
        raw_attack_name: str = Form(""),
        raw_attack_modifier: str = Form(""),
        raw_attack_attack_type: str = Form(""),
        raw_attack_attack_effect: str = Form(""),
        additional_description: str = Form(""),
        creature_description: str = Form(""),
        creature_subtype: str = Form(""),
        image_uri: str = Form(""),
        raw_field_id: str = Form(...),
        classification_event_id: str = Form(...),
        template_name: str = Form(...),
        semantic_result_json: str = Form(...),
        decision: str = Form(...),
        name: str = Form(""),
        description: str = Form(""),
        move_type: str = Form(""),
        range_value: str = Form(""),
        range_unit: str = Form(""),
        assigned_llm_score: str = Form(""),
        edit_note: str = Form(""),
        rerun_note: str = Form(""),
        rerun_template_name: str = Form(""),
        session: Session = Depends(get_db_session),
        ) -> HTMLResponse:
    raw_attack = RawAttack(
        name=raw_attack_name,
        modifier=raw_attack_modifier,
        attack_type=raw_attack_attack_type,
        attack_effect=raw_attack_attack_effect,
    )
    semantic_context = _semantic_context_from_form(additional_description, creature_description, creature_subtype)
    original_result = _semantic_result_from_json(semantic_result_json)
    raw_field = session.get(RawField, raw_field_id)
    referenced_event = session.get(ClassificationEvent, classification_event_id)

    if decision == "reject":
        review_event = record_human_review(
            session, raw_field=raw_field, referenced_event=referenced_event,
            review=HumanReview(status=ValidationStatus.REJECTED, result=None,
                                assigned_llm_score=_parse_assigned_llm_score(assigned_llm_score),
                                edit_note=edit_note or None),
            actor=get_human_actor(session),
        )
        activate_classification_event(session, raw_field=raw_field, event=review_event)
        return _message_page("No card produced: the classification was rejected.")

    if decision == "rerun":
        # NOTE:
        # Mirrors _review_input.py's CLI rerun, but as one HTTP round
        # trip instead of a loop inside the same process: a fresh
        # classify_attack() call, an optional note appended to
        # additional_description, and optionally a different template.
        # On any failure, re-shows review_form.html.jinja2 with the
        # ORIGINAL (pre-rerun) classification untouched plus an error
        # banner — same principle as the UnknownAttackRange bounce-back
        # below: a failed action here must not discard the reviewer's
        # already-reviewed state. No fingerprint check on this branch —
        # rerun is a deliberate manual retry, always a new attempt, never
        # deduplicated against the cache (see compute_fingerprint()).
        if rerun_template_name not in {option.path for option in ATTACK_PROMPT_TEMPLATE_OPTIONS}:
            return templates.TemplateResponse(
                request, "review_form.html.jinja2",
                _review_form_context(
                    raw_attack, semantic_context, original_result, template_name, image_uri,
                    raw_field_id=raw_field_id, classification_event_id=classification_event_id,
                    error_message=f"Unknown prompt template: {rerun_template_name!r}.",
                ),
            )

        rerun_context = semantic_context
        if rerun_note.strip():
            combined_description = (
                f"{semantic_context.additional_description}\n{rerun_note}"
                if semantic_context.additional_description else rerun_note
            )
            rerun_context = dataclasses.replace(semantic_context, additional_description=combined_description)

        try:
            new_result = classify_attack(
                raw_attack=raw_attack,
                additional_description=rerun_context.additional_description,
                creature_description=rerun_context.creature_description,
                creature_subtype=rerun_context.creature_subtype,
                template_name=rerun_template_name,
            )
        except ModelUnavailableError as exc:
            error_message = f"The configured LLM model is unavailable: {exc}"
        except Exception as exc:
            error_message = f"Rerun failed: {exc}"
        else:
            new_event = record_llm_run(
                session, raw_field=raw_field, semantic_result=new_result, actor=get_llm_actor(session),
                prompt_name=rerun_template_name, model_name=get_llm_client().model_name,
                confidence_threshold=validation_settings.CONFIDENCE_THRESHOLD,
                decision=None, rerun_note=rerun_note or None,
            )
            return templates.TemplateResponse(
                request, "review_form.html.jinja2",
                _review_form_context(
                    raw_attack, rerun_context, new_result, rerun_template_name, image_uri,
                    raw_field_id=raw_field_id, classification_event_id=new_event.id,
                ),
            )

        return templates.TemplateResponse(
            request, "review_form.html.jinja2",
            _review_form_context(
                raw_attack, semantic_context, original_result, template_name, image_uri,
                raw_field_id=raw_field_id, classification_event_id=classification_event_id,
                error_message=error_message,
            ),
        )

    if decision == "correct":
        if not name.strip():
            return _message_page("Name cannot be blank.", status_code=422)

        raw_attack = dataclasses.replace(raw_attack, name=name)

        try:
            corrected_range = _parse_positive_range(range_value, range_unit)
        except ValueError as exc:
            return _message_page(f"Invalid range value: {exc}", status_code=422)

        final_result = dataclasses.replace(
            original_result,
            description=description,
            move_type=MoveType(move_type),
            move_range=corrected_range,
        )
        review_status = ValidationStatus.CORRECTED
    else:
        final_result = original_result
        review_status = ValidationStatus.APPROVED

    review_event = record_human_review(
        session, raw_field=raw_field, referenced_event=referenced_event,
        review=HumanReview(status=review_status, result=final_result,
                            assigned_llm_score=_parse_assigned_llm_score(assigned_llm_score),
                            edit_note=edit_note or None),
        actor=get_human_actor(session),
    )

    try:
        return _render_card(
            session, raw_field, review_event, raw_attack, final_result, semantic_context,
            template_name, image_uri,
        )
    except UnknownAttackRange as exc:
        return templates.TemplateResponse(
            request, "review_form.html.jinja2",
            _review_form_context(
                raw_attack, semantic_context, final_result, template_name, image_uri,
                raw_field_id=raw_field_id, classification_event_id=classification_event_id,
                error_message=f"Could not build the card: {exc} Provide a range below and try again.",
            ),
        )
