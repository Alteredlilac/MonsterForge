"""
Turning a resolved pipeline/review state into the HTTP response the
browser actually sees.

Named responses.py rather than rendering.py to avoid the same kind of
collision jinja_templating.py was named to avoid: this project already
has a top-level monsterforge/rendering/ package
(move_card_renderer.py, library_renderer.py), imported directly into
this same app -- a second "rendering" module living at
monsterforge/ui/rendering.py would be genuinely ambiguous to a reader
seeing both imported side by side.

Every route ends up calling into one of these four functions -- a
plain dead-end message, a freshly built card, an already-saved card
served from cache, or the review form itself -- rather than building
an HTMLResponse inline.
"""
import json

from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from monsterforge.db.enums import CardType
from monsterforge.db.pipeline import ClassificationEvent, RawField
from monsterforge.llm.semantic_classification.attacks import (
    ATTACK_PROMPT_TEMPLATE_OPTIONS,
    AttackSemanticResult,
    SemanticContextInput,
)
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import (
    UnknownAttackRange,
    is_melee,
    raw_to_structured_attack,
)
from monsterforge.pipeline.attack_repository import activate_classification_event, save_card, save_structured_data
from monsterforge.pipeline.attack_repository_queries import find_existing_card
from monsterforge.rendering.move_card_renderer import render_move_card_html_with_edit
from monsterforge.serialization.domain_to_json import card_to_json
from monsterforge.structured_data.dnd.v3x.enums import MoveType, UnitSystem
from monsterforge.transformation.dnd.v3x.converters.attacks_converter import attack_converter
from monsterforge.ui.hidden_fields import semantic_result_to_json


def review_form_context(
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
        "semantic_result_json": semantic_result_to_json(semantic_result),
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


def message_page(message: str, status_code: int = 200) -> HTMLResponse:
    """A plain response for an outcome that produces no card (blank
    input, a classification failure, a rejected review) — always with a
    way back to /convert, rather than a bare dead-end message."""
    return HTMLResponse(f'<p>{message}</p><p><a href="/convert">Home</a></p>', status_code=status_code)


def render_card(
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
        return message_page(f"Could not build the card: {exc}", status_code=422)

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
        "semantic_result_json": semantic_result_to_json(semantic_result),
    }

    return HTMLResponse(render_move_card_html_with_edit(card_data, "/review/edit", edit_form_fields))


def serve_cached_card(
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
        # NOTE:
        # card.name, not raw_field.data["name"] -- the latter is the
        # original, immutable submission (see RawField's own docstring)
        # and would silently discard a later name correction (MVP 2.19).
        # card.name is exactly the name this specific card was built
        # with, so it's already correct by construction.
        "raw_attack_name": card.name,
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
