"""
Read-only queries over the data pipeline.attack_repository.py's
write-path functions save: serving an already-cached card, browsing the
saved-cards library, and resolving which name/description/move_type
was in effect at a given point in an attack's history. No function here
ever calls session.add()/session.commit() -- that's the sibling
module's job.

Split out of attack_repository.py once the read side (added for the
cards library) grew large enough to be its own concern, answering a
different domain question ("given what's already saved, what do we
show or look up?") than the write-path functions that record new
events.
"""
import sqlalchemy as sa
from sqlalchemy.orm import Session

from monsterforge.db.cards import Card
from monsterforge.db.pipeline import ClassificationEvent, RawField, StructuredData
from monsterforge.db.reference_data import Actor
from monsterforge.validation.enums import ValidationStatus


class InconsistentActiveClassificationError(ValueError):
    """A raw_field's active classification event has no corresponding
    cards row — a data-integrity anomaly, not something to silently
    paper over by reclassifying. See find_existing_card()."""


def find_existing_card(session: Session, event: ClassificationEvent) -> tuple[StructuredData, Card]:
    """
    Look up the structured_data/cards pair already saved for `event`.

    Raises:
        InconsistentActiveClassificationError:
            If `event` is a raw_field's active event but no
            structured_data row exists for it, or that structured_data
            has no cards row — a data-integrity anomaly (e.g. the
            pipeline failed between activating the event and saving its
            output), reported loudly rather than silently reclassifying
            as if the event had never been resolved.
    """
    structured_data = session.query(StructuredData).filter_by(classification_event_id=event.id).first()
    if structured_data is None:
        raise InconsistentActiveClassificationError(
            f"classification_event {event.id} is active but has no structured_data row."
        )

    card = session.query(Card).filter_by(structured_data_id=structured_data.id).first()
    if card is None:
        raise InconsistentActiveClassificationError(
            f"structured_data {structured_data.id} has no corresponding cards row."
        )

    return structured_data, card


def list_classification_events(session: Session, raw_field_id: str) -> list[dict]:
    """
    Build one summary dict per classification_events row for a raw_field,
    oldest first — the full history a card's current state was built
    from, not just its currently active result.

    Rules:
    - actor_name/actor_authority are resolved here (not left as a bare
      actor_id), the same presentation-shaped-summary spirit as
      list_saved_cards()'s own entries. authority is the conflict-
      resolution rank from db/reference_data.py (LLM=0, human
      reviewer=10) — worth showing next to who did what.
    - result is this event's own recorded classification (description/
      move_type/move_range/confidence/rationale, see
      semantic_result_to_dict()) — an empty dict for a REJECTED review,
      which records no classification (see record_human_review()). This
      is what actually changed at each step: an LLM_RUN's own answer, or
      a human review's approved-as-is or corrected values, so a
      CORRECTED row's result can be compared against the LLM_RUN it
      references to see exactly what a reviewer changed.
    - is_active flags the row currently pointed at by the raw_field's
      current_classification_event_id, independent of chronological
      position — a rerun can sit PENDING, never activated, so "active"
      is not simply "the newest row".
    - effective_name is the name actually in effect right after this
      event, resolved by walking the raw_field's corrected_name history
      forward from raw_fields.data["name"] (the original submission) —
      unlike description/move_type/move_range, corrected_name is only
      ever set on the specific event that changed it (NULL everywhere
      else), so this carries the most recent non-NULL value forward
      instead of reading a single row in isolation. See also
      resolve_effective_name(), which looks up one specific event's
      effective_name from this same list.
    """
    raw_field = session.get(RawField, raw_field_id)
    events = (
        session.query(ClassificationEvent)
        .filter_by(raw_field_id=raw_field_id)
        .order_by(ClassificationEvent.created_at.asc())
        .all()
    )

    summaries = []
    effective_name = raw_field.data["name"]
    for event in events:
        actor = session.get(Actor, event.actor_id)
        if event.corrected_name is not None:
            effective_name = event.corrected_name
        summaries.append({
            "id": event.id,
            "event_type": event.event_type.value,
            "status": event.status.value,
            "decision": event.decision.value if event.decision else None,
            "actor_name": actor.actor_name,
            "actor_authority": actor.authority,
            "created_at": event.created_at.isoformat(),
            "is_active": event.id == raw_field.current_classification_event_id,
            "result": event.result,
            "prompt_name": event.prompt_name,
            "model_name": event.model_name,
            "rerun_note": event.rerun_note,
            "assigned_llm_score": event.assigned_llm_score,
            "edit_note": event.edit_note,
            "corrected_name": event.corrected_name,
            "effective_name": effective_name,
        })
    return summaries


def resolve_effective_name(session: Session, raw_field: RawField, event_id: str) -> str:
    """
    Resolve the name in effect right after one specific classification_
    events row — not necessarily the raw_field's current one, since
    event_id may be an old, already-superseded event reopened for
    review (MVP 2.18) that predates a later correction.

    Falls back to raw_fields.data["name"] (the original submission) if
    event_id isn't found in the raw_field's own history at all, which
    should not happen in practice for a valid event_id.
    """
    for event in list_classification_events(session, raw_field.id):
        if event["id"] == event_id:
            return event["effective_name"]
    return raw_field.data["name"]


def list_saved_cards(session: Session, *, query: str | None = None) -> list[dict]:
    """
    Build one gallery-shaped entry per raw_field with a resolved,
    card-backed active classification event, most recent first.

    Rules:
    - query, if given, filters to raw_fields whose name contains it
      (case-insensitive) or whose id starts with it — matches either
      the full raw_field id or the short id shown in the library UI
      (see rendering/library_renderer.py's short_id).
    - A raw_field with no active event yet is skipped — there is
      nothing at all to show for it yet.
    - A raw_field whose active event is REJECTED still gets an entry
      (unlike earlier versions of this function, which skipped it
      entirely): a rejection reachable via /library/events/{id}/review
      (MVP 2.18) must stay reachable itself, history included, rather
      than vanishing from the library along with any good earlier
      result a reviewer might want to reactivate. find_existing_card()
      is never even called in this case — a REJECTED event never has a
      card (see record_human_review()/_render_card()) — so
      classification_result/move_card are both None; the entry's
      display name falls back to resolve_effective_name() (the raw_field's
      original name, or a later correction if one happened before the
      rejection) instead of a card's own name (see
      rendering/library_renderer.py for how it renders an entry with no
      card).
    - A raw_field whose active event is NOT rejected but still has no
      saved card behind it (InconsistentActiveClassificationError) is
      skipped rather than given an entry: that combination is a genuine
      data-integrity anomaly, not the expected REJECTED case above, and
      this is a read-only browsing view where one broken row must not
      break the whole listing.
    - classification_result is the active event's own result dict
      (description/move_type/move_range/confidence/rationale, see
      semantic_result_to_dict()) — always the currently active values,
      which for a CORRECTED review are the corrected ones, not the
      originating LLM_RUN's pre-correction answer. confidence/rationale
      are always present here even on a HUMAN_REVIEW row: a correction
      only ever replaces description/move_type/move_range (see
      ui/app.py's "correct" branch), never confidence/rationale, so
      they're carried through from the original classification either
      way.
    - assigned_llm_score/edit_note come straight from the active event
      (populated only for HUMAN_REVIEW/MANUAL_CORRECTION) — None when
      the active event is an auto-approved LLM_RUN with no human
      review at all.
    - revision_count/events come from list_classification_events(): the
      total number of classification_events rows for the raw_field
      (every LLM run, rerun, and human decision counts) and their full
      chronological detail, for the library's per-card history tab.
    """
    fields_query = session.query(RawField).filter(RawField.current_classification_event_id.isnot(None))
    if query:
        fields_query = fields_query.filter(
            sa.or_(RawField.name.ilike(f"%{query}%"), RawField.id.ilike(f"{query}%"))
        )
    raw_fields = fields_query.order_by(RawField.created_at.desc()).all()

    entries = []
    for raw_field in raw_fields:
        active_event = session.get(ClassificationEvent, raw_field.current_classification_event_id)

        card = None
        classification_result = None
        if active_event.decision != ValidationStatus.REJECTED:
            try:
                _structured_data, card = find_existing_card(session, active_event)
            except InconsistentActiveClassificationError:
                continue
            classification_result = active_event.result

        events = list_classification_events(session, raw_field.id)

        entries.append({
            "raw_field_id": raw_field.id,
            "name": resolve_effective_name(session, raw_field, active_event.id),
            "case": {
                "name": raw_field.data["name"],
                "modifier": raw_field.data["modifier"],
                "attack_type": raw_field.data["attack_type"],
                "attack_effect": raw_field.data["attack_effect"],
            },
            "context": {
                "additional_description": raw_field.data.get("additional_description"),
                "creature_description": raw_field.data.get("creature_description"),
                "creature_subtype": raw_field.data.get("creature_subtype"),
            },
            "raw_response": None,
            "classification_result": classification_result,
            "assigned_llm_score": active_event.assigned_llm_score,
            "edit_note": active_event.edit_note,
            "revision_count": len(events),
            "events": events,
            "move_card": card.content if card else None,
        })
    return entries
