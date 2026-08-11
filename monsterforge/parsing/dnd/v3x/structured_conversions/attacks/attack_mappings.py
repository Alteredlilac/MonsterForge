"""
Mapping data used to convert raw D&D 3.x attacks into structured attacks.

This module contains known attack properties, such as range and damage type,
used by the structured conversion layer.
"""
from dataclasses import dataclass
from monsterforge.structured_data.dnd.v3x.enums import DamageType
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import UnitSystem

# TODO completare la tabella KNOWN_ATTACKS


@dataclass(frozen=True)
class AttackProperties:
    range: EffectRange | None
    damage_type: DamageType | None


KNOWN_ATTACKS = {
    "shortbow": AttackProperties(
        range=EffectRange(
            effect_range=20,
            range_unit_system=UnitSystem.IMPERIAL,
        ),
        damage_type=DamageType.PIERCING,
    ),
    "morningstar": AttackProperties(
        range=None,
        damage_type=DamageType.BLUDGEONING,
    ),
}