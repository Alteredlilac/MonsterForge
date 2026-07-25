"""
Tests for the SpecialAbility base model shared by SpecialAttack and
SpecialQuality.
"""
from monsterforge.structured_data.dnd.v3x.special_ability import SpecialAbility
from monsterforge.structured_data.dnd.v3x.enums import SpecialAbilityType


def test_special_ability_minimal_creation():
    ability = SpecialAbility(
        name="Darkvision", special_ability_type=SpecialAbilityType.EXTRAORDINARY,
    )
    assert ability.name == "Darkvision"
    assert ability.description is None


def test_special_ability_auto_generates_unique_id():
    a1 = SpecialAbility(name="A", special_ability_type=SpecialAbilityType.SUPERNATURAL)
    a2 = SpecialAbility(name="B", special_ability_type=SpecialAbilityType.SUPERNATURAL)
    assert a1.id != a2.id


def test_special_ability_supports_three_types():
    for ability_type in (
        SpecialAbilityType.EXTRAORDINARY,
        SpecialAbilityType.SUPERNATURAL,
        SpecialAbilityType.SPELL_LIKE,
    ):
        ability = SpecialAbility(name="X", special_ability_type=ability_type)
        assert ability.special_ability_type == ability_type
