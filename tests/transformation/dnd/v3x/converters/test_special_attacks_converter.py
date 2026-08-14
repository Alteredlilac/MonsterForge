"""
Tests for special_attack_converter().

Covers:
- shallow-card construction (regression: this was an empty stub
  returning None, breaking cards_to_add for any attack with effects)
- SpecialAbilityType -> domain MoveType mapping
- a stable default id is present (not deterministic in MVP zero)
"""
from monsterforge.structured_data.dnd.v3x.special_attacks import SpecialAttack
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectTarget
from monsterforge.structured_data.dnd.v3x.enums import SpecialAbilityType, TargetType
from monsterforge.transformation.dnd.v3x.converters.special_attacks_converter import (
    special_attack_converter,
)
from monsterforge.domain.enums import MoveType, MoveCategory, MoveMode, EffectType, Resource


def make_special_attack(**overrides):
    defaults = dict(
        name="trip",
        special_ability_type=SpecialAbilityType.EXTRAORDINARY,
        target=EffectTarget(target_type=TargetType.SOMETHING),
    )
    defaults.update(overrides)
    return SpecialAttack(**defaults)


def test_special_attack_converter_produces_a_move_card():
    special_attack = make_special_attack()

    card = special_attack_converter(special_attack)

    assert card.name == "Trip"
    assert card.description
    assert card.id is not None
    assert card.category == MoveCategory.ATTACK
    assert card.mode == MoveMode.ACTIVE
    assert card.effect == EffectType.ENTITY
    assert card.resource == Resource.NONE


def test_special_attack_converter_uses_provided_description_when_present():
    special_attack = make_special_attack(description="Knocks the target prone.")

    card = special_attack_converter(special_attack)

    assert card.description == "Knocks the target prone."


def test_special_attack_converter_generates_a_fallback_description():
    special_attack = make_special_attack(name="push", description=None)

    card = special_attack_converter(special_attack)

    assert "push" in card.description


def test_special_attack_converter_maps_extraordinary_to_physical():
    special_attack = make_special_attack(special_ability_type=SpecialAbilityType.EXTRAORDINARY)

    card = special_attack_converter(special_attack)

    assert card.move_type == MoveType.PHYSICAL


def test_special_attack_converter_maps_supernatural_to_magical():
    special_attack = make_special_attack(special_ability_type=SpecialAbilityType.SUPERNATURAL)

    card = special_attack_converter(special_attack)

    assert card.move_type == MoveType.MAGICAL


def test_special_attack_converter_maps_spell_like_to_magical():
    special_attack = make_special_attack(special_ability_type=SpecialAbilityType.SPELL_LIKE)

    card = special_attack_converter(special_attack)

    assert card.move_type == MoveType.MAGICAL


def test_special_attack_converter_each_call_gets_its_own_id():
    """MVP zero has no deterministic identity yet — every conversion of
    "the same" special attack currently gets a fresh random id. This is
    expected to change once fingerprint-based ids are introduced."""
    first = special_attack_converter(make_special_attack())
    second = special_attack_converter(make_special_attack())

    assert first.id != second.id
