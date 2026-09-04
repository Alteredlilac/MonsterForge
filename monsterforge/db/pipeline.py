"""
The core conversion pipeline tables for the db/ package: raw_fields,
classification_events, structured_data.

Distinct from db/reference_data.py's lookup tables and db/scraping.py's
scraped input: this is the append-only event log at the heart of the
schema, where every LLM run, rerun, and human review of a raw field
accumulates as its own row rather than overwriting a "current result"
column. See classification_events' own docstring below for the specific
append-only rule and its one deliberate exception.
"""

import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from monsterforge.db.base import Base, uuid4_str
from monsterforge.db.enums import EntityType, EventStatus, EventType, RawKind
from monsterforge.validation.enums import ValidationStatus


# =====================
# RAW FIELD
# =====================
class RawField(Base):
    """A single raw-field submission (today only Attack), as one JSON blob."""

    __tablename__ = "raw_fields"

    id: Mapped[str] = mapped_column(sa.Text, primary_key=True, default=uuid4_str)
    # Nullable: an attack entered by hand via the web form has no source page.
    page_id: Mapped[str | None] = mapped_column(sa.Text, sa.ForeignKey("pages.id"), nullable=True)
    # NOTE:
    # Not inherited from page_id via pages.game_id, precisely because
    # page_id is nullable for manual submissions: without a game_id of
    # its own here, that case would have no way to declare which game
    # system it belongs to.
    game_id: Mapped[str] = mapped_column(sa.Text, sa.ForeignKey("games.id"))
    raw_kind: Mapped[RawKind] = mapped_column(
        sa.Enum(RawKind, values_callable=lambda x: [e.value for e in x], native_enum=False)
    )
    # Promoted from the data blob below so rows can be searched/listed by
    # name without parsing JSON (e.g. RawAttack.name).
    name: Mapped[str] = mapped_column(sa.Text)
    # NOTE:
    # Holds both the raw object's own fields (name/modifier/attack_type/
    # attack_effect for an Attack) and the submission's stable semantic
    # context (additional_description/creature_description/
    # creature_subtype — the same three fields as SemanticContextInput)
    # in the same blob, not a second one — both answer "what was
    # submitted," reused unchanged across every classification attempt
    # for this row. A rerun's extra note is the one part that varies per
    # attempt, so it lives on classification_events.rerun_note instead.
    data: Mapped[dict] = mapped_column(sa.JSON)
    # Points at the event considered current/valid, so downstream stages
    # don't need to re-read the whole history to find the active result.
    current_classification_event_id: Mapped[str | None] = mapped_column(
        sa.Text, sa.ForeignKey("classification_events.id"), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime)


# =====================
# CLASSIFICATION EVENT
# =====================
class ClassificationEvent(Base):
    """A chronological, append-only log of everything that happens to a
    raw field: LLM runs, reruns, human reviews, manual corrections.

    Every row shares this one schema regardless of event_type — not
    separate tables per event kind. Only `status` may change on a row
    after it's written; every other column is a permanent historical
    record of what happened, including on rows later superseded by a
    more recent event.
    """

    __tablename__ = "classification_events"

    id: Mapped[str] = mapped_column(sa.Text, primary_key=True, default=uuid4_str)
    raw_field_id: Mapped[str] = mapped_column(sa.Text, sa.ForeignKey("raw_fields.id"))
    # NOTE:
    # HUMAN_REVIEW vs. MANUAL_CORRECTION — both are human-driven, and
    # both can involve editing a field (e.g. a name, a description); the
    # distinction isn't "review vs. no review" in the everyday sense of
    # those words (a correction is itself a judgment call, so calling one
    # of the two "not a review" would be misleading) — it's specifically
    # whether the row is a decision on one particular pending LLM_RUN:
    # - HUMAN_REVIEW: a decision (approve/correct/reject) on one specific
    #   LLM_RUN result shown to the human for that purpose.
    #   referenced_event_id is set to that LLM_RUN row's id.
    # - MANUAL_CORRECTION: an edit made on the human's own initiative,
    #   not as a decision on any specific pending LLM_RUN row.
    #   referenced_event_id, if set at all here, points at whichever
    #   event's result is being edited — not at an LLM_RUN awaiting a
    #   decision.
    event_type: Mapped[EventType] = mapped_column(
        sa.Enum(EventType, values_callable=lambda x: [e.value for e in x], native_enum=False)
    )
    # The next 5 columns are populated only for event_type == LLM_RUN,
    # NULL on every other row (human_review/manual_correction rows have
    # no prompt/model/confidence of their own).
    prompt_name: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    # NOTE:
    # The CONFIDENCE_THRESHOLD value actually in effect at the moment of
    # this LLM run, not read from the live config at query time. Without
    # this, re-reading history after the threshold changes couldn't say
    # for certain why a given confidence was or wasn't sent to review —
    # the row must tell its own story, independent of a config value that
    # may have since changed.
    confidence_threshold_at_time: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    # The extra note appended to additional_description for THIS specific
    # rerun attempt only — NULL on a first classification attempt and on
    # every non-LLM_RUN row. The stable base context lives on
    # raw_fields.data (see above); this column captures only this
    # attempt's delta, not the whole reconstructed context.
    rerun_note: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    result: Mapped[dict] = mapped_column(sa.JSON)
    # Populated only for event_type in (HUMAN_REVIEW, MANUAL_CORRECTION).
    assigned_llm_score: Mapped[float | None] = mapped_column(sa.Float, nullable=True)
    edit_note: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    # Never NULL — every event has an actor, including the LLM itself.
    actor_id: Mapped[str] = mapped_column(sa.Text, sa.ForeignKey("actors.id"))
    # NOTE:
    # Reuses validation/enums.py's ValidationStatus rather than a new
    # vocabulary. On LLM_RUN rows: AUTO_APPROVED if the result was used
    # directly without review, NULL if awaiting review. On HUMAN_REVIEW/
    # MANUAL_CORRECTION rows: always APPROVED/CORRECTED/REJECTED, never
    # NULL or AUTO_APPROVED (that value only ever appears on LLM_RUN rows).
    decision: Mapped[ValidationStatus | None] = mapped_column(
        sa.Enum(ValidationStatus, values_callable=lambda x: [e.value for e in x], native_enum=False),
        nullable=True,
    )
    # The one column allowed to change after this row is written — see
    # the class docstring and db/enums.py's EventStatus.
    status: Mapped[EventStatus] = mapped_column(
        sa.Enum(EventStatus, values_callable=lambda x: [e.value for e in x], native_enum=False)
    )
    # An explicit semantic pointer to the event a decision is being made
    # about, chosen by the user/system — not a chronological ordering.
    # This can "skip back" past the most recent event; never confuse it
    # with a previous/next-event linked list, deliberately not built: a
    # linked list would need manual upkeep on every insert, with real
    # risk of breaking the chain on a single mistake — an unjustified
    # cost when created_at already gives chronological ordering for free.
    referenced_event_id: Mapped[str | None] = mapped_column(
        sa.Text, sa.ForeignKey("classification_events.id"), nullable=True
    )
    # NOT NULL: with random UUID4 primary keys, created_at is the only
    # way to reconstruct chronological order.
    created_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime)


# =====================
# STRUCTURED DATA
# =====================
class StructuredData(Base):
    """Final typed data for a raw field, after casting/interpretation."""

    __tablename__ = "structured_data"

    id: Mapped[str] = mapped_column(sa.Text, primary_key=True, default=uuid4_str)
    # Not nullable, and no alternative page_id: every structured_data row
    # always derives from a raw_field, never directly from a page —
    # raw_fields is the mandatory intermediate stage for every data kind,
    # not just Attack. Kept alongside classification_event_id below for
    # convenient direct queries, even though it's also reachable by
    # joining through that event.
    raw_field_id: Mapped[str] = mapped_column(sa.Text, sa.ForeignKey("raw_fields.id"))
    # NOTE:
    # The real derivation link: which classification produced this row.
    # A raw_field can have more than one structured_data row over time —
    # each reclassification/correction produces a new one instead of
    # updating an existing row (same append-only philosophy as
    # classification_events, extended one stage further down the
    # pipeline) — so raw_field_id alone can no longer identify "the"
    # structured_data for a given attempt.
    classification_event_id: Mapped[str] = mapped_column(sa.Text, sa.ForeignKey("classification_events.id"))
    entity_type: Mapped[EntityType] = mapped_column(
        sa.Enum(EntityType, values_callable=lambda x: [e.value for e in x], native_enum=False)
    )
    # Promoted from the data blob below (e.g. structured_data.dnd.v3x.
    # attacks.Attack.name).
    name: Mapped[str] = mapped_column(sa.Text)
    data: Mapped[dict] = mapped_column(sa.JSON)
