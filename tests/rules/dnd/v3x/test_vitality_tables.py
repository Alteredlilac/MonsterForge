"""
Tests for vitality_tables.py.

These tests verify the integrity of the static vitality conversion rules
used by the D&D 3.x transformation pipeline.

The module only defines immutable data mappings and does not contain
calculation logic. Tests therefore focus on:
- completeness of Size and DiceType mappings
- consistency of ordered vitality values
- immutability of rule tables
"""
import pytest
from monsterforge.rules.dnd.v3x.vitality_tables import SIZE_HP_TABLE, DICE_AVERAGE_HP
from monsterforge.structured_data.dnd.v3x.enums import Size, DiceType



def test_size_hp_table_has_all_sizes():
    """Every Size enum member must have a corresponding HP entry.
    Missing entries would cause lookup failures during vitality
    calculation.
    """
    for size in Size:
        assert size in SIZE_HP_TABLE


def test_size_hp_table_values_increase_with_size():
    """Sanity check: bigger creatures should never have less base HP
    than smaller ones."""
    ordered_sizes = [
        Size.FINE, Size.DIMINUTIVE, Size.TINY, Size.SMALL, Size.MEDIUM,
        Size.LARGE, Size.HUGE, Size.GARGANTUAN, Size.COLOSSAL,
    ]
    values = [SIZE_HP_TABLE[s] for s in ordered_sizes]
    assert values == sorted(values)


def test_dice_average_hp_has_all_valid_hit_die_types():
    """Every hit die type listed in DESIGN.md's LIFE table must have an
    entry. DiceType.D3 is deliberately excluded: it's a valid DiceType
    (used for generic damage dice), but not a valid creature hit die per
    DESIGN.md.
    """
    valid_hit_die_types = [
        DiceType.D2, DiceType.D4, DiceType.D6,
        DiceType.D8, DiceType.D10, DiceType.D12,
    ]
    for dice_type in valid_hit_die_types:
        assert dice_type in DICE_AVERAGE_HP


def test_dice_average_hp_values_are_positive():
    assert all(v > 0 for v in DICE_AVERAGE_HP.values())

def test_dice_average_hp_values_are_ordered():
    """Higher hit dice should have higher average HP values."""
    ordered_dice = [
        DiceType.D2,
        DiceType.D4,
        DiceType.D6,
        DiceType.D8,
        DiceType.D10,
        DiceType.D12,
    ]

    values = [DICE_AVERAGE_HP[d] for d in ordered_dice]

    assert values == sorted(values)


@pytest.mark.parametrize(
    "table",
    [
        SIZE_HP_TABLE,
        DICE_AVERAGE_HP,
    ],
)
def test_tables_are_immutable(table):
    """Rule tables should not be mutable at runtime."""

    key = next(iter(table))

    with pytest.raises(TypeError):
        table[key] = 999
        