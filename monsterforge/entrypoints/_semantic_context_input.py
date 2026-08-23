"""
Shared interactive helpers for collecting the optional semantic-
classification context (additional_description, creature_description,
creature_subtype) that llm.semantic_classification.classify_attack()
accepts alongside a raw attack.

Used by every entry point that wants classify_attack() exercised with
realistic context instead of always defaulting it to None — currently
convert_attack_cli.py and test_llm_prompt_cli.py.
"""
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype
from monsterforge.llm.semantic_classification.attacks import SemanticContextInput  # re-exported: existing importers use this module's path


def prompt_for_creature_subtype() -> CreatureSubtype | None:
    """Ask for an optional creature subtype, re-prompting on invalid input.

    CreatureSubtype is a (str, Enum), so the raw text maps directly onto
    a member's value (e.g. "incorporeal" -> CreatureSubtype.INCORPOREAL).
    """
    while True:
        text = input("Creature subtype (optional, e.g. incorporeal): ").strip().lower()

        if not text:
            return None

        try:
            return CreatureSubtype(text)
        except ValueError:
            valid_values = ", ".join(member.value for member in CreatureSubtype)
            print(f"Unknown creature subtype {text!r}. Valid values: {valid_values}")


def prompt_for_multiple_creature_subtypes() -> list[CreatureSubtype]:
    """
    Ask for multiple optional creature subtypes until an empty input.

    Each subtype is validated individually by prompt_for_creature_subtype().
    """
    subtypes = []

    while True:
        print("Enter creature subtypes one at a time (press Enter to finish).")
        subtype = prompt_for_creature_subtype()

        if subtype is None:
            return subtypes

        subtypes.append(subtype)


def resolve_relevant_creature_subtype(
        subtypes: list[CreatureSubtype]) -> CreatureSubtype | None:
    """
    Reduce a list of entered subtypes to the single value
    classify_attack.jinja2 actually branches on.

    NOTE:
    The template's classification rule currently only checks for
    "incorporeal" ("always classify as magical"). Only that subtype is
    surfaced here, even if the user enters several — matching what
    AttackSemanticContext.creature_subtype (a single optional value, not
    a list) can express in the real classify_attack() pipeline today.
    A creature having multiple subtypes at once is common in D&D, but
    modeling that properly belongs to AttackSemanticContext itself, not
    to this input helper. If the template's rules grow to depend on
    other subtypes, extend this function accordingly.
    """
    if CreatureSubtype.INCORPOREAL in subtypes:
        return CreatureSubtype.INCORPOREAL

    return None


def prompt_for_semantic_context() -> SemanticContextInput:
    """Collect additional_description, creature_description, and the
    resolved creature_subtype interactively."""
    additional_description = input("Additional description (optional): ").strip() or None
    creature_description = input("Creature description (optional): ").strip() or None
    entered_subtypes = prompt_for_multiple_creature_subtypes()
    creature_subtype = resolve_relevant_creature_subtype(entered_subtypes)

    return SemanticContextInput(
        additional_description=additional_description,
        creature_description=creature_description,
        creature_subtype=creature_subtype,
    )
