"""
Tests for the SpecialQuality model.
"""
from monsterforge.structured_data.dnd.v3x.special_qualities import SpecialQuality
from monsterforge.structured_data.dnd.v3x.enums import SpecialAbilityType, DamageType


def test_special_quality_minimal_creation():
    darkvision = SpecialQuality(
        name="Darkvision", special_ability_type=SpecialAbilityType.EXTRAORDINARY,
    )
    assert darkvision.name == "Darkvision"
    assert darkvision.always_active is True
    assert darkvision.requires_action is False


def test_special_quality_can_require_action():
    """always_active and requires_action are independent flags: a
    shapeshifting form can be both 'always active once assumed' and
    'requires an action to trigger' (e.g. werewolf forms)."""
    quality = SpecialQuality(
        name="Wolf Form", special_ability_type=SpecialAbilityType.SUPERNATURAL,
        always_active=True, requires_action=True,
    )
    assert quality.always_active is True
    assert quality.requires_action is True


def test_special_quality_with_damage_reduction(make_damage_reduction):
    quality = SpecialQuality(
        name="Damage Reduction",
        special_ability_type=SpecialAbilityType.EXTRAORDINARY,
        damage_reduction=make_damage_reduction(reduction_value=10, bypass_type="magic"),
    )
    assert quality.damage_reduction.reduction_value == 10


def test_special_quality_with_resistances_and_vulnerabilities(make_damage_resistance):
    quality = SpecialQuality(
        name="Elemental Nature",
        special_ability_type=SpecialAbilityType.EXTRAORDINARY,
        damage_resistances=[make_damage_resistance(damage_type=DamageType.COLD)],
        vulnerabilities=[DamageType.FIRE],
    )
    assert quality.damage_resistances[0].damage_type == DamageType.COLD
    assert DamageType.FIRE in quality.vulnerabilities


def test_special_quality_immunities_are_open_strings():
    quality = SpecialQuality(
        name="Immunities",
        special_ability_type=SpecialAbilityType.EXTRAORDINARY,
        immunities=["poison", "disease", "sleep"],
    )
    assert "poison" in quality.immunities


def test_special_quality_with_regeneration(make_regeneration):
    quality = SpecialQuality(
        name="Regeneration",
        special_ability_type=SpecialAbilityType.EXTRAORDINARY,
        regeneration=make_regeneration(regeneration_value=5),
    )
    assert quality.regeneration.regeneration_value == 5


def test_special_quality_with_granted_movement(make_movement):
    quality = SpecialQuality(
        name="Flight", special_ability_type=SpecialAbilityType.SUPERNATURAL,
        granted_movement=[make_movement()],
    )
    assert len(quality.granted_movement) == 1
