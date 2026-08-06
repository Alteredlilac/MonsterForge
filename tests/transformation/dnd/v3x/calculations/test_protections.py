"""
Tests for Armor and Talisman calculation.

The Wolf example (AC 14, Dex +2 -> Armor 2) is the canonical case from
design.md.
"""
from monsterforge.transformation.dnd.v3x.calculations.protections import (
    calculate_creature_armor, calculate_creature_talisman,
)


# =====================
# ARMOR
# =====================
def test_wolf_armor_matches_design_doc_example():
    result = calculate_creature_armor(
        armor_class=14, size_modifier=0, dexterity_modifier=2, deflection_bonus=0,
    )
    assert result == 2


def test_armor_ignores_size_and_deflection_bonuses():
    """Size and deflection contributions are excluded from the final
    MonsterForge Armor value, even though they're subtracted during
    calculation to isolate the natural/armor component."""
    with_size = calculate_creature_armor(
        armor_class=18, size_modifier=-2, dexterity_modifier=2, deflection_bonus=0,
    )
    assert with_size == 8


# =====================
# TALISMAN
# =====================
def test_talisman_uses_the_higher_resistance_value():
    result = calculate_creature_talisman(
        spell_resistance=15, power_resistance=10, deflection_bonus=0,
    )
    assert result == 5  # 15 - 10 = 5, spell resistance wins


def test_talisman_below_threshold_keeps_only_deflection():
    """When resistance doesn't exceed 10, only the deflection bonus
    is kept, per the design.md example (SR 0, deflection +1 -> 1)."""
    result = calculate_creature_talisman(
        spell_resistance=0, power_resistance=0, deflection_bonus=1,
    )
    assert result == 1


def test_talisman_adds_deflection_when_resistance_exceeds_threshold():
    result = calculate_creature_talisman(
        spell_resistance=15, power_resistance=0, deflection_bonus=2,
    )
    assert result == 7  # (15 - 10) + 2
    