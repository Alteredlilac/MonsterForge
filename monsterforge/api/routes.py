"""
GET/POST /api/cards, GET /api/cards/{raw_field_id} -- JSON access to the
persistence layer's saved cards (see PERSISTENCE.md), for a
non-interactive consumer rather than a person browsing the web UI.

Reads are the JSON equivalent of GET /library/cards/GET /library/cards/{id}
(ui/routes/library.py), filtered to real cards only -- a raw_field with
no active event, or whose active event is REJECTED, has nothing to
return here. Creation mirrors ui/routes/convert.py's own /convert
sequence (fingerprint, cache hit, classify, confidence gate, build and
persist), duplicated rather than reused: that route always returns
HTMLResponse with web-specific edit-form fields, a contract this API
has no use for. Human review (approve/correct/reject/rerun) stays a
web-only, human-only action on purpose: this API can create or rerun a
classification, but never resolves an ambiguous one itself -- that
decision stays exclusively on the web, through POST /review.

Every route reuses the same repository functions ui/routes/ already
calls, and the same get_db_session dependency -- neither is duplicated
here, only the response shape (JSON instead of HTML) differs. Both this
package and ui/ depend on db/ for that dependency; neither depends on
the other, keeping the two branches independent all the way down to
which app serves them (see api/app.py).
"""
import dataclasses
import json
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from monsterforge.api.models import AttackCreateRequest, ErrorResponse, PendingReviewResponse
from monsterforge.config import validation_settings
from monsterforge.db.enums import CardType
from monsterforge.db.pipeline import ClassificationEvent, RawField
from monsterforge.db.session import get_db_session
from monsterforge.llm.client import get_llm_client
from monsterforge.llm.clients.gemini import ModelUnavailableError
from monsterforge.llm.semantic_classification.attacks import (
    ATTACK_PROMPT_TEMPLATE_OPTIONS,
    AttackSemanticResult,
    SemanticContextInput,
    classify_attack,
    range_context_note,
)
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import (
    is_melee,
    raw_to_structured_attack,
)
from monsterforge.pipeline.attack_repository import (
    activate_classification_event,
    compute_fingerprint,
    get_or_create_raw_field,
    record_llm_run,
    save_card,
    save_structured_data,
)
from monsterforge.pipeline.attack_repository_queries import (
    InconsistentActiveClassificationError,
    find_existing_card,
    list_saved_cards,
)
from monsterforge.pipeline.reference_lookups import get_default_game, get_llm_actor
from monsterforge.serialization.domain_to_json import card_to_json
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.transformation.dnd.v3x.converters.attacks_converter import attack_converter
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import needs_review

router = APIRouter(prefix="/api")


# =====================
# GET /api/cards
# =====================
@router.get("/cards")
def list_cards(q: str = "", session: Session = Depends(get_db_session)) -> list[dict[str, Any]]:
    """
    List every attack with a real, currently active card.

    q, if given, filters by the attack's name (substring, case-insensitive)
    or id (prefix) -- same matching rule as GET /library/cards.

    Reuses list_saved_cards() as-is (see its own docstring for the exact
    shape of each entry) rather than a new repository function: the only
    difference from the library's own listing is dropping raw_fields with
    no move_card at all (a REJECTED active event, kept in the library so
    a reviewer can find and reactivate an older result, but with no card
    for a read-only API consumer to receive).
    """
    query = q.strip()
    entries = list_saved_cards(session, query=query or None)
    return [entry for entry in entries if entry["move_card"] is not None]


# =====================
# GET /api/cards/{raw_field_id}
# =====================
@router.get(
    "/cards/{raw_field_id}",
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def get_card(raw_field_id: str, session: Session = Depends(get_db_session)) -> dict[str, Any]:
    """
    Return one saved card's full content (see serialization.domain_to_
    json.card_to_json()), found by raw_field_id -- the same lookup
    ui/routes/library.py::view_saved_card() does, JSON instead of HTML.

    card.content is returned as-is, never rebuilt from raw_to_structured_
    attack()/attack_converter(): the pipeline stays one-way (raw ->
    structured -> domain, never the reverse), the same rule the web UI's
    own cache-hit path already follows for the same reason.
    """
    raw_field = session.get(RawField, raw_field_id)
    if raw_field is None or raw_field.current_classification_event_id is None:
        return JSONResponse({"error": "No saved card found for that id."}, status_code=404)

    active_event = session.get(ClassificationEvent, raw_field.current_classification_event_id)
    if active_event.decision == ValidationStatus.REJECTED:
        return JSONResponse({"error": "This attack was previously rejected — no card to show."}, status_code=422)

    try:
        _structured_data, card = find_existing_card(session, active_event)
    except InconsistentActiveClassificationError as exc:
        return JSONResponse({"error": f"Could not load the saved card: {exc}"}, status_code=500)

    return card.content


# =====================
# CARD CREATION
# =====================
def _build_and_persist_card(
        session: Session,
        raw_field: RawField,
        classification_event: ClassificationEvent,
        raw_attack: RawAttack,
        semantic_result: AttackSemanticResult,
        image_uri: str | None) -> JSONResponse:
    """
    Build the final card, persist it as structured_data/cards for
    `classification_event`, and activate that event -- the JSON
    equivalent of ui/responses.py::render_card(), duplicated rather than
    reused (see this module's own docstring for why). Activation happens
    only after a successful save, same reasoning as render_card(): a
    mid-build failure must never leave `raw_field` pointing at an ACTIVE
    event with no saved card, the exact anomaly find_existing_card()
    exists to catch on a later fingerprint hit.

    Any build failure (UnknownAttackRange included) is reported as a
    plain 422 rather than re-raised for a caller to redirect elsewhere:
    unlike the web UI, this API has no review form to bounce back to.
    """
    try:
        structured_attack = raw_to_structured_attack(raw_attack, semantic_result)
        move_card = attack_converter(structured_attack, attack_image_uri=image_uri or None)
    except Exception as exc:
        return JSONResponse({"error": f"Could not build the card: {exc}"}, status_code=422)

    card_data = json.loads(card_to_json(move_card))

    structured_data = save_structured_data(
        session, raw_field=raw_field, classification_event=classification_event,
        structured_attack=structured_attack,
    )
    save_card(session, structured_data=structured_data, card_data=card_data, card_type=CardType.MOVE_CARD)
    activate_classification_event(session, raw_field=raw_field, event=classification_event)

    return JSONResponse(card_data, status_code=201)


# =====================
# POST /api/cards
# =====================
@router.post(
    "/cards",
    responses={
        202: {"model": PendingReviewResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def create_card(payload: AttackCreateRequest, session: Session = Depends(get_db_session)) -> JSONResponse:
    """
    Create (or reuse) a card for the submitted attack.

    Mirrors /convert's own sequence exactly: a fingerprint hit against
    an already-rejected event reports the same 422 instead of
    reclassifying; a fingerprint hit against any other active event is
    served back unchanged (no LLM call, no new database row); otherwise
    the attack is classified, gated by the exact same needs_review()
    check /convert uses -- reading the same shared confidence threshold,
    never a value the request itself supplies, so the same attack at the
    same confidence resolves identically on both channels -- and either
    reported as pending_review or built, persisted, and returned.
    """
    if payload.template_name not in {option.path for option in ATTACK_PROMPT_TEMPLATE_OPTIONS}:
        return JSONResponse({"error": f"Unknown prompt template: {payload.template_name!r}."}, status_code=422)

    raw_attack = RawAttack(
        name=payload.name, modifier=payload.modifier, attack_type=payload.attack_type,
        attack_effect=payload.attack_effect,
    )

    explicit_range = None
    if not is_melee(raw_attack) and payload.range_value is not None:
        explicit_range = EffectRange(effect_range=payload.range_value, range_unit_system=payload.range_unit)

    if (
        payload.attack_type in ("ranged", "ranged touch")
        and not (payload.additional_description or "").strip()
        and explicit_range is None
    ):
        return JSONResponse(
            {"error": "A ranged attack needs either a range value and unit, or a description "
                      "mentioning its range — neither was provided."},
            status_code=422,
        )

    semantic_context = SemanticContextInput(
        additional_description=payload.additional_description,
        creature_description=payload.creature_description,
        creature_subtype=payload.creature_subtype,
    )
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
    # get_or_create_raw_field() is always called first, never conditioned
    # on a separate "does an active result exist?" check -- see its own
    # docstring for why (a raw_field can already exist for this
    # fingerprint with no active event yet).
    fingerprint = compute_fingerprint(raw_attack, semantic_context.creature_subtype, explicit_range)
    raw_field = get_or_create_raw_field(
        session, game_id=get_default_game(session).id, raw_attack=raw_attack,
        semantic_context=semantic_context, fingerprint=fingerprint,
    )

    if raw_field.current_classification_event_id is not None:
        active_event = session.get(ClassificationEvent, raw_field.current_classification_event_id)
        if active_event.decision == ValidationStatus.REJECTED:
            return JSONResponse({"error": "This attack was previously rejected."}, status_code=422)
        try:
            _structured_data, card = find_existing_card(session, active_event)
        except InconsistentActiveClassificationError as exc:
            return JSONResponse({"error": f"Could not load the saved card: {exc}"}, status_code=500)
        return JSONResponse(card.content, status_code=200)

    try:
        semantic_result = classify_attack(
            raw_attack=raw_attack,
            additional_description=semantic_context.additional_description,
            creature_description=semantic_context.creature_description,
            creature_subtype=semantic_context.creature_subtype,
            template_name=payload.template_name,
        )
    except ModelUnavailableError as exc:
        return JSONResponse({"error": f"The configured LLM model is unavailable: {exc}"}, status_code=503)
    except Exception as exc:
        return JSONResponse({"error": f"Classification failed: {exc}"}, status_code=502)

    if explicit_range is not None:
        # The request's own range/unit is trusted over whatever the LLM
        # returned for move_range -- same override rule as /convert.
        semantic_result = dataclasses.replace(semantic_result, move_range=explicit_range)

    requires_review = needs_review(confidence=semantic_result.confidence)

    llm_event = record_llm_run(
        session, raw_field=raw_field, semantic_result=semantic_result, actor=get_llm_actor(session),
        prompt_name=payload.template_name, model_name=get_llm_client().model_name,
        confidence_threshold=validation_settings.CONFIDENCE_THRESHOLD,
        decision=None if requires_review else ValidationStatus.AUTO_APPROVED,
    )

    if requires_review:
        # Deliberately not activated: PENDING until a human decides, on
        # the web -- activating an unresolved event here would make an
        # unreviewed result look like the raw_field's current one.
        return JSONResponse({"status": "pending_review", "event_id": llm_event.id}, status_code=202)

    return _build_and_persist_card(session, raw_field, llm_event, raw_attack, semantic_result, payload.image_uri)
