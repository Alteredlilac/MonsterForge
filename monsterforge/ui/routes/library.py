"""
The cards library: GET /library/cards (read-only browsing, searchable
by name/id), GET /library/cards/{raw_field_id} (reopen a saved card for
printing or further review), and GET /library/events/{classification_
event_id}/review (reopen any past classification event, not just the
raw_field's currently active one, for a fresh review decision).
"""
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from monsterforge.db.enums import EventType
from monsterforge.db.pipeline import ClassificationEvent, RawField
from monsterforge.db.session import get_db_session
from monsterforge.llm.semantic_classification.attacks import ATTACK_PROMPT_TEMPLATE
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.pipeline.attack_repository_queries import (
    InconsistentActiveClassificationError,
    find_existing_card,
    list_saved_cards,
    resolve_effective_name,
)
from monsterforge.rendering.library_renderer import render_library_html
from monsterforge.ui.context import semantic_context_from_form
from monsterforge.ui.hidden_fields import semantic_result_from_json
from monsterforge.ui.jinja_templating import templates
from monsterforge.ui.responses import message_page, review_form_context, serve_cached_card
from monsterforge.validation.enums import ValidationStatus

router = APIRouter()


@router.get("/library/cards", response_class=HTMLResponse)
def cards_library(q: str = "", session: Session = Depends(get_db_session)) -> HTMLResponse:
    """Read-only browsing of every card currently saved in the database,
    optionally filtered by `q` against the attack's name or id — see
    pipeline.attack_repository_queries.list_saved_cards() and
    rendering.library_renderer.render_library_html(). Deliberately
    separate from the public, curated gallery (rendering/gallery_renderer.py),
    which reads from a fixed JSON dataset, not the live database."""
    query = q.strip()
    entries = list_saved_cards(session, query=query or None)
    return HTMLResponse(render_library_html(entries, query=query))


@router.get("/library/cards/{raw_field_id}", response_class=HTMLResponse)
def view_saved_card(raw_field_id: str, session: Session = Depends(get_db_session)) -> HTMLResponse:
    """Reopen an already-saved card for printing or further review,
    found by raw_field_id (e.g. a link from the cards library) rather
    than through a fresh fingerprint hit. Delegates to
    serve_cached_card() for the actual rendering — the same page
    /convert's own cache-hit path already builds, with Print and "Edit
    this classification" (-> /review/edit) both already on it."""
    raw_field = session.get(RawField, raw_field_id)
    if raw_field is None or raw_field.current_classification_event_id is None:
        return message_page("No saved card found for that id.", status_code=404)

    active_event = session.get(ClassificationEvent, raw_field.current_classification_event_id)
    if active_event.decision == ValidationStatus.REJECTED:
        return message_page("This attack was previously rejected — no card to show.", status_code=422)

    try:
        _structured_data, card = find_existing_card(session, active_event)
    except InconsistentActiveClassificationError as exc:
        return message_page(f"Could not load the saved card: {exc}", status_code=500)

    # NOTE:
    # template_name isn't a column on a HUMAN_REVIEW row (see
    # db/pipeline.py) -- walk back to the LLM_RUN it references for the
    # prompt actually used, same pattern already used by
    # list_saved_cards()/list_classification_events() for confidence/
    # rationale. Always by id (referenced_event_id, a real FK), never
    # by name -- a name like "Bite" can have homonyms across raw_fields.
    origin_event = active_event
    if active_event.event_type == EventType.HUMAN_REVIEW and active_event.referenced_event_id:
        origin_event = session.get(ClassificationEvent, active_event.referenced_event_id)
    template_name = origin_event.prompt_name or ATTACK_PROMPT_TEMPLATE

    # Not stored anywhere on raw_field -- it's the saved card's own
    # column (promoted from its content, see db/cards.py).
    image_uri = card.image_uri or ""

    return serve_cached_card(session, raw_field, active_event, template_name, image_uri)


@router.get("/library/events/{classification_event_id}/review", response_class=HTMLResponse)
def reopen_event_for_review(
        request: Request, classification_event_id: str,
        session: Session = Depends(get_db_session)) -> HTMLResponse:
    """Reopen any past classification_events row for a fresh review
    decision, not just the raw_field's currently active one — approving
    or correcting it here makes it the new active result. Works
    uniformly whether or not this event ever had a card built for it (a
    superseded, never-decided LLM_RUN never does) since it reopens the
    review form directly, the same way /review/edit already does,
    rather than a rendered card. Not linked to at all from
    library.html.jinja2 for a REJECTED event, whose own result is an
    empty dict — nothing to review; rejected here too, directly, in
    case this URL is reached some other way."""
    event = session.get(ClassificationEvent, classification_event_id)
    if event is None:
        return message_page("No such classification event.", status_code=404)
    if event.decision == ValidationStatus.REJECTED:
        return message_page("This event was rejected — nothing to review.", status_code=422)

    raw_field = session.get(RawField, event.raw_field_id)
    # resolve_effective_name(), not raw_field.data["name"] -- the name
    # in effect as of THIS specific event may already reflect an
    # earlier correction (MVP 2.19), which the original, immutable
    # submission on raw_field never carries.
    raw_attack = RawAttack(
        name=resolve_effective_name(session, raw_field, event.id), modifier=raw_field.data["modifier"],
        attack_type=raw_field.data["attack_type"], attack_effect=raw_field.data["attack_effect"],
    )
    semantic_context = semantic_context_from_form(
        raw_field.data.get("additional_description") or "",
        raw_field.data.get("creature_description") or "",
        raw_field.data.get("creature_subtype") or "",
    )
    semantic_result = semantic_result_from_json(json.dumps(event.result))

    # Same by-id walk-back as view_saved_card() above, for the same reason.
    origin_event = event
    if event.event_type == EventType.HUMAN_REVIEW and event.referenced_event_id:
        origin_event = session.get(ClassificationEvent, event.referenced_event_id)
    template_name = origin_event.prompt_name or ATTACK_PROMPT_TEMPLATE

    try:
        _structured_data, card = find_existing_card(session, event)
        image_uri = card.image_uri or ""
    except InconsistentActiveClassificationError:
        # NOTE:
        # Unlike view_saved_card()'s lookup on the raw_field's ACTIVE
        # event (where a missing card is a real data-integrity anomaly),
        # a missing card here is normal, not an anomaly: a superseded
        # LLM_RUN that a rerun overtook before ever being decided, or a
        # rejected review, never had one built in the first place.
        image_uri = ""

    return templates.TemplateResponse(
        request, "review_form.html.jinja2",
        review_form_context(
            raw_attack, semantic_context, semantic_result, template_name, image_uri,
            raw_field_id=raw_field.id, classification_event_id=event.id,
        ),
    )
