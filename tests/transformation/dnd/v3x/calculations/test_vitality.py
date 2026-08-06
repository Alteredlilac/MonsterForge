"""
Tests for vitality calculation.

The Wolf example (Medium, 2d8 -> 23 HP) is the reference case used
throughout design.md and is treated as the canonical regression test.
"""
from monsterforge.transformation.dnd.v3x.calculations.vitality import calculate_life_value
from monsterforge.structured_data.dnd.v3x.enums import Size, DiceType


def test_wolf_vitality_matches_design_doc_example():
    """Medium creature, 2d8 hit dice -> 15 (Medium base) + 2*4 (D8 avg) = 23."""
    result = calculate_life_value(
        creature_size=Size.MEDIUM, hit_dice_type=DiceType.D8, num_hit_dice=2,
    )
    assert result == 23


def test_vitality_scales_with_hit_dice_count():
    single = calculate_life_value(
        creature_size=Size.MEDIUM,
        hit_dice_type=DiceType.D8,
        num_hit_dice=1)
    double = calculate_life_value(
        creature_size=Size.MEDIUM,
        hit_dice_type=DiceType.D8,
        num_hit_dice=2)
    assert double == single + 4  # one extra D8 die = +4 average


def test_vitality_defaults_to_one_hit_die():
    result = calculate_life_value(creature_size=Size.SMALL, hit_dice_type=DiceType.D6)
    assert result == 10 + 3  # SMALL base (10) + 1 D6 average (3)


def test_vitality_increases_with_size():
    small = calculate_life_value(
        creature_size=Size.SMALL,
        hit_dice_type=DiceType.D8,
        num_hit_dice=1)
    large = calculate_life_value(
        creature_size=Size.LARGE,
        hit_dice_type=DiceType.D8,
        num_hit_dice=1)
    assert large > small
    