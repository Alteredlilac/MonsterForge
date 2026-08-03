"""
Static progression tables for D&D 3.x transformation.

This module defines immutable deterministic mappings and constants
used to convert progression-related rules from D&D 3.x into
MonsterForge domain values.

Rules:
- Spell progression maps each ProgressionRate to the number of
  known spells gained per level.
- Combat progression maps each ProgressionRate to the number of
  known combat abilities (attacks/defenses) gained per level.
- Character classes gain a fixed number of skill points per level.

These values are consumed by the transformation layer.
They do not contain calculation logic.
"""
# NOTE:
# These tables represent game rules and are intentionally immutable.
# They should not be modified during runtime.
from typing import Mapping
from types import MappingProxyType
from monsterforge.structured_data.dnd.v3x.enums import ProgressionRate

# =====================
# SKILLS
# =====================

# Number of skill points gained per character level.
SKILL_POINTS_PER_LEVEL: int = 1


# =====================
# PROGRESSION LEVEL MAPPING
# =====================

SPELLS_PER_LEVEL_MAPPING: Mapping[ProgressionRate, int] = MappingProxyType({
    ProgressionRate.LOW: 1,
    ProgressionRate.MEDIUM: 2,
    ProgressionRate.HIGH: 3,
})


COMBAT_ABILITIES_PER_LEVEL_MAPPING: Mapping[ProgressionRate, int] = MappingProxyType({
    ProgressionRate.LOW: 1,
    ProgressionRate.MEDIUM: 2,
    ProgressionRate.HIGH: 3,
})
