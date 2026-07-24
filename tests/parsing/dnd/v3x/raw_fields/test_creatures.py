"""
Tests for raw creature stat block models.

Covers:
- Basic dataclass construction
- Special ability inheritance
- Nested structures (movement, saves, abilities, attacks)
- Default list values
- Raw string preservation
"""

from monsterforge.parsing.dnd.v3x.raw_fields.creatures import (
    Movement,
    SpecialAbility,
    SpecialAttack,
    SpecialQuality,
    Saves,
    Abilities,
    Skill,
    Creature,
)

from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import FullAttack


# =====================
# INHERITANCE
# =====================

def test_special_attack_is_special_ability():
    assert issubclass(SpecialAttack, SpecialAbility)


def test_special_quality_is_special_ability():
    assert issubclass(SpecialQuality, SpecialAbility)


# =====================
# BASIC STRUCTURES
# =====================

def test_movement_creation():
    movement = Movement(
        description="fly 60 ft."
    )

    assert movement.description == "fly 60 ft."


def test_skill_creation():
    skill = Skill(
        name="Listen",
        modifier="+8"
    )

    assert skill.name == "Listen"


def test_saves_preserve_description_for_special_cases():
    saves = Saves(
        description="Uses master's saves"
    )

    assert saves.description == "Uses master's saves"


def test_abilities_allow_missing_values():
    abilities = Abilities(
        strength="-",
        constitution=None,  # qui non lo dichiareri 
    )

    assert abilities.strength == "-"
    assert abilities.constitution is None


# =====================
# SPECIAL ABILITIES
# =====================

def test_special_attack_creation():
    attack = SpecialAttack(
        name="Poison",
        type_description="Ex",
        description="Deals constitution damage"
    )

    assert attack.name == "Poison"
    assert attack.type_description == "Ex"


def test_special_quality_creation():
    quality = SpecialQuality(
        name="Darkvision",
        type_description="Ex",
        description="Sees in darkness"
    )

    assert quality.name == "Darkvision"


# =====================
# CREATURE
# =====================

def test_creature_defaults_lists_are_empty():
    creature = Creature(
        name="Wolf",
        size="Medium",
        type="Animal",
        hit_dice="2d8+4",
        total_life="13 hp",
        initiative="+2",
        armor_class="14",
        touch="12",
        flat_footed="12",
        base_attack="+1",
        grapple="+2",
        space="5 ft.",
        reach="5 ft.",
        saves=Saves(),
        abilities=Abilities(),
        environment="Temperate forests",
        challenge_rating="1",
        alignment="Neutral",
    )

    assert creature.subtype == []
    assert creature.speed == []
    assert creature.special_attacks == []
    assert creature.special_qualities == []
    assert creature.skills == []
    assert creature.feats == []


def test_creature_with_nested_data():
    movement = Movement(
        name="fly",
        description="60 ft."
    )

    attack = Attack(
        name="Bite",
        modifier="+3",
        attack_type="melee",
        attack_effect="1d6+1"
    )

    full_attack = FullAttack(
        attacks=[attack]
    )

    creature = Creature(
        name="Young Dragon",
        size="Small",
        type="Dragon",
        subtype=["Fire"],
        hit_dice="5d12+10",
        total_life="42 hp",
        initiative="+4",
        speed=[movement],
        armor_class="18",
        touch="15",
        flat_footed="14",
        base_attack="+5",
        grapple="+7",
        attack=attack,
        full_attack=full_attack,
        space="5 ft.",
        reach="5 ft.",
        saves=Saves(
            fortitude_save="+5",
            reflex_save="+4",
            will_save="+5",
        ),
        abilities=Abilities(
            strength="15",
            charisma="12",
        ),
        environment="Mountains",
        challenge_rating="3",
        alignment="Chaotic Evil",
    )

    assert creature.speed[0].name == "fly"
    assert creature.attack.name == "Bite"
    assert creature.full_attack.attacks[0].name == "Bite"
    assert creature.abilities.strength == "15"


# =====================
# RAW DATA PRESERVATION
# =====================

def test_creature_preserves_raw_values():
    creature = Creature(
        name="Spectre",
        size="Medium",
        type="Undead",
        hit_dice="7d12",
        total_life="45 hp",
        initiative="+7",
        armor_class="15",
        touch="15",
        flat_footed="12",
        base_attack="+3",
        grapple="-",
        space="5 ft.",
        reach="5 ft.",
        saves=Saves(),
        abilities=Abilities(
            strength="-",
            constitution="-",
        ),
        environment="Any",
        challenge_rating="7",
        alignment="Chaotic Evil",
    )

    # Values remain source-formatted and are not interpreted
    assert creature.hit_dice == "7d12"
    assert creature.abilities.strength == "-"
    