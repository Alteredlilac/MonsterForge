"""
Tests for passive defensive trait representations: DamageReduction,
DamageResistance, Regeneration.
"""
from monsterforge.structured_data.dnd.v3x.enums import DamageType


def test_damage_reduction_bypass_type_is_optional(make_damage_reduction):
    dr = make_damage_reduction(bypass_type=None)
    assert dr.bypass_type is None


def test_damage_reduction_with_bypass(make_damage_reduction):
    dr = make_damage_reduction(reduction_value=10, bypass_type="silver")
    assert dr.reduction_value == 10
    assert dr.bypass_type == "silver"


def test_damage_resistance_creation(make_damage_resistance):
    resistance = make_damage_resistance(
        damage_type=DamageType.COLD, resistance_value=20,
    )
    assert resistance.damage_type == DamageType.COLD
    assert resistance.resistance_value == 20


def test_regeneration_bypass_types_default_to_empty(make_regeneration):
    regen = make_regeneration()
    assert regen.bypass_damage_types == []


def test_regeneration_with_bypass_types(make_regeneration):
    regen = make_regeneration(
        regeneration_value=5,
        bypass_damage_types=[DamageType.FIRE, DamageType.ACID],
    )
    assert regen.regeneration_value == 5
    assert DamageType.FIRE in regen.bypass_damage_types
