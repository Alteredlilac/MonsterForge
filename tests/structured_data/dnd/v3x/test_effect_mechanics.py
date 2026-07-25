"""
Tests for shared mechanical components: EffectRange, CriticalHit,
SavingThrow, EffectDuration, EffectUsage, EffectArea, DamageOverTime,
EffectTarget, EffectModifier, EffectGrant.
"""
from monsterforge.structured_data.dnd.v3x.enums import (
    SavingThrowEffect, Duration, Usage, TargetType,
    ModifierTarget, GrantedType,
)


def test_saving_throw_defaults_to_negates(make_saving_throw):
    save = make_saving_throw()
    assert save.saving_throw_effect == SavingThrowEffect.NEGATES


def test_saving_throw_can_override_effect(make_saving_throw):
    save = make_saving_throw(saving_throw_effect=SavingThrowEffect.HALF)
    assert save.saving_throw_effect == SavingThrowEffect.HALF


def test_effect_duration_defaults_to_instant(make_effect_duration):
    duration = make_effect_duration()
    assert duration.duration == Duration.INSTANT
    assert duration.duration_time is None


def test_effect_usage_defaults_to_unlimited(make_effect_usage):
    usage = make_effect_usage()
    assert usage.usage == Usage.UNLIMITED
    assert usage.requires_recharge is False


def test_effect_usage_with_recharge(make_effect_usage, make_time_expression):
    usage = make_effect_usage(
        usage=Usage.LIMITED, requires_recharge=True,
        recharge_time=make_time_expression(),
    )
    assert usage.requires_recharge is True
    assert usage.recharge_time is not None


def test_damage_over_time_creation(make_damage_over_time):
    dot = make_damage_over_time()
    assert dot.damage_frequency is not None
    assert len(dot.damages) == 1
    assert dot.occurrences is None  # None = indefinite


def test_effect_target_optional_fields_default(make_effect_target):
    target = make_effect_target()
    assert target.target_type == TargetType.CREATURE
    assert target.target_alignment == []
    assert target.creature_type is None


def test_effect_modifier_creation(make_effect_modifier):
    modifier = make_effect_modifier(target=ModifierTarget.DAMAGE, modifier=2)
    assert modifier.target == ModifierTarget.DAMAGE
    assert modifier.modifier == 2


def test_effect_grant_default_amount_is_one(make_effect_grant):
    grant = make_effect_grant()
    assert grant.amount == 1
    assert grant.grant_type == GrantedType.CREATURE


def test_effect_grant_amount_can_be_dice(make_effect_grant, make_dice):
    """A grant's amount can be a fixed int or a dice expression
    (e.g. 'summons 2d4 wolves')."""
    dice_amount = make_dice(dice_number=2)
    grant = make_effect_grant(amount=dice_amount)
    assert grant.amount is dice_amount
