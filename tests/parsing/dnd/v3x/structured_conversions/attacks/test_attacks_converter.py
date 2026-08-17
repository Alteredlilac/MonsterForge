"""
Tests for raw_to_structured_attack() and its deterministic helpers.

Covers:
- raw_to_structured_attack() is a pure function: semantic classification
  is passed in as a parameter, not performed internally (regression:
  it used to call classify_attack() positionally against a keyword-only
  signature, raising TypeError for every attack)
- melee/ranged/touch detection and known-attack range fallback
- the "bite plus trip" reference scenario end to end for this stage
"""
import pytest
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import (
    raw_to_structured_attack,
    UnknownAttackRange,
)
from monsterforge.llm.semantic_classification.attacks import AttackSemanticResult
from monsterforge.structured_data.dnd.v3x.enums import MoveType, UnitSystem
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.entrypoints.sample_attacks import SAMPLE_ATTACKS


def make_semantic_result(**overrides):
    defaults = dict(
        description="A vicious attack.",
        move_type=MoveType.PHYSICAL,
        move_range=None,
        confidence=0.95,
        rationale="Deterministic test fixture.",
    )
    defaults.update(overrides)
    return AttackSemanticResult(**defaults)


def test_raw_to_structured_attack_does_not_call_the_llm():
    """The function is pure: no classify_attack() call, no network I/O —
    constructing an AttackSemanticResult by hand is enough."""
    raw_attack = RawAttack(
        name="Bite", modifier="+7", attack_type="melee", attack_effect="1d6+3 plus trip"
    )
    semantic_result = make_semantic_result(description="A sharp bite.")

    structured = raw_to_structured_attack(raw_attack, semantic_result)

    assert structured.name == "Bite"
    assert structured.description == "A sharp bite."
    assert structured.move_type == MoveType.PHYSICAL
    assert structured.melee is True
    assert structured.attack_bonus == 7


def test_raw_to_structured_attack_bite_plus_trip_reference_scenario():
    raw_attack = RawAttack(
        name="Bite", modifier="+7", attack_type="melee", attack_effect="1d6+3 plus trip"
    )
    semantic_result = make_semantic_result()

    structured = raw_to_structured_attack(raw_attack, semantic_result)

    assert len(structured.damages) == 1
    assert structured.damages[0].damage_bonus == 3
    assert [e.name for e in structured.effects] == ["trip"]
    assert structured.attack_range is None  # melee


def test_raw_to_structured_attack_ranged_uses_semantic_range_first():
    raw_attack = RawAttack(
        name="Light ray", modifier="+2", attack_type="ranged touch", attack_effect="1d6"
    )
    semantic_range = EffectRange(effect_range=30, range_unit_system=UnitSystem.IMPERIAL)
    semantic_result = make_semantic_result(move_type=MoveType.MAGICAL, move_range=semantic_range)

    structured = raw_to_structured_attack(raw_attack, semantic_result)

    assert structured.attack_range is semantic_range
    assert structured.touch is True


def test_raw_to_structured_attack_ranged_falls_back_to_known_attacks():
    raw_attack = RawAttack(
        name="Shortbow", modifier="+8", attack_type="ranged", attack_effect="1d6"
    )
    semantic_result = make_semantic_result(move_range=None)

    structured = raw_to_structured_attack(raw_attack, semantic_result)

    assert structured.attack_range.effect_range == 20


def test_raw_to_structured_attack_ranged_without_known_range_raises():
    raw_attack = RawAttack(
        name="Mystery weapon", modifier="+8", attack_type="ranged", attack_effect="1d6"
    )
    semantic_result = make_semantic_result(move_range=None)

    with pytest.raises(UnknownAttackRange):
        raw_to_structured_attack(raw_attack, semantic_result)


@pytest.mark.parametrize("case", [c for c in SAMPLE_ATTACKS if c["name"]])
def test_raw_to_structured_attack_handles_all_sample_attacks(case):
    """Structural smoke test: every non-empty SAMPLE_ATTACKS case must
    convert without raising, given a plausible semantic result. A
    move_range is always supplied: melee attacks ignore it (see
    get_known_attack_range), so this avoids depending on KNOWN_ATTACKS
    or replicating is_melee()'s own text-matching logic here, and covers
    edge cases like "Swarm" (empty attack_type, neither melee nor a
    KNOWN_ATTACKS entry)."""
    raw_attack = RawAttack(**case)
    semantic_result = make_semantic_result(
        move_range=EffectRange(effect_range=10, range_unit_system=UnitSystem.METRIC)
    )

    structured = raw_to_structured_attack(raw_attack, semantic_result)

    assert structured.name == case["name"]
