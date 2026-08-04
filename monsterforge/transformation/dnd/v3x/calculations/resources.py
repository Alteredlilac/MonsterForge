"""
Resource calculation rules for D&D 3.x transformation.

This module defines the rules used to convert D&D 3.x progression
values into deterministic MonsterForge action resources.

Responsibilities:
- Calculate Stamina from Base Attack Bonus.
- Calculate Mana from caster and manifester progression.

Rules:
- Stamina is calculated from Base Attack Bonus and represents the
  physical action pool available per turn.
- Mana is calculated from the effective magic level and represents
  the magical action pool available per turn.
- Decimal values are rounded down.
- Stamina has a minimum value of 1.
- Mana has a minimum value of 1 only for creatures with magic
  progression.
- The maximum value of both resources is limited to 4 to preserve
  gameplay speed.

This module applies transformation calculations but does not define
static mappings or source data structures.
"""

from .general_math import floor_value

# =====================
# STAMINA
# =====================
def calculate_stamina(base_attack_bonus: int) -> int:
    """
    Calculate deterministic stamina value from D&D 3.x Base Attack Bonus.

    Rules:
    - Stamina is calculated as one fifth of the Base Attack Bonus.
    - Decimal values are rounded down.
    - Creatures with Base Attack Bonus always have at least 1 stamina.
    - The maximum stamina value is limited to 4 to preserve gameplay speed.

    Examples:
        BAB 25 -> 4 stamina
        BAB 7 -> 1 stamina
        BAB 0 -> 1 stamina
    """
    stamina = floor_value(base_attack_bonus / 5)

    # NOTE:
    # The maximum number of attacks per turn is limited to 4
    # to preserve gameplay speed.
    stamina = min(4,stamina)

    return max(1, stamina)

# =====================
# MANA
# =====================
def calculate_mana(
    *,
    caster_level: int | None,
    manifester_level: int | None,
    ) -> int:
    """
    Calculate deterministic mana value from D&D 3.x magic progression.

    Rules:
    - The effective magic level is the highest value between caster
    level and manifester level.
    - Every 5 effective magic levels generate 1 mana point.
    - Creatures without caster or manifester levels have 0 mana.
    - Creatures with magic progression always have at least 1 mana.
    - The maximum mana value is limited to 4 to preserve gameplay speed.
    """
    magic_level = max(caster_level or 0, manifester_level or 0)

    if magic_level == 0:
        return 0

    mana = floor_value(magic_level / 5)

    # NOTE:
    # The maximum number of spells per turn is limited to 4
    # to preserve gameplay speed.
    mana = min(4,mana)

    return max(1, mana)    
