"""
Orchestrate the D&D 3.x Attack -> MoveCard conversion pipeline.

This module composes the three independently-testable stages already
implemented elsewhere (LLM classification, raw->structured conversion,
structured->domain conversion) into the single entry point consumed by
the CLI entry points and, later, the API layer.

This is the MVP zero version: a pure, linear composition with no
persistence, deduplication, or human-validation branching. It is the
intentional seam where those features will be added later — see
.claude/project-context/MVP_zero.md §12 and
.claude/future_plans/EXPANDED_MVP_PLAN.md — without changing the three
stages it composes.
"""
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.llm.semantic_classification.attacks import classify_attack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import (
    raw_to_structured_attack,
)
from monsterforge.transformation.dnd.v3x.converters.attacks_converter import attack_converter
from monsterforge.domain.moves import MoveCard


def convert_attack(raw_attack: RawAttack) -> MoveCard:
    """
    Convert a raw D&D 3.x attack into a domain MoveCard.

    Rules:
    - Classify the attack semantically via the LLM (description, move
      type, range).
    - Combine that result with the deterministic parsing of the raw
      fields into a structured Attack.
    - Convert the structured Attack into a MoveCard.

    No caching, deduplication, persistence, or human-validation gate is
    performed here — every call re-invokes the LLM classifier and
    produces a MoveCard with a fresh random id.
    """
    semantic_result = classify_attack(raw_attack=raw_attack)
    structured_attack = raw_to_structured_attack(raw_attack, semantic_result)

    return attack_converter(structured_attack)
