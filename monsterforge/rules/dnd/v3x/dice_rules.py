
"""
Static tables for D&D 3.x dice conversion rules.

This module defines immutable deterministic mappings used to convert
dice-based values into fixed numerical values during the transformation
pipeline.

Rules:
- Each DiceType maps to its average roll value.
- Dice rolls are normalized into deterministic values instead of being
  randomly evaluated.

Example:
    A D6 value is converted into:
        dice_value = 3
"""
# NOTE:
# These tables represent game rules and are intentionally immutable.
# They should not be modified during runtime.
from typing import Mapping
from types import MappingProxyType
from monsterforge.structured_data.dnd.v3x.enums import DiceType


# =====================
# DICE RULES
# =====================
# Average numerical value for each dice type
DICE_AVERAGE_VALUES: Mapping[DiceType, int] = MappingProxyType({
    DiceType.D4: 2,
    DiceType.D6: 3,
    DiceType.D8: 4,
    DiceType.D10: 5,
    DiceType.D12: 6,
    }) 
