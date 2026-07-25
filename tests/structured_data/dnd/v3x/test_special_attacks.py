"""
Tests for the SpecialAttack model.
"""
from monsterforge.structured_data.dnd.v3x.special_attacks import SpecialAttack
from monsterforge.structured_data.dnd.v3x.enums import SpecialAbilityType


def test_special_attack_minimal_creation(make_effect_target):
    breath = SpecialAttack(
        name="Breath Weapon",
        special_ability_type=SpecialAbilityType.SUPERNATURAL,
        target=make_effect_target(),
    )
    assert breath.name == "Breath Weapon"
    assert breath.melee is True
    assert breath.area_effect is False


def test_special_attack_inherits_from_special_ability(make_effect_target):
    from monsterforge.structured_data.dnd.v3x.special_ability import SpecialAbility
    attack = SpecialAttack(
        name="X", special_ability_type=SpecialAbilityType.EXTRAORDINARY,
        target=make_effect_target(),
    )
    assert isinstance(attack, SpecialAbility)


def test_special_attack_with_damage_and_saving_throw(
    make_effect_target, make_damage, make_saving_throw,
):
    breath = SpecialAttack(
        name="Breath Weapon",
        special_ability_type=SpecialAbilityType.SUPERNATURAL,
        target=make_effect_target(),
        damages=[make_damage(dice_number=6)],
        saving_throw=make_saving_throw(saving_throw_value=18),
    )
    assert breath.damages[0].dice_number == 6
    assert breath.saving_throw.saving_throw_value == 18


def test_special_attack_area_effect_flag(make_effect_target, make_effect_area):
    breath = SpecialAttack(
        name="Cone of Cold",
        special_ability_type=SpecialAbilityType.SPELL_LIKE,
        target=make_effect_target(),
        area_effect=True,
        area_of_effect=make_effect_area(),
    )
    assert breath.area_effect is True
    assert breath.area_of_effect is not None


def test_special_attack_default_duration_and_usage(make_effect_target):
    """duration and usage have factory defaults, unlike most other
    optional components on this class."""
    attack = SpecialAttack(
        name="X", special_ability_type=SpecialAbilityType.EXTRAORDINARY,
        target=make_effect_target(),
    )
    assert attack.duration is not None
    assert attack.usage is not None
