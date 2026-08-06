"""
Tests for general deterministic math utilities: floor_value, halve_value,
convert_dice_to_value.
"""
from monsterforge.transformation.dnd.v3x.calculations.general_math import (
    floor_value, halve_value, convert_dice_to_value,
)
from monsterforge.structured_data.dnd.v3x.enums import DiceType


def test_floor_value_rounds_down():
    assert floor_value(4.9) == 4
    assert floor_value(2.1) == 2


def test_halve_value_minimum_is_one():
    assert halve_value(1) == 1
    assert halve_value(0) == 1


def test_halve_value_rounds_down():
    assert halve_value(5) == 2
    assert halve_value(4) == 2


def test_halve_value_treats_negative_as_magnitude():
    """Negative inputs are treated as positive magnitudes, not clamped
    to the minimum — halve_value(-5) behaves like halve_value(5)."""
    assert halve_value(-5) == 2


def test_convert_dice_to_value_returns_single_die_average():
    assert convert_dice_to_value(DiceType.D6) == 3
    assert convert_dice_to_value(DiceType.D8) == 4
    assert convert_dice_to_value(DiceType.D12) == 6
