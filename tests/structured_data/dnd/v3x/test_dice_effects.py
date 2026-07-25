"""
Tests for shared dice-based effect representations: Dice, Damage,
Healing, TimeExpression.
"""
from monsterforge.structured_data.dnd.v3x.enums import DiceType, DamageType, Ability
from monsterforge.structured_data.dnd.v3x.dice_effects import Dice


def test_dice_all_fields_optional():
    dice = Dice()
    assert dice.dice_number is None
    assert dice.dice_type is None
    assert dice.modifier is None


def test_damage_minimal_creation(make_damage):
    dmg = make_damage()
    assert dmg.dice_number == 1
    assert dmg.dice_type == DiceType.D6
    assert dmg.damage_type == DamageType.PHYSICAL


def test_damage_with_bonus_damage(make_damage):
    """A Damage entry can carry both a base damage die and a bonus damage
    component of a different type (e.g. a flaming sword: base physical +
    bonus fire)."""
    dmg = make_damage(damage_bonus=2, damage_bonus_type=DamageType.FIRE)
    assert dmg.damage_bonus == 2
    assert dmg.damage_bonus_type == DamageType.FIRE


def test_damage_affected_ability_optional(make_damage):
    dmg = make_damage(affected_ability=Ability.STRENGTH)
    assert dmg.affected_ability == Ability.STRENGTH


def test_healing_restores_full_amount_defaults_to_false(make_healing):
    heal = make_healing()
    assert heal.restores_full_amount is False


def test_healing_can_restore_full_amount(make_healing):
    heal = make_healing(restores_full_amount=True)
    assert heal.restores_full_amount is True


def test_time_expression_creation(make_time_expression):
    te = make_time_expression(dice_number=2, dice_type=DiceType.D4)
    assert te.dice_number == 2
    assert te.dice_type == DiceType.D4
