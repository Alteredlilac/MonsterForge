"""
General deterministic mathematical rules used during transformation.

This module defines reusable calculation helpers that are not tied
to a specific game concept, but are used to normalize values during
the conversion from structured_data into domain objects.

Rules:
- Decimal values are always rounded down.
- Absolute values can be reduced by half using floor rounding.
- Dice values are converted into deterministic averages.
"""
import math
from monsterforge.rules.dnd.v3x.dice_rules import DICE_AVERAGE_VALUES
from monsterforge.structured_data.dnd.v3x.enums import DiceType


def floor_value(value: float) -> int:
    """
   Convert a decimal value into an integer using floor rounding.

    MonsterForge always rounds decimal conversion results down
    during the transformation process.

    Example:
        4.9 -> 4
        2.1 -> 2
    """
    return math.floor(value)

def feet_to_meters(feet: int | float) -> float:
    """
    Convert D&D 3.x feet-based measurements into MonsterForge meters.

    Some values in D&D 3.x are expressed in feet and must be
    converted into the metric system used by MonsterForge.
    """
    # NOTE:
    # D&D 3.x movement values are based on a 5-foot grid.
    # When converting to meters, values are normalized to the nearest
    # 1.5 meter increment to preserve the original movement scale.
    meters = feet * 0.3048
    return round(meters / 1.5) * 1.5


def halve_value(value: int) -> int:
    """
    Halve an integer value using floor rounding, ignoring the sign,
    with a minimum result of 1.

    Used when absolute magnitude values from D&D 3.x are converted
    into reduced deterministic values. Negative inputs are treated
    as positive magnitudes.

    Examples:
        5 -> 2
        4 -> 2
        1 -> 1
        0 -> 1
        -5 -> 2
    """
    return max(1, abs(value) // 2)

# NOTE:
# Values are stored as absolute values without sign.
# The positive or negative behavior is handled elsewhere based on
# the effect semantics.
#
# Examples:
# - damage: decreases the target value
# - healing: increases the target value
# - bonus: increases the target value
# - penalty: decreases the target value


def convert_dice_to_value(dice_type: DiceType) -> int:
    """
    Convert a D&D 3.x dice type into its deterministic MonsterForge value.

    Dice-based values from D&D 3.x are normalized into fixed numerical
    values during transformation instead of being randomly evaluated.

    Example:
        D6 -> 3
        D8 -> 4
    """  
    return DICE_AVERAGE_VALUES[dice_type]
