"""
Persistence operations for the Attack classification pipeline.

Sits alongside attack_pipeline.py, not inside db/: db/ defines the
schema (tables, columns, relationships), this module is the
access/orchestration logic that uses it, the same split already
established between rules/ (static data) and transformation/ (functions
consuming that data). Every function here takes an explicit
SQLAlchemy session rather than opening its own, so both ui/app.py
(today) and, later, attack_pipeline.py itself (MVP 1.3) can call the
same functions without duplicating logic.
"""
import datetime
import hashlib
import json

import sqlalchemy as sa
from sqlalchemy.orm import Session

from monsterforge.db.cards import Card
from monsterforge.db.enums import CardType, EntityType, EventStatus, EventType, RawKind
from monsterforge.db.pipeline import ClassificationEvent, RawField, StructuredData
from monsterforge.db.reference_data import Actor, Game
from monsterforge.db.seed import DND_GAME_NAME, HUMAN_REVIEWER_ACTOR_NAME, LLM_ACTOR_NAME
from monsterforge.llm.semantic_classification.attacks import (
    AttackSemanticResult,
    SemanticContextInput,
    semantic_result_to_dict,
)
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.serialization.plain_data import to_plain
from monsterforge.structured_data.dnd.v3x.attacks import Attack as StructuredAttack
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import HumanReview


class InconsistentActiveClassificationError(ValueError):
    """A raw_field's active classification event has no corresponding
    cards row — a data-integrity anomaly, not something to silently
    paper over by reclassifying. See find_existing_card()."""


def compute_fingerprint(
        raw_attack: RawAttack,
        creature_subtype: CreatureSubtype | None,
        effect_range: EffectRange | None) -> str:
    """
    Compute a deterministic cache key for an attack submission.

    Rules:
    - Includes name/modifier/attack_type/attack_effect (always),
      creature_subtype (the only free-form context field with a rigid
      classification rule attached), and effect_range when known.
    - Deliberately excludes additional_description/creature_description
      (free text): two submissions of mechanically the same attack for
      different creatures almost always have different free-text
      context, so including it would make the cache almost never hit in
      practice, defeating its purpose. creature_subtype is the one
      context field kept, since it can carry a rigid classification rule
      (e.g. "incorporeal" forces a magical move type) rather than just
      influencing the LLM's judgment the way free text does.

    A JSON-encoded list of the components is hashed rather than a
    delimiter-joined string, so a value that happens to contain the
    delimiter can't produce a colliding fingerprint for two genuinely
    different inputs.
    """
    components = [
        raw_attack.name,
        raw_attack.modifier,
        raw_attack.attack_type,
        raw_attack.attack_effect,
        creature_subtype.value if creature_subtype else None,
        effect_range.effect_range if effect_range else None,
        effect_range.range_unit_system.value if effect_range else None,
    ]
    normalized = json.dumps(components)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_default_game(session: Session) -> Game:
    """Return the seeded D&D 3.x game row (see db/seed.py)."""
    return session.query(Game).filter_by(name=DND_GAME_NAME).one()


def get_llm_actor(session: Session) -> Actor:
    """Return the seeded actor row representing the LLM (see db/seed.py)."""
    return session.query(Actor).filter_by(actor_name=LLM_ACTOR_NAME).one()


def get_human_actor(session: Session) -> Actor:
    """Return the seeded actor row representing the human reviewer (see db/seed.py)."""
    return session.query(Actor).filter_by(actor_name=HUMAN_REVIEWER_ACTOR_NAME).one()


def get_or_create_raw_field(
        session: Session, *,
        game_id: str,
        raw_attack: RawAttack,
        semantic_context: SemanticContextInput,
        fingerprint: str) -> RawField:
    """
    Look up an existing raw_fields row by fingerprint, or create one.

    Rules:
    - Same fingerprint always means the same submission (see
      compute_fingerprint()'s own rules for exactly which fields that
      covers) — an existing row is returned unchanged, never
      re-validated field by field.
    - Always called first, never conditioned on another lookup: this is
      the only place that decides whether a raw_field for this
      fingerprint already exists. Calling it only after a separate
      "cache hit" check found nothing would risk an IntegrityError on
      fingerprint's UNIQUE constraint whenever a row already exists but
      has no active classification event yet (e.g. an earlier attempt
      interrupted before any event was activated).
    - page_id stays None: every caller of this repository submits an
      attack by hand through the web form, never from a scraped page.
    - The new row's data blob combines the raw attack's own fields with
      the submission's semantic context in one blob, not two — both
      answer "what was submitted," reused unchanged across every
      classification attempt for this row.
    """
    existing = session.query(RawField).filter_by(fingerprint=fingerprint).first()
    if existing is not None:
        return existing

    raw_field = RawField(
        page_id=None,
        game_id=game_id,
        raw_kind=RawKind.ATTACK,
        name=raw_attack.name,
        fingerprint=fingerprint,
        data={
            "name": raw_attack.name,
            "modifier": raw_attack.modifier,
            "attack_type": raw_attack.attack_type,
            "attack_effect": raw_attack.attack_effect,
            "additional_description": semantic_context.additional_description,
            "creature_description": semantic_context.creature_description,
            "creature_subtype": (
                semantic_context.creature_subtype.value if semantic_context.creature_subtype else None
            ),
        },
        created_at=datetime.datetime.now(),
    )
    session.add(raw_field)
    session.commit()
    return raw_field


def record_llm_run(
        session: Session, *,
        raw_field: RawField,
        semantic_result: AttackSemanticResult,
        actor: Actor,
        prompt_name: str,
        model_name: str,
        confidence_threshold: float,
        decision: ValidationStatus | None,
        rerun_note: str | None = None) -> ClassificationEvent:
    """
    Record one LLM classification attempt as a new append-only event.

    `decision` must already be resolved by the caller before this is
    called — AUTO_APPROVED if no review is needed, None if the result
    is awaiting one. decision is fixed at creation time and never
    changes afterward, unlike `status` (the one deliberate exception to
    classification_events' append-only rule — see db/pipeline.py). The
    event starts PENDING regardless of `decision`: activating it (making
    it the raw_field's current result) is a separate step, see
    activate_classification_event().
    """
    event = ClassificationEvent(
        raw_field_id=raw_field.id,
        event_type=EventType.LLM_RUN,
        prompt_name=prompt_name,
        model_name=model_name,
        confidence=semantic_result.confidence,
        confidence_threshold_at_time=confidence_threshold,
        rerun_note=rerun_note,
        result=semantic_result_to_dict(semantic_result),
        actor_id=actor.id,
        decision=decision,
        status=EventStatus.PENDING,
        created_at=datetime.datetime.now(),
    )
    session.add(event)
    session.commit()
    return event


def record_human_review(
        session: Session, *,
        raw_field: RawField,
        referenced_event: ClassificationEvent,
        review: HumanReview,
        actor: Actor) -> ClassificationEvent:
    """
    Record a human review decision as a new append-only event.

    `referenced_event_id` points at the specific LLM_RUN this decision
    is about (see db/pipeline.py's HUMAN_REVIEW vs. MANUAL_CORRECTION
    distinction) — an explicit semantic pointer, not a chronological
    one. `review.result` is None only for a REJECTED review (per
    HumanReview's own contract); stored here as an empty dict rather
    than None, since ClassificationEvent.result is never nullable —
    every event has some result, even an empty one for a rejection with
    nothing to reuse. Like record_llm_run(), this never activates the
    event on its own; that's activate_classification_event()'s job.
    """
    event = ClassificationEvent(
        raw_field_id=raw_field.id,
        event_type=EventType.HUMAN_REVIEW,
        result=semantic_result_to_dict(review.result) if review.result is not None else {},
        assigned_llm_score=review.assigned_llm_score,
        edit_note=review.edit_note,
        actor_id=actor.id,
        decision=review.status,
        status=EventStatus.PENDING,
        referenced_event_id=referenced_event.id,
        created_at=datetime.datetime.now(),
    )
    session.add(event)
    session.commit()
    return event


def activate_classification_event(
        session: Session, *,
        raw_field: RawField,
        event: ClassificationEvent) -> None:
    """
    Mark `event` as the current/valid result for `raw_field`.

    Archives whatever event was previously active for this raw_field
    (if any), sets `event.status = ACTIVE`, and points
    `raw_field.current_classification_event_id` at it. Called for every
    resolved outcome, including a REJECTED human review — status tracks
    "the most recently resolved state for this raw_field", not only "a
    usable result"; callers must check `event.decision` separately
    before treating an active event as something to build a card from.
    """
    previous_active_id = raw_field.current_classification_event_id
    if previous_active_id is not None:
        previous_active = session.get(ClassificationEvent, previous_active_id)
        if previous_active is not None:
            previous_active.status = EventStatus.ARCHIVED

    event.status = EventStatus.ACTIVE
    raw_field.current_classification_event_id = event.id
    session.commit()


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
    """
    raw_field = session.get(RawField, raw_field_id)
    events = (
        session.query(ClassificationEvent)
        .filter_by(raw_field_id=raw_field_id)
        .order_by(ClassificationEvent.created_at.asc())
        .all()
    )

    summaries = []
    for event in events:
        actor = session.get(Actor, event.actor_id)
        summaries.append({
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
        })
    return summaries


def list_saved_cards(session: Session, *, query: str | None = None) -> list[dict]:
    """
    Build one gallery-shaped entry per raw_field with a resolved,
    card-backed active classification event, most recent first.

    Rules:
    - query, if given, filters to raw_fields whose name contains it
      (case-insensitive) or whose id starts with it — matches either
      the full raw_field id or the short id shown in the library UI
      (see rendering/library_renderer.py's short_id).
    - A raw_field with no active event yet, or whose active event was
      REJECTED (no card exists for a rejection), is skipped.
    - A raw_field whose active event has no saved card behind it
      (InconsistentActiveClassificationError) is skipped rather than
      raised: this is a read-only browsing view, one broken row must
      not break the whole listing.
    - classification_result is the active event's own result dict
      (description/move_type/move_range/confidence/rationale, see
      semantic_result_to_dict()) — always the currently active values,
      which for a CORRECTED review are the corrected ones, not the
      originating LLM_RUN's pre-correction answer. confidence/rationale
      are always present here even on a HUMAN_REVIEW row: a correction
      only ever replaces description/move_type/move_range (see
      ui/app.py's "correct" branch), never confidence/rationale, so
      they're carried through from the original classification either
      way. (REJECTED reviews, whose result is an empty dict, are
      already filtered out above.)
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
        if active_event.decision == ValidationStatus.REJECTED:
            continue

        try:
            _structured_data, card = find_existing_card(session, active_event)
        except InconsistentActiveClassificationError:
            continue

        events = list_classification_events(session, raw_field.id)

        entries.append({
            "raw_field_id": raw_field.id,
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
            "classification_result": active_event.result,
            "assigned_llm_score": active_event.assigned_llm_score,
            "edit_note": active_event.edit_note,
            "revision_count": len(events),
            "events": events,
            "move_card": card.content,
        })
    return entries


def save_structured_data(
        session: Session, *,
        raw_field: RawField,
        classification_event: ClassificationEvent,
        structured_attack: StructuredAttack) -> StructuredData:
    """Persist a StructuredAttack as the structured_data row for `classification_event`."""
    structured_data = StructuredData(
        raw_field_id=raw_field.id,
        classification_event_id=classification_event.id,
        entity_type=EntityType.ATTACK,
        name=structured_attack.name,
        data=to_plain(structured_attack),
    )
    session.add(structured_data)
    session.commit()
    return structured_data


def save_card(
        session: Session, *,
        structured_data: StructuredData,
        card_data: dict,
        card_type: CardType) -> Card:
    """Persist an already-serialized MoveCard dict (see card_to_json()) as a cards row."""
    card = Card(
        structured_data_id=structured_data.id,
        card_type=card_type,
        name=card_data["name"],
        content=card_data,
    )
    session.add(card)
    session.commit()
    return card
