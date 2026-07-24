"""
Tests for raw attack field models.

Covers:
- Attack creation
- FullAttack composition
- Atomic attack assumption
"""

from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack, FullAttack


def test_attack_creation():
    attack = Attack(
        name="Bite",
        modifier="+5",
        attack_type="melee",
        attack_effect="1d6+3"
    )

    assert attack.name == "Bite"


def test_full_attack_contains_multiple_attacks():
    bite = Attack(
        name="Bite",
        modifier="+5",
        attack_type="melee",
        attack_effect="1d6+3"
    )

    claw = Attack(
        name="Claw",
        modifier="+3",
        attack_type="melee",
        attack_effect="1d4+1"
    )

    full_attack = FullAttack(attacks=[bite, claw])

    assert len(full_attack.attacks) == 2


def test_attack_is_atomic_entry():
    # Raw attacks are expected to already be split into atomic entries
    # (e.g. "claw +8 and bite +3" → two Attack instances).
    attack = Attack(
        name="Bite",
        modifier="+5",
        attack_type="melee",
        attack_effect="1d6+3"
    )

    assert " and " not in attack.name.lower()