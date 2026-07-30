"""
Static mappings for Body and Spirit stat calculation.

This module defines the relationships between D&D 3.x ability scores
and the target system's physical (Body) and mental (Spirit) stats.

It provides immutable mapping tables, including standard mappings and
special-case overrides (e.g. undead, constructs).

These mappings are consumed by the transformation layer, where
ability modifiers are normalized (negative values treated as 0) and
used to derive final stat values.

Notes:
- Some creatures may override standard mappings (e.g. defense source stat).
- Additional conditional rules (e.g. caster-based stat swaps) are handled
  during transformation, not in this module.
"""
# NOTE:
# These tables represent game rules and are intentionally immutable.
# They should not be modified during runtime.
from typing import Mapping
from types import MappingProxyType


# =====================
# BODY STAT MAPPINGS
# =====================
# Default mapping for physical stats
BODY_STAT_MAPPING: Mapping[str, str] = MappingProxyType({
    "attack": "strength",
    "defense": "constitution",
    "speed": "dexterity",
})

# Undead override: defense is based on dexterity
UNDEAD_BODY_STAT_MAPPING: Mapping[str, str] = MappingProxyType({
    "attack": "strength",
    "defense": "dexterity",
    "speed": "dexterity",
})

# Construct override: defense is based on strength
CONSTRUCT_BODY_STAT_MAPPING: Mapping[str, str] = MappingProxyType({
    "attack": "strength",
    "defense": "strength",
    "speed": "dexterity",
})


# =====================
# SPIRIT STAT MAPPING
# =====================
# Default mapping for spiritual stats
SPIRIT_STAT_MAPPING: Mapping[str, str] = MappingProxyType({
    "power": "intelligence",
    "ward": "wisdom",
    "flow": "charisma",
})