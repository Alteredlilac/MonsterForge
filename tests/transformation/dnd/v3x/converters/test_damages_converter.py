"""
Tests for damages_converter.py: structured_data.Damage -> domain.MoveEffect.

Covers:
- damage_category() classification for all 8 dispatch categories
- one behavioral test per resolver in DAMAGE_RESOLVERS
- regression coverage for the damage_bonus_type/damage_type bug: a
  bonus-only damage component (no dice) had its detected type silently
  discarded and defaulted to PHYSICAL/ENERGY_DRAIN, because
  resolve_modifier()/resolve_drain_modifier() read damage_bonus_type,
  a field the parser never populates, instead of damage_type
"""
import pytest
from monsterforge.structured_data.dnd.v3x.dice_effects import Damage
from monsterforge.structured_data.dnd.v3x.enums import DiceType, DamageType, Ability
from monsterforge.domain.enums import DamageType as DomainDamageType, AffectedAttribute
from monsterforge.domain.moves import MoveEffect
from monsterforge.transformation.dnd.v3x.converters.damages_converter import (
    damage_category,
    resolve_dice_drain_modifier,
    resolve_dice_drain,
    resolve_drain_modifier,
    resolve_dice_modifier,
    resolve_dice,
    resolve_modifier,
    resolve_drain,
    resolve_no_values,
    InvalidDamageConfigurationError,
)


# =====================
# DAMAGE CATEGORY CLASSIFICATION
# =====================
@pytest.mark.parametrize(
    "damage, expected_category",
    [
        (Damage(dice_type=DiceType.D6, affected_ability=Ability.WISDOM, damage_bonus=2), "dice_drain_modifier"),
        (Damage(dice_type=DiceType.D6, affected_ability=Ability.WISDOM), "dice_drain"),
        (Damage(affected_ability=Ability.WISDOM, damage_bonus=2), "drain_modifier"),
        (Damage(dice_type=DiceType.D6, damage_bonus=2), "dice_modifier"),
        (Damage(dice_type=DiceType.D6), "dice"),
        (Damage(affected_ability=Ability.WISDOM), "drain"),
        (Damage(damage_bonus=2), "modifier"),
        (Damage(), "none"),
    ],
)
def test_damage_category_classification(damage, expected_category):
    assert damage_category(damage) == expected_category


# =====================
# RESOLVE_DICE
# =====================
def test_resolve_dice_defaults_to_physical():
    d = Damage(dice_number=1, dice_type=DiceType.D6)
    effects = resolve_dice(d)
    assert effects == [MoveEffect(damage_type=DomainDamageType.PHYSICAL, effect_value=3)]


def test_resolve_dice_uses_explicit_type():
    d = Damage(dice_number=2, dice_type=DiceType.D8, damage_type=DamageType.FIRE)
    effects = resolve_dice(d)
    assert effects == [MoveEffect(damage_type=DomainDamageType.FIRE, effect_value=8)]


# =====================
# RESOLVE_MODIFIER
# =====================
def test_resolve_modifier_defaults_to_physical():
    d = Damage(damage_bonus=5)
    effects = resolve_modifier(d)
    assert effects == [MoveEffect(damage_type=DomainDamageType.PHYSICAL, effect_value=5)]


def test_resolve_modifier_uses_damage_type_not_damage_bonus_type():
    """Regression: a bonus-only component (e.g. "plus 1 fire") must keep
    its detected type. The parser writes it to damage_type, never to
    damage_bonus_type -- reading the latter silently produced PHYSICAL
    for every typed bonus-only damage in the real pipeline."""
    d = Damage(damage_bonus=1, damage_type=DamageType.FIRE)
    effects = resolve_modifier(d)
    assert effects == [MoveEffect(damage_type=DomainDamageType.FIRE, effect_value=1)]


# =====================
# RESOLVE_DICE_MODIFIER
# =====================
def test_resolve_dice_modifier_same_type_combines_into_one_effect():
    """2d4+5 fire damage -> a single FIRE effect, dice and modifier summed."""
    d = Damage(dice_number=2, dice_type=DiceType.D4, damage_type=DamageType.FIRE,
               damage_bonus=5, damage_bonus_type=DamageType.FIRE)
    effects = resolve_dice_modifier(d)
    assert effects == [MoveEffect(damage_type=DomainDamageType.FIRE, effect_value=9)]


def test_resolve_dice_modifier_negative_modifier_clamps_to_minimum_one():
    """1d4-2 physical damage: D4 averages 2, minus 2 -> 0, clamped to the
    D&D rule that a dice-based damage roll always deals at least 1
    point. Regression case: found as a real 0-damage MoveEffect on a
    "Bite 1d4-2" attack in committed gallery output."""
    d = Damage(dice_number=1, dice_type=DiceType.D4, damage_bonus=-2)
    effects = resolve_dice_modifier(d)
    assert effects == [MoveEffect(damage_type=DomainDamageType.PHYSICAL, effect_value=1)]


def test_resolve_dice_modifier_defaults_both_components_to_physical():
    d = Damage(dice_number=1, dice_type=DiceType.D6, damage_bonus=3)
    effects = resolve_dice_modifier(d)
    assert effects == [MoveEffect(damage_type=DomainDamageType.PHYSICAL, effect_value=6)]


def test_resolve_dice_modifier_different_types_split_into_two_effects():
    """1d8 fire damage +2 acid damage. Exercises the "different types on
    one Damage" branch via damage_bonus_type, set explicitly here since
    the real parser never populates it (see the NOTE: in the source) --
    the resolver itself still supports this shape."""
    d = Damage(dice_number=1, dice_type=DiceType.D8, damage_type=DamageType.FIRE,
               damage_bonus=2, damage_bonus_type=DamageType.ACID)
    effects = resolve_dice_modifier(d)
    assert effects == [
        MoveEffect(damage_type=DomainDamageType.FIRE, effect_value=4),
        MoveEffect(damage_type=DomainDamageType.ACID, effect_value=2),
    ]


# =====================
# RESOLVE_DICE_DRAIN
# =====================
def test_resolve_dice_drain_matches_1d4_wisdom_drain_example():
    """1d4 Wisdom drain -> average 2, halved to 1. Matches the shape of a
    real live-API sample already committed in entrypoints/output/."""
    d = Damage(dice_number=1, dice_type=DiceType.D4, affected_ability=Ability.WISDOM)
    effects = resolve_dice_drain(d)
    assert effects == [MoveEffect(
        damage_type=DomainDamageType.NEGATIVE_ENERGY,
        effect_unit=AffectedAttribute.WARD,
        effect_value=1,
    )]


# =====================
# RESOLVE_DRAIN_MODIFIER
# =====================
def test_resolve_drain_modifier_defaults_to_energy_drain():
    d = Damage(affected_ability=Ability.STRENGTH, damage_bonus=4)
    effects = resolve_drain_modifier(d)
    assert effects == [MoveEffect(
        damage_type=DomainDamageType.NEGATIVE_ENERGY,
        effect_unit=AffectedAttribute.ATTACK,
        effect_value=2,
    )]


def test_resolve_drain_modifier_uses_damage_type_not_damage_bonus_type():
    """Same regression as resolve_modifier(): reads damage_type, not the
    never-populated damage_bonus_type."""
    d = Damage(affected_ability=Ability.INTELLIGENCE, damage_bonus=2, damage_type=DamageType.FIRE)
    effects = resolve_drain_modifier(d)
    assert effects == [MoveEffect(
        damage_type=DomainDamageType.FIRE,
        effect_unit=AffectedAttribute.POWER,
        effect_value=1,
    )]


# =====================
# RESOLVE_DICE_DRAIN_MODIFIER
# =====================
def test_resolve_dice_drain_modifier_case1_both_energy_drain():
    """1d6 + 2 Dexterity damage: dice and modifier both default to
    ENERGY_DRAIN -> combined into a single effect."""
    d = Damage(dice_number=1, dice_type=DiceType.D6, affected_ability=Ability.DEXTERITY, damage_bonus=2)
    effects = resolve_dice_drain_modifier(d)
    assert effects == [MoveEffect(
        damage_type=DomainDamageType.NEGATIVE_ENERGY,
        effect_unit=AffectedAttribute.SPEED,
        effect_value=2,
    )]


def test_resolve_dice_drain_modifier_case2_drain_dice_plus_typed_modifier():
    """1d4 Constitution damage +3 fire damage: dice side resolves as
    drain, modifier side keeps its own (explicitly set) type."""
    d = Damage(dice_number=1, dice_type=DiceType.D4, affected_ability=Ability.CONSTITUTION,
               damage_bonus=3, damage_bonus_type=DamageType.FIRE)
    effects = resolve_dice_drain_modifier(d)
    assert effects == [
        MoveEffect(damage_type=DomainDamageType.NEGATIVE_ENERGY,
                        effect_unit=AffectedAttribute.DEFENSE, effect_value=1),
        MoveEffect(damage_type=DomainDamageType.FIRE, effect_value=3),
    ]


def test_resolve_dice_drain_modifier_case3_typed_dice_plus_drain_modifier():
    """1d8 acid damage +4 Wisdom damage: dice side keeps its own type,
    modifier side resolves as drain."""
    d = Damage(dice_number=1, dice_type=DiceType.D8, damage_type=DamageType.ACID,
               affected_ability=Ability.WISDOM, damage_bonus=4)
    effects = resolve_dice_drain_modifier(d)
    assert effects == [
        MoveEffect(damage_type=DomainDamageType.ACID, effect_value=4),
        MoveEffect(damage_type=DomainDamageType.NEGATIVE_ENERGY,
                        effect_unit=AffectedAttribute.WARD, effect_value=2),
    ]


def test_resolve_dice_drain_modifier_raises_when_neither_side_is_energy_drain():
    d = Damage(dice_number=1, dice_type=DiceType.D6, damage_type=DamageType.FIRE,
               affected_ability=Ability.STRENGTH, damage_bonus=2, damage_bonus_type=DamageType.ACID)
    with pytest.raises(InvalidDamageConfigurationError):
        resolve_dice_drain_modifier(d)


# =====================
# RESOLVE_DRAIN / RESOLVE_NO_VALUES
# =====================
def test_resolve_drain_rejects_drain_only_damage():
    """Ability damage requires dice or a numeric value -- a bare
    affected_ability with neither is not resolvable."""
    d = Damage(affected_ability=Ability.WISDOM)
    with pytest.raises(InvalidDamageConfigurationError):
        resolve_drain(d)


def test_resolve_no_values_returns_empty_list():
    assert resolve_no_values(Damage()) == []
