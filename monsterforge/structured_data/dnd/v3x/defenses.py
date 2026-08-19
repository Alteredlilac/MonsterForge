"""
Shared defensive trait representations for D&D 3.x creatures.

Unlike effect_mechanics.py (which describes how an effect behaves when
actively applied, e.g. an attack or spell), this module represents
passive/innate defensive properties: damage reduction, energy resistance
and immunity, and regeneration. Used primarily by special_qualities.py,
but potentially relevant to creature templates (CreatureModifier) as well.
"""
from dataclasses import dataclass, field
from .enums import DamageType


@dataclass(kw_only=True)
class DamageReduction:
    reduction_value: int              # e.g. 5, 10, 15
    bypass_type: str | None = None    # e.g. "magic", "silver", "cold iron" — kept as str rather than an enum for flexibility


@dataclass(kw_only=True)
class DamageResistance:
    damage_type: DamageType          # elemental (fire, cold), energy (positive/negative), or type (bludgeoning)
    resistance_value: int             # e.g. 10, 20, 30


@dataclass(kw_only=True)
class Regeneration:
    regeneration_value: int           # e.g. 5 (HP recovered per round)
    bypass_damage_types: list[DamageType] = field(default_factory=list)  # e.g. [FIRE, ACID]