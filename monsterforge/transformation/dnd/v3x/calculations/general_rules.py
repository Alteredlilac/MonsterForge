"""
Deterministic rule applications for D&D 3.x transformation.

This module defines functions that apply domain-specific rules
to normalize values from D&D 3.x into MonsterForge deterministic values.

Rules:
- Dice-based values are converted into deterministic numerical values
  using dice rules.
- Certain values (e.g. healing, drained abilities) are reduced using
  floor-based transformations with a minimum threshold.
- Progression rates are resolved into per-level values using
  progression tables.

These functions are used by the transformation layer to convert
structured_data into domain objects.

They rely on rule tables and general math utilities, but do not define
static mappings themselves.
"""
from monsterforge.structured_data.dnd.v3x.enums import DiceType, ProgressionRate
from .general_math import floor_value, halve_value, convert_dice_to_value
from monsterforge.rules.dnd.v3x.progression_tables import SPELLS_PER_LEVEL_MAPPING, COMBAT_ABILITIES_PER_LEVEL_MAPPING

# =====================
# DRAINED ABILITY
# =====================
def calculate_drained_ability_value(value: DiceType) -> int:
    """
    Convert a D&D 3.x drained ability value into a deterministic value.

    Rules:
    - Dice-based values are converted using their average value.
    - The result is halved using floor rounding.
    - The final value has a minimum of 1 and cannot be negative.

    Examples:
        D6 -> 3 -> 1
        D8 -> 4 -> 2
    """
    return halve_value(convert_dice_to_value(value))

# =====================
# DAMAGE
# =====================
def normalize_damage(value: DiceType) -> int:
    """
    Convert a D&D 3.x damage value into a deterministic value.

    Rules:
    - Dice-based values are converted using their average value.

    Examples:
        D6 -> 3
        D8 -> 4
    """
    return convert_dice_to_value(value)

# =====================
# HEALING
# =====================
def normalize_healing(value: DiceType | int) -> int:
    """
    Normalize healing values from D&D 3.x into deterministic values.

    Rules:
    - DiceType values are converted using their average value. #valore delle dice_rules
    - Absolute integer values are halved using floor rounding,
      with a minimum result of 1.

    Examples:
        D6 -> 3
        5 -> 2
    """
    if isinstance(value, DiceType):
        return convert_dice_to_value(value)
    
    if isinstance(value, int):
        return halve_value(value)
    
    raise TypeError("value must be an int or DiceType")
    

# =====================
# SPELLS PER LEVEL
# =====================
def calculate_known_spells_per_level(progression_rate: ProgressionRate) -> int:
    """
    Calculate the number of known spells gained per level
    from a D&D 3.x progression rate.
    """
    return SPELLS_PER_LEVEL_MAPPING[progression_rate]


# =====================
# ABILITIES PER LEVEL
# =====================
def calculate_combat_abilities_per_level(
    progression_rate: ProgressionRate
) -> int:
    """
    Calculate the number of known combat abilities gained per level
    from a D&D 3.x progression rate.
    """
    return COMBAT_ABILITIES_PER_LEVEL_MAPPING[progression_rate]
