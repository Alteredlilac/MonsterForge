"""
Static mappings between D&D 3.x structured_data enums and MonsterForge
domain enums. Used by converters/ to translate classified/typed values
from the source system into the generic card-game vocabulary.
"""
# NOTE:
# These tables represent game rules and are intentionally immutable.
# They should not be modified during runtime.
from types import MappingProxyType
from typing import Mapping
from monsterforge.structured_data.dnd.v3x.enums import (DamageType as StructDamageType,
                                                        Ability)
from monsterforge.domain.enums import (DamageType as DomainDamageType, AffectedAttribute)


# =====================
# DAMAGE TYPE
# =====================
DAMAGE_TYPE_MAPPING: Mapping[StructDamageType, DomainDamageType] = MappingProxyType({
    # Physical
    StructDamageType.BLUDGEONING: DomainDamageType.PHYSICAL,
    StructDamageType.SLASHING: DomainDamageType.PHYSICAL,
    StructDamageType.PIERCING: DomainDamageType.PHYSICAL,
    StructDamageType.PHYSICAL: DomainDamageType.PHYSICAL,
    # Energy Damage
    StructDamageType.FIRE: DomainDamageType.FIRE,
    StructDamageType.COLD: DomainDamageType.COLD,
    StructDamageType.ACID: DomainDamageType.ACID,
    StructDamageType.ELECTRICITY: DomainDamageType.LIGHTNING,
    StructDamageType.SONIC: DomainDamageType.THUNDER,
    # Force / Disintegration
    StructDamageType.DISINTEGRATION: DomainDamageType.DISINTEGRATION,
    StructDamageType.FORCE: DomainDamageType.PHYSICAL,
    # Negative / Positive Energy
    StructDamageType.NEGATIVE_ENERGY: DomainDamageType.NEGATIVE_ENERGY,
    StructDamageType.POSITIVE_ENERGY: DomainDamageType.POSITIVE_ENERGY,
    # Energy Drain
    StructDamageType.ENERGY_DRAIN: DomainDamageType.NEGATIVE_ENERGY,
})


# =====================
# ABILITY DAMAGE
# =====================
ABILITY_DAMAGE_MAPPING: Mapping[Ability, AffectedAttribute] = MappingProxyType({
    Ability.STRENGTH: AffectedAttribute.ATTACK,
    Ability.DEXTERITY: AffectedAttribute.SPEED,
    Ability.CONSTITUTION: AffectedAttribute.DEFENSE,
    Ability.INTELLIGENCE: AffectedAttribute.POWER,
    Ability.WISDOM: AffectedAttribute.WARD,
    Ability.CHARISMA: AffectedAttribute.FLOW,
})
