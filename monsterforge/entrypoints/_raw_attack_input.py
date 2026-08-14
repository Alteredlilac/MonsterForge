"""
Shared interactive input helper for entry points that need a raw
Attack (raw_fields) built from user-provided values.

Manual input is a first-class path in this project (see README.md), not
a workaround: this lets a user hand-enter a custom attack and run it
through the full pipeline without scraping.
"""
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack


def prompt_for_raw_attack() -> RawAttack:
    """Interactively collect the four raw_fields.Attack fields."""
    print("Enter the raw attack fields (leave blank where not applicable):")
    name = input("Name: ").strip()
    modifier = input("Modifier (e.g. +5): ").strip()
    attack_type = input("Attack type (e.g. melee, ranged, ranged touch): ").strip()
    attack_effect = input("Attack effect (e.g. 1d6+3 plus trip): ").strip()

    return RawAttack(
        name=name,
        modifier=modifier,
        attack_type=attack_type,
        attack_effect=attack_effect,
    )
