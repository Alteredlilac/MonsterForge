"""
Tests for _llm_response_capture.classify_with_raw_response().

Covers:
- the raw LLM response is captured alongside the parsed result
- GeminiClient.generate_text() is restored to its original, unwrapped
  form afterwards, including when classify_attack() raises
"""
import json
from unittest.mock import MagicMock
import pytest
import monsterforge.llm.client as llm_client_module
from monsterforge.entrypoints._llm_response_capture import classify_with_raw_response
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.llm.semantic_classification.attacks import (
    InvalidAttackSemanticResultError,
)


VALID_RESPONSE = json.dumps({
    "description": "A vicious bite.",
    "move_type": "physical",
    "move_range": None,
    "confidence": 0.9,
    "rationale": "Natural melee attack.",
})


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.generate_text.return_value = VALID_RESPONSE
    llm_client_module._client = client
    yield client
    llm_client_module._client = None


def test_captures_the_raw_response_alongside_the_parsed_result(mock_client):
    raw_attack = RawAttack(
        name="Bite", modifier="+7", attack_type="melee", attack_effect="1d6+3"
    )

    result, raw_response = classify_with_raw_response(raw_attack)

    assert raw_response == VALID_RESPONSE
    assert result.description == "A vicious bite."


def test_restores_generate_text_after_a_successful_call(mock_client):
    original = mock_client.generate_text
    raw_attack = RawAttack(
        name="Bite", modifier="+7", attack_type="melee", attack_effect="1d6+3"
    )

    classify_with_raw_response(raw_attack)

    assert mock_client.generate_text is original


def test_restores_generate_text_even_when_classification_fails(mock_client):
    mock_client.generate_text.return_value = "not valid json"
    original = mock_client.generate_text
    raw_attack = RawAttack(
        name="Bite", modifier="+7", attack_type="melee", attack_effect="1d6+3"
    )

    with pytest.raises(InvalidAttackSemanticResultError):
        classify_with_raw_response(raw_attack)

    assert mock_client.generate_text is original
