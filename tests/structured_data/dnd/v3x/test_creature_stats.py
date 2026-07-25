"""
Tests for creature stat building blocks: HitDice, Movement, ArmorClass,
Space, Reach, Abilities, Saves.

These are pure data containers with no logic, so tests only confirm
correct instantiation and default behavior.
"""
from monsterforge.structured_data.dnd.v3x.enums import (
    DiceType, UnitSystem, MovementMode, FlyManeuverability,
)
from monsterforge.structured_data.dnd.v3x.creature_stats import (
    HitDice, Movement, ArmorClass,
)


def test_hit_dice_creation(make_hit_dice):
    hd = make_hit_dice(num_hit_dice=2, hit_dice_type=DiceType.D8)
    assert hd.num_hit_dice == 2
    assert hd.hit_dice_type == DiceType.D8


def test_movement_maneuverability_defaults_to_none(make_movement):
    move = make_movement()
    assert move.maneuverability is None


def test_movement_with_flight():
    move = Movement(
        movement_speed=18, unit_system=UnitSystem.METRIC,
        movement_type=MovementMode.FLY,
        maneuverability=FlyManeuverability.GOOD,
    )
    assert move.movement_type == MovementMode.FLY
    assert move.maneuverability == FlyManeuverability.GOOD


def test_armor_class_bonus_fields_default_to_zero():
    ac = ArmorClass(armor_class=14, flat_footed_ac=12, touch_ac=12)
    assert ac.size_modifier == 0
    assert ac.dexterity_modifier == 0
    assert ac.miscellaneous_bonus == {}


def test_armor_class_with_full_breakdown(make_armor_class):
    ac = make_armor_class(
        armor_class=18, dexterity_modifier=2, natural_armor_bonus=2,
    )
    assert ac.armor_class == 18
    assert ac.dexterity_modifier == 2
    assert ac.natural_armor_bonus == 2


def test_space_and_reach_creation(make_space, make_reach):
    space = make_space(space=1)
    reach = make_reach(reach=1)
    assert space.space == 1
    assert reach.reach == 1


def test_abilities_allows_undefined_scores(make_abilities):
    """Constitution/Intelligence may be None for undead/constructs/mindless creatures."""
    skeleton_abilities = make_abilities(constitution=None, intelligence=None)
    assert skeleton_abilities.constitution is None
    assert skeleton_abilities.intelligence is None
    assert skeleton_abilities.strength == 13


def test_saves_creation(make_saves):
    saves = make_saves(fortitude_save=5, reflex_save=2, will_save=1)
    assert saves.fortitude_save == 5
    assert saves.reflex_save == 2
    assert saves.will_save == 1
