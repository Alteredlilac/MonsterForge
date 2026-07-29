"""
Static tables for vitality (HP) calculation.

This module defines immutable deterministic mappings used by the
vitality calculation pipeline.

Rules:
- Each Size maps to a fixed base vitality value.
- Each DiceType maps to its average roll value.
- The final vitality value is calculated during the transformation stage
  by combining the size base value with the average hit dice contribution.

Example:
    A Medium creature with 2d8 hit dice:
        base_hp = 15
        dice_avg = 4
        total = 15 + (2 * 4) = 23
"""
# NOTE:
# These tables represent game rules and are intentionally immutable.
# They should not be modified during runtime.
from monsterforge.structured_data.dnd.v3x.enums import Size, DiceType
from typing import Mapping
from types import MappingProxyType

# =====================
# VITALITY RULES
# =====================

# Base vitality value by creature size
SIZE_HP_TABLE: Mapping[Size, int] = MappingProxyType({
    Size.FINE: 1,
    Size.DIMINUTIVE: 2,
    Size.TINY: 5,
    Size.SMALL: 10,
    Size.MEDIUM: 15,
    Size.LARGE: 30,
    Size.HUGE: 45,
    Size.GARGANTUAN: 60,
    Size.COLOSSAL: 90,
})

# Average HP value per hit die type
DICE_AVERAGE_HP: Mapping[DiceType, int] = MappingProxyType({
    DiceType.D4: 2,
    DiceType.D6: 3,
    DiceType.D8: 4,
    DiceType.D10: 5,
    DiceType.D12: 6,
})
