"""
Protection calculation rules for D&D 3.x transformation.

This module defines deterministic calculations used to convert
D&D 3.x defensive values into MonsterForge protection stats.

Responsibilities:
- Calculate physical protection values from D&D Armor Class.
- Calculate magical protection values from spell resistance,
  power resistance, and deflection bonuses.

Rules:
- Armor is calculated from total Armor Class excluding size,
  deflection, and other non-dexterity bonuses.
- Talisman is calculated from resistance values and deflection bonuses.
- Only normalized deterministic values are returned.

These functions apply transformation rules but do not define
static mappings or source data structures.
"""

# =====================
# ARMOR
# =====================
def calculate_creature_armor(
        *,
        armor_class: int,
        size_modifier: int,
        dexterity_modifier: int,
        deflection_bonus: int
        ):
    """
    Calculate MonsterForge Armor from D&D 3.x Armor Class.

    Rule:
    - Armor is calculated by removing Dexterity, size, and deflection
      contributions from the total Armor Class.
    - The base AC value (10) is also removed.
    - Size modifiers and deflection bonuses are ignored in the final
      MonsterForge value.

    Examples:
        AC 14, Dexterity +2, no modifiers -> Armor 2
        AC 18, Size -2, Dexterity +2 -> Armor 8
    """
    return (
    armor_class
    - dexterity_modifier
    - size_modifier
    - deflection_bonus
    - 10
    )


# =====================
# TALISMAN
# =====================
def calculate_creature_talisman(
        *,
        spell_resistance: int,
        power_resistance: int,
        deflection_bonus: int
        ):
    """
    Calculate MonsterForge Talisman from D&D 3.x resistance values.

    Rules:
    - The highest resistance value between spell resistance and
      power resistance is used.
    - Values are reduced by 10.
    - Positive remaining values are increased by deflection bonus.
    - If resistance does not exceed 10, only deflection bonus is kept.

    Examples:
        Spell resistance 15, deflection +2 -> Talisman 7
        Spell resistance 0, deflection +1 -> Talisman 1
    """
    resistance = max(spell_resistance, power_resistance) -10
    if resistance > 0:
        return resistance + deflection_bonus

    return deflection_bonus
