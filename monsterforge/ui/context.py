"""
Turning raw form input into domain values, before classification.

These three functions all answer the same question -- given a string
(or a few strings) straight off a Form(...) field, what's the
equivalent domain value? -- for the two pieces of pre-classification
context every route needs to resolve: the optional creature/context
fields, and an explicit range value/unit.
"""
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype, UnitSystem
from monsterforge.llm.semantic_classification.attacks import SemanticContextInput


def parse_positive_range(range_value: str, range_unit: str) -> EffectRange | None:
    """
    Build an EffectRange from raw form input, deterministically — a
    numeric value plus a unit dropdown is already fixed, structured
    data, so it's built directly rather than round-tripped through the
    LLM's own free-text interpretation of it.

    Returns None if no range value was given (range is optional unless
    the caller has already required it). Raises ValueError if a range
    value is given but isn't a positive integer, or if the unit is
    missing/invalid — a negative or zero range has no real meaning.
    """
    if not range_value.strip():
        return None

    value = int(range_value)
    if value < 1:
        raise ValueError(f"range value must be positive, got {value}.")

    return EffectRange(effect_range=value, range_unit_system=UnitSystem(range_unit))


def range_context_note(effect_range: EffectRange) -> str:
    """Render an EffectRange as a short sentence to prepend to the LLM's
    additional_description context, so its own confidence reflects that
    the range is already known rather than guessed."""
    unit = "feet" if effect_range.range_unit_system == UnitSystem.IMPERIAL else "meters"
    return f"Range: {effect_range.effect_range} {unit}."


def semantic_context_from_form(
        additional_description: str,
        creature_description: str,
        creature_subtype: str) -> SemanticContextInput:
    return SemanticContextInput(
        additional_description=additional_description or None,
        creature_description=creature_description or None,
        creature_subtype=CreatureSubtype(creature_subtype) if creature_subtype else None,
    )
