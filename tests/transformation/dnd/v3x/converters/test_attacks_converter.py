"""
Tests for attack_converter(): structured_data.Attack -> domain.MoveCard.

Covers:
- the Wolf/Bite worked example from README.md ("Bite 1d6" -> "Deal 3
  damage to a single target", Stamina cost)
- the full "bite plus trip" reference scenario end to end, exercising
  cards_to_add via special_attack_converter (regression: this used to
  contain [None] because special_attack_converter was an empty stub)
"""
from monsterforge.structured_data.dnd.v3x.attacks import Attack
from monsterforge.structured_data.dnd.v3x.dice_effects import Damage
from monsterforge.structured_data.dnd.v3x.special_attacks import SpecialAttack
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectTarget
from monsterforge.structured_data.dnd.v3x.enums import (
    DiceType, DamageType as StructDamageType, SpecialAbilityType, TargetType,
)
from monsterforge.structured_data.dnd.v3x.enums import MoveType as StructMoveType
from monsterforge.transformation.dnd.v3x.converters.attacks_converter import attack_converter
from monsterforge.domain.enums import MoveCategory, MoveMode, EffectType, Resource, EntityEffect


def test_bite_matches_the_readme_worked_example():
    """README.md: Bite 1d6 -> "Deal 3 damage to a single target", Stamina
    cost. 1d6 averages to 3 per DESIGN.md's damage rule."""
    bite = Attack(
        move_type=StructMoveType.PHYSICAL,
        name="Bite",
        description="A sharp bite.",
        damages=[Damage(dice_number=1, dice_type=DiceType.D6, damage_type=StructDamageType.PHYSICAL)],
    )

    card = attack_converter(bite)

    assert card.name == "Bite"
    assert card.category == MoveCategory.ATTACK
    assert card.mode == MoveMode.ACTIVE
    assert card.effect == EffectType.DAMAGE
    assert card.resource == Resource.STAMINA
    assert len(card.move_effects) == 1
    assert card.move_effects[0].effect_value == 3
    assert card.cards_to_add == []


def test_bite_plus_trip_reference_scenario_end_to_end():
    """The reference scenario used throughout MVP zero planning: a bite
    attack granting a Trip maneuver must produce a MoveCard whose
    cards_to_add contains a real, usable Trip MoveCard — not [None]."""
    trip = SpecialAttack(
        name="trip",
        special_ability_type=SpecialAbilityType.EXTRAORDINARY,
        target=EffectTarget(target_type=TargetType.SOMETHING),
    )
    bite = Attack(
        move_type=StructMoveType.PHYSICAL,
        name="Bite",
        description="A vicious bite that can knock the target down.",
        damages=[Damage(dice_number=1, dice_type=DiceType.D6, damage_type=StructDamageType.PHYSICAL, damage_bonus=3)],
        effects=[trip],
    )

    card = attack_converter(bite)

    assert card.entity_effect == [EntityEffect.MOVES]
    assert len(card.cards_to_add) == 1
    trip_card = card.cards_to_add[0]
    assert trip_card is not None
    assert trip_card.name == "Trip"
    assert trip_card.category == MoveCategory.ATTACK
