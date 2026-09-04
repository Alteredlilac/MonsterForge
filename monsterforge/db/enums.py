"""
Enums for the db/ package's own persistence-layer concepts (event log
discriminators, row lifecycle state), as opposed to game concepts
(domain/enums.py) or the pipeline's review-workflow concepts
(validation/enums.py).

Local enums.py per package, same pattern as every other enum-owning
package in this project.
"""
from enum import Enum


# =====================
# EVENT TYPE
# =====================
class EventType(str, Enum):
    """Discriminates what kind of thing happened to a raw_fields row."""

    LLM_RUN = "llm_run"  # a classify_attack() call — first attempt or rerun
    HUMAN_REVIEW = "human_review"  # a decision (approve/correct/reject) on one specific pending LLM_RUN result — that row's id goes in referenced_event_id
    MANUAL_CORRECTION = "manual_correction"  # a human edits a field on their own initiative (e.g. renames a card, rewrites a description) — not a decision on any specific pending LLM_RUN row


# =====================
# EVENT STATUS
# =====================
class EventStatus(str, Enum):
    """Whether a classification_events row still describes the result
    currently in use — the one column of that table allowed to change
    after the row is written."""

    PENDING = "pending"
    ACTIVE = "active"
    ARCHIVED = "archived"


# =====================
# RAW KIND
# =====================
class RawKind(str, Enum):
    """What kind of raw_fields object a row's data blob holds."""

    ATTACK = "attack"


# NOTE:
# ATTACK is the only real producer today (raw_fields/dnd/v3x/attacks.py).
# Extend this list when a second raw_fields producer (talents, spells,
# special qualities) is actually built — not in advance of one existing.


# =====================
# ENTITY TYPE
# =====================
class EntityType(str, Enum):
    """What kind of typed object a structured_data row's data blob holds."""

    CREATURE = "creature"
    ATTACK = "attack"
    SPELL = "spell"


# NOTE:
# A starting guess at which structured_data/ types get persisted, not a
# verified/exhaustive list — only Attack has a real structured_data
# model and converter today (structured_data/dnd/v3x/attacks.py). Expect
# this to grow as more structured_data types are actually built.

