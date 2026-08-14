"""
Tests for D&D 3.x attack semantic classification.

Covers:
- _parse_attack_result(): valid/invalid LLM JSON responses
- _parse_effect_range(): valid/invalid move_range payloads
- _build_attack_prompt(): renders the real classify_attack.jinja2 template
- classify_attack(): end-to-end with the LLM client mocked, including a
  regression check that get_llm_client() is called with no arguments
  (it used to be called as get_llm_client(llm_model=LLM_MODEL), which
  raised TypeError since get_llm_client() takes no parameters)
"""
import json
from unittest.mock import patch
import pytest
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.llm.semantic_classification.attacks import (
    _parse_attack_result,
    _parse_effect_range,
    _build_attack_prompt,
    classify_attack,
    AttackSemanticResult,
    InvalidAttackSemanticResultError,
)
from monsterforge.structured_data.dnd.v3x.enums import MoveType, UnitSystem


VALID_RESPONSE = json.dumps({
    "description": "A sudden ray of electricity.",
    "move_type": "magical",
    "move_range": {"value": 30, "unit": "feet"},
    "confidence": 0.91,
    "rationale": "Ranged touch attack dealing electricity damage.",
})


# =====================
# _parse_attack_result
# =====================
def test_parse_attack_result_valid_response():
    result = _parse_attack_result(VALID_RESPONSE)

    assert result == AttackSemanticResult(
        description="A sudden ray of electricity.",
        move_type=MoveType.MAGICAL,
        move_range=_parse_effect_range({"value": 30, "unit": "feet"}),
        confidence=0.91,
        rationale="Ranged touch attack dealing electricity damage.",
    )


def test_parse_attack_result_rejects_invalid_json():
    with pytest.raises(InvalidAttackSemanticResultError):
        _parse_attack_result("not json")


def test_parse_attack_result_rejects_missing_field():
    data = json.loads(VALID_RESPONSE)
    del data["rationale"]

    with pytest.raises(InvalidAttackSemanticResultError):
        _parse_attack_result(json.dumps(data))


def test_parse_attack_result_rejects_extra_field():
    data = json.loads(VALID_RESPONSE)
    data["extra"] = "unexpected"

    with pytest.raises(InvalidAttackSemanticResultError):
        _parse_attack_result(json.dumps(data))


def test_parse_attack_result_rejects_invalid_move_type():
    data = json.loads(VALID_RESPONSE)
    data["move_type"] = "elemental"

    with pytest.raises(InvalidAttackSemanticResultError):
        _parse_attack_result(json.dumps(data))


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_parse_attack_result_rejects_confidence_out_of_range(confidence):
    data = json.loads(VALID_RESPONSE)
    data["confidence"] = confidence

    with pytest.raises(InvalidAttackSemanticResultError):
        _parse_attack_result(json.dumps(data))


def test_parse_attack_result_rejects_boolean_confidence():
    data = json.loads(VALID_RESPONSE)
    data["confidence"] = True

    with pytest.raises(InvalidAttackSemanticResultError):
        _parse_attack_result(json.dumps(data))


# =====================
# _parse_effect_range
# =====================
def test_parse_effect_range_none():
    assert _parse_effect_range(None) is None


def test_parse_effect_range_feet():
    result = _parse_effect_range({"value": 30, "unit": "feet"})

    assert result.effect_range == 30
    assert result.range_unit_system == UnitSystem.IMPERIAL


def test_parse_effect_range_meters():
    result = _parse_effect_range({"value": 10, "unit": "meters"})

    assert result.effect_range == 10
    assert result.range_unit_system == UnitSystem.METRIC


def test_parse_effect_range_rejects_unknown_unit():
    with pytest.raises(InvalidAttackSemanticResultError):
        _parse_effect_range({"value": 10, "unit": "cubits"})


def test_parse_effect_range_rejects_missing_keys():
    with pytest.raises(InvalidAttackSemanticResultError):
        _parse_effect_range({"value": 10})


def test_parse_effect_range_rejects_negative_value():
    with pytest.raises(InvalidAttackSemanticResultError):
        _parse_effect_range({"value": -5, "unit": "feet"})


# =====================
# _build_attack_prompt
# =====================
def test_build_attack_prompt_renders_the_real_template():
    context = {
        "raw_attack": RawAttack(
            name="Bite", modifier="+7", attack_type="melee", attack_effect="1d6+3 plus trip"
        ),
        "additional_description": None,
        "creature_description": None,
        "creature_subtype": None,
    }

    prompt = _build_attack_prompt(context)

    assert "Bite" in prompt
    assert "1d6+3 plus trip" in prompt
    assert "Return ONLY a valid JSON object" in prompt


# =====================
# classify_attack
# =====================
def test_classify_attack_calls_get_llm_client_with_no_arguments():
    """Regression: get_llm_client() takes no parameters. This used to be
    called as get_llm_client(llm_model=LLM_MODEL), raising TypeError.
    autospec enforces the real signature, so a reintroduced kwarg would
    fail this test even though the client itself is mocked."""
    raw_attack = RawAttack(
        name="Bite", modifier="+7", attack_type="melee", attack_effect="1d6+3 plus trip"
    )

    with patch(
        "monsterforge.llm.semantic_classification.attacks.get_llm_client",
        autospec=True,
    ) as mock_get_llm_client:
        mock_get_llm_client.return_value.generate_text.return_value = VALID_RESPONSE

        result = classify_attack(raw_attack=raw_attack)

    mock_get_llm_client.assert_called_once_with()
    assert result.move_type == MoveType.MAGICAL
    assert result.confidence == 0.91
