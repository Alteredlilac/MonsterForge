"""
Tests for domain-specific rule applications: drained ability, damage,
healing normalization, and progression-based per-level values.
"""
import pytest
from monsterforge.transformation.dnd.v3x.calculations.general_rules import (
    normalize_drained_ability, normalize_damage, normalize_healing,
    calculate_known_spells_per_level, calculate_combat_abilities_per_level,
)
from monsterforge.structured_data.dnd.v3x.enums import DiceType, ProgressionRate


def test_normalize_drained_ability_halves_the_average():
    """D6 -> average 3 -> halved -> 1 (floor)."""
    assert normalize_drained_ability(dice_type=DiceType.D6) == 1


def test_normalize_drained_ability_never_below_one():
    assert normalize_drained_ability(dice_type=DiceType.D4) >= 1


def test_normalize_damage_does_not_halve():
    """Unlike drained abilities, damage uses the full average value."""
    assert normalize_damage(dice_type=DiceType.D6) == 3


def test_normalize_damage_scales_with_dice_count():
    """2d8 breath-weapon-style damage: 2 * 4 = 8."""
    assert normalize_damage(dice_type=DiceType.D8, num_dice=2) == 8


def test_normalize_healing_with_dice_type():
    assert normalize_healing(healing_value=DiceType.D6) == 3


def test_normalize_healing_with_multiple_dice():
    assert normalize_healing(healing_value=DiceType.D8, num_dice=2) == 8


def test_normalize_healing_with_absolute_value_is_halved():
    """Absolute healing amounts (not dice expressions) are halved,
    e.g. a fixed '5 HP' heal becomes 2."""
    assert normalize_healing(healing_value=5) == 2


def test_normalize_healing_absolute_value_ignores_num_dice():
    """num_dice has no effect when healing_value is a plain int."""
    assert normalize_healing(healing_value=5, num_dice=3) == normalize_healing(healing_value=5)


def test_normalize_healing_rejects_invalid_type():
    with pytest.raises(TypeError):
        normalize_healing(healing_value="5")


def test_spells_per_level_progression_rates_are_ordered():
    low = calculate_known_spells_per_level(ProgressionRate.LOW)
    medium = calculate_known_spells_per_level(ProgressionRate.MEDIUM)
    high = calculate_known_spells_per_level(ProgressionRate.HIGH)
    assert low <= medium <= high


def test_combat_abilities_per_level_progression_rates_are_ordered():
    low = calculate_combat_abilities_per_level(ProgressionRate.LOW)
    high = calculate_combat_abilities_per_level(ProgressionRate.HIGH)
    assert low <= high
    