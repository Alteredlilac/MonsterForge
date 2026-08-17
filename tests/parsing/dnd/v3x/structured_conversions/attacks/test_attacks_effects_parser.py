"""
Tests for D&D 3.x attack-effect parsing.

Covers:
- get_special_attacks() constructs valid SpecialAttack objects
  (regression: SpecialAttack.target used to be omitted, which raised
  TypeError for any attack with a bare-word secondary effect)
- the general rule that a component with no dice/bonus of its own is
  always a special attack, even when it names a recognized DamageType
- get_attack_effects() against the hand-validated golden fixture in
  expected_attack_effects.py, covering all of SAMPLE_ATTACKS
"""
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_effects_parser import (
    get_special_attacks,
    get_attack_effects,
)
from monsterforge.structured_data.dnd.v3x.enums import TargetType
from monsterforge.entrypoints.sample_attacks import SAMPLE_ATTACKS
from tests.tools.generate_expected_outputs import to_plain
from .expected_attack_effects import EXPECTED_ATTACK_EFFECTS


def test_get_special_attacks_sets_a_target():
    raw_attack = RawAttack(
        name="Bite",
        modifier="+7",
        attack_type="melee",
        attack_effect="1d6+3 plus trip",
    )

    special_attacks = get_special_attacks(raw_attack)

    assert len(special_attacks) == 1
    assert special_attacks[0].name == "trip"
    assert special_attacks[0].target.target_type == TargetType.SOMETHING


def test_get_special_attacks_handles_bare_effect_with_no_dice():
    raw_attack = RawAttack(
        name="Tongue",
        modifier="+12",
        attack_type="melee touch",
        attack_effect="paralysis",
    )

    special_attacks = get_special_attacks(raw_attack)

    assert len(special_attacks) == 1
    assert special_attacks[0].name == "paralysis"
    assert special_attacks[0].target.target_type == TargetType.SOMETHING


def test_get_special_attacks_returns_empty_list_when_no_secondary_effect():
    raw_attack = RawAttack(
        name="Claw",
        modifier="+9",
        attack_type="melee",
        attack_effect="2d6+4",
    )

    assert get_special_attacks(raw_attack) == []


def test_bare_recognized_damage_type_with_no_dice_is_a_special_attack():
    """A component naming a recognized DamageType (e.g. "positive
    energy") is still a special attack, not a Damage, when it carries no
    dice/bonus of its own — matching the treatment of unrecognized bare
    words like "rust"/"paralysis". Ravid's tail touch (positive energy,
    no dice) is a special ability, not quantifiable per-hit damage."""
    raw_attack = RawAttack(
        name="Tail touch",
        modifier="+4",
        attack_type="melee touch",
        attack_effect="positive energy",
    )

    effects = get_attack_effects(raw_attack)

    assert effects.damages == []
    assert [s.name for s in effects.special_attacks] == ["positive energy"]


def test_recognized_damage_type_after_plus_with_no_dice_is_also_a_special_attack():
    """Same rule applied to a component after "plus": "energy drain" has
    no dice/bonus of its own, so it becomes a special attack alongside
    the physical damage from the first component, not a silently
    absorbed qualifier."""
    raw_attack = RawAttack(
        name="Incorporeal touch",
        modifier="+6",
        attack_type="melee",
        attack_effect="1d8 plus energy drain",
    )

    effects = get_attack_effects(raw_attack)

    assert len(effects.damages) == 1
    assert [s.name for s in effects.special_attacks] == ["energy drain"]


def test_get_attack_effects_matches_the_validated_golden_fixture():
    """Regression test anchored to expected_attack_effects.py: the
    parser's actual output over SAMPLE_ATTACKS, generated once by
    generate_expected_attack_effects.py and hand-reviewed, then
    committed as a golden fixture. A future parser change that no
    longer matches this file fails here."""
    for case, expected in zip(SAMPLE_ATTACKS, EXPECTED_ATTACK_EFFECTS):
        raw_attack = RawAttack(**case)
        actual = to_plain(get_attack_effects(raw_attack))
        assert actual == expected, f"Mismatch for case: {case}"
