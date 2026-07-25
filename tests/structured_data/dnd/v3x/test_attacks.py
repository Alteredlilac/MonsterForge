"""
Tests for the Attack and FullAttack models.
"""
from monsterforge.structured_data.dnd.v3x.attacks import Attack, FullAttack


def test_attack_minimal_creation():
    bite = Attack(name="Bite")
    assert bite.name == "Bite"
    assert bite.melee is True
    assert bite.touch is False
    assert bite.damages == []


def test_attack_with_damage_and_range(make_damage, make_effect_range):
    shortbow = Attack(
        name="Shortbow", melee=False,
        attack_range=make_effect_range(effect_range=18),
        damages=[make_damage()],
    )
    assert shortbow.melee is False
    assert shortbow.attack_range.effect_range == 18
    assert len(shortbow.damages) == 1


def test_attack_with_critical_hit(make_critical_hit):
    claw = Attack(name="Claw", critical_hit=make_critical_hit(critical_threat_min=19))
    assert claw.critical_hit.critical_threat_min == 19


def test_attack_effects_default_to_empty_list():
    bite = Attack(name="Bite")
    assert bite.effects == []


def test_full_attack_aggregates_multiple_attacks():
    claw = Attack(name="Claw")
    bite = Attack(name="Bite")
    full = FullAttack(attacks=[claw, bite])
    assert len(full.attacks) == 2
    assert full.attacks[0].name == "Claw"


def test_full_attack_defaults_to_empty_list():
    full = FullAttack()
    assert full.attacks == []
