"""
GET /api/cards and GET /api/cards/{raw_field_id} -- read-only JSON access
to every card the persistence layer has saved (see PERSISTENCE.md), for
a non-interactive consumer rather than a person browsing the web UI.

The JSON equivalent of GET /library/cards/GET /library/cards/{id}
(ui/routes/library.py), filtered to real cards only -- a raw_field with
no active event, or whose active event is REJECTED, has nothing to
return here. Human review (approve/correct/reject/rerun) stays a
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
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from monsterforge.db.pipeline import ClassificationEvent, RawField
from monsterforge.db.session import get_db_session
from monsterforge.pipeline.attack_repository_queries import (
    InconsistentActiveClassificationError,
    find_existing_card,
    list_saved_cards,
)
from monsterforge.validation.enums import ValidationStatus

router = APIRouter(prefix="/api")


class ErrorResponse(BaseModel):
    """The one error shape used by every route in this file -- the
    status code carries the meaning (404 not found, 422 invalid state,
    500 data-integrity anomaly), this just carries a readable message."""
    error: str


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
