"""
Lookup mappings used to convert raw D&D 3.x attack-effect values into
structured enum values.

This module defines the deterministic mappings used by the attack-effects
parser and its helper functions to translate known textual values from raw
D&D 3.x "attack_effect" fields into the corresponding "structured_data"
enums.

The lookup mappings include:

- textual damage types mapped to DamageType values
- textual ability names and abbreviations mapped to Ability values

The mappings are intentionally limited to known and explicitly supported
D&D 3.x values. Unknown textual values are not resolved by this module and
are handled by the parser or by the semantic classification layer when
appropriate.
"""
from monsterforge.structured_data.dnd.v3x.enums import Ability, DamageType

# =====================
# DAMAGE TYPE
# =====================
DAMAGE_TYPE_MAP = {
    "bludgeoning": DamageType.BLUDGEONING,
    "slashing": DamageType.SLASHING,
    "piercing": DamageType.PIERCING,
    "physical": DamageType.PHYSICAL,

    "fire": DamageType.FIRE,
    "cold": DamageType.COLD,
    "acid": DamageType.ACID,
    "electricity": DamageType.ELECTRICITY,
    "sonic": DamageType.SONIC,

    "disintegration": DamageType.DISINTEGRATION,
    "force": DamageType.FORCE,

    "negative energy": DamageType.NEGATIVE_ENERGY,
    "positive energy": DamageType.POSITIVE_ENERGY,

    "energy drain": DamageType.ENERGY_DRAIN,
}

# =====================
# ABILITY
# =====================
ABILITY_MAP = {
    "str": Ability.STRENGTH,
    "strength": Ability.STRENGTH,

    "dex": Ability.DEXTERITY,
    "dexterity": Ability.DEXTERITY,

    "con": Ability.CONSTITUTION,
    "constitution": Ability.CONSTITUTION,

    "int": Ability.INTELLIGENCE,
    "intelligence": Ability.INTELLIGENCE,

    "wis": Ability.WISDOM,
    "wisdom": Ability.WISDOM,

    "cha": Ability.CHARISMA,
    "charisma": Ability.CHARISMA,
}
