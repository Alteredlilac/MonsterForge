"""
Orchestrate the D&D 3.x Attack -> MoveCard conversion pipeline.

This module composes the three independently-testable stages already
implemented elsewhere (LLM classification, raw->structured conversion,
structured->domain conversion) into the single entry point consumed by
the CLI entry points and, later, the API layer.

This is the MVP zero version: a pure, linear composition with no
persistence, deduplication, or human-validation branching. It is the
intentional seam where those features get added later, by wrapping this
same function, without changing the three stages it composes.
"""
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.llm.semantic_classification.attacks import classify_attack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import (
    raw_to_structured_attack,
)
from monsterforge.transformation.dnd.v3x.converters.attacks_converter import attack_converter
from monsterforge.domain.moves import MoveCard
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype


def convert_attack(
        raw_attack: RawAttack,
        *,
        additional_description: str | None = None,
        creature_description: str | None = None,
        creature_subtype: CreatureSubtype | None = None) -> MoveCard:
    """
    Convert a raw D&D 3.x attack into a domain MoveCard.

    Rules:
    - Classify the attack semantically via the LLM (description, move
      type, range), using whatever optional context is supplied to
      sharpen the classification — none of it is required.
    - Combine that result with the deterministic parsing of the raw
      fields into a structured Attack.
    - Convert the structured Attack into a MoveCard.

    No caching, deduplication, persistence, or human-validation gate is
    performed here — every call re-invokes the LLM classifier and
    produces a MoveCard with a fresh random id.
    """
    semantic_result = classify_attack(
        raw_attack=raw_attack,
        additional_description=additional_description,
        creature_description=creature_description,
        creature_subtype=creature_subtype,
    )
    structured_attack = raw_to_structured_attack(raw_attack, semantic_result)

    return attack_converter(structured_attack)
