"""
Tests for Stamina and Mana calculation.
"""
from monsterforge.transformation.dnd.v3x.calculations.resources import (
    calculate_stamina, calculate_mana,
)


# =====================
# STAMINA
# =====================
def test_stamina_scales_with_base_attack_bonus():
    assert calculate_stamina(25) == 4
    assert calculate_stamina(10) == 2


def test_stamina_minimum_is_one_even_at_zero_bab():
    assert calculate_stamina(0) == 1


def test_stamina_is_capped_at_four():
    """The max attacks-per-turn cap (4) preserves gameplay speed even
    for very high Base Attack Bonus values."""
    assert calculate_stamina(40) == 4


# =====================
# MANA
# =====================
def test_mana_is_zero_without_any_magic_progression():
    assert calculate_mana(caster_level=None, manifester_level=None) == 0


def test_mana_minimum_is_one_for_any_caster_level():
    assert calculate_mana(caster_level=1, manifester_level=None) == 1


def test_mana_uses_the_higher_of_caster_or_manifester_level():
    result = calculate_mana(caster_level=5, manifester_level=15)
    assert result == 3  # 15 // 5


def test_mana_is_capped_at_four():
    assert calculate_mana(caster_level=25, manifester_level=None) == 4
    