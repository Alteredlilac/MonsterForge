"""
Vitality calculation rules used during D&D 3.x transformation.

This module defines deterministic calculations used to convert
D&D 3.x vitality-related data into MonsterForge domain values.

Rules:
- Base vitality is determined by creature size.
- Hit dice contributions are converted using deterministic average
  dice values.
- Total vitality is calculated by combining size vitality with
  hit dice contribution.

The static rule tables are defined in rules/dnd/v3x/vitality_tables.py
and consumed by this module.

This module contains calculation logic only; it does not define
source data structures or static rule mappings.
"""
from monsterforge.rules.dnd.v3x.vitality_tables import SIZE_HP_TABLE, DICE_AVERAGE_HP
from monsterforge.structured_data.dnd.v3x.enums import Size, DiceType

# =====================
# LIFE
# =====================
def calculate_life_value(*,creature_size: Size,hit_dice_type: DiceType, num_hit_dice: int = 1) -> int:
    """
    Calculate deterministic vitality value from D&D 3.x creature data.

    Rules:
    - Each creature size provides a fixed base vitality value.
    - Each hit die type is converted using its deterministic average value.
    - Total vitality is calculated as:
        size vitality + (number of hit dice * average hit die value)

    Example:
        Medium creature with 2d8 hit dice:
            15 + (2 * 4) = 23
    """   
    return (
    SIZE_HP_TABLE[creature_size]
    + num_hit_dice * DICE_AVERAGE_HP[hit_dice_type]
    )
