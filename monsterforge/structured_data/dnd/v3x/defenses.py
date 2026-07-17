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
    reduction_value: int              # es. 5, 10, 15
    bypass_type: str | None = None    # es. "magic", "silver", "cold iron" usato str, invece di enum per compatibilità


@dataclass(kw_only=True)
class DamageResistance:
    damage_type: DamageType          # elementali (fuoco, freddo), energia (positiva/negativa), tipo (contundenti)
    resistance_value: int             # es. 10, 20, 30


@dataclass(kw_only=True)
class Regeneration:
    regeneration_value: int           # es. 5 (PF recuperati per round)
    bypass_damage_types: list[DamageType] = field(default_factory=list)  # es. [FIRE, ACID]