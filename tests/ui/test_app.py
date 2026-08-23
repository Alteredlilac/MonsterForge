"""
Tests for the MVP 1 FastAPI web app (ui/app.py).

Covers the four possible outcomes of the review gate (auto-approved,
approved, corrected, rejected), the blank-attack short-circuit, and a
ModelUnavailableError response. classify_attack is always mocked: no
real API calls in tests.
"""
import re
from unittest.mock import patch
from fastapi.testclient import TestClient
from monsterforge.llm.clients.gemini import ModelUnavailableError
from monsterforge.llm.semantic_classification.attacks import AttackSemanticResult
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import MoveType, UnitSystem
from monsterforge.ui.app import app

client = TestClient(app)

RAW_ATTACK_FORM = {"name": "Bite", "modifier": "+5", "attack_type": "melee", "attack_effect": "1d6+3"}


def make_semantic_result(**overrides):
    defaults = dict(
        description="A vicious bite.",
        move_type=MoveType.PHYSICAL,
        move_range=None,
        confidence=0.4,
        rationale="test rationale",
    )
    defaults.update(overrides)
    return AttackSemanticResult(**defaults)


def _extract_semantic_result_json(html: str) -> str:
    match = re.search(r"name=\"semantic_result_json\" value='(.*?)'", html)
    assert match is not None, "review form did not include the expected hidden field"
    return match.group(1)


# =====================
# GET /convert
# =====================
def test_show_convert_form_lists_creature_subtypes():
    response = client.get("/convert")

    assert response.status_code == 200
    assert "incorporeal" in response.text


# =====================
# POST /convert
# =====================
def test_convert_blank_attack_produces_no_card_and_skips_classification():
    with patch("monsterforge.ui.app.classify_attack") as mock_classify:
        response = client.post("/convert", data={})

    mock_classify.assert_not_called()
    assert response.status_code == 200
    assert "No card produced" in response.text


def test_convert_high_confidence_renders_card_directly():
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        response = client.post("/convert", data=RAW_ATTACK_FORM)

    assert response.status_code == 200
    assert "BITE" in response.text.upper()
    assert "Human Review Requested" not in response.text


def test_convert_low_confidence_shows_review_form():
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.3)):
        response = client.post("/convert", data=RAW_ATTACK_FORM)

    assert response.status_code == 200
    assert "Human Review Requested" in response.text
    assert "test rationale" in response.text


def test_convert_reports_model_unavailable_error():
    with patch("monsterforge.ui.app.classify_attack", side_effect=ModelUnavailableError("gone")):
        response = client.post("/convert", data=RAW_ATTACK_FORM)

    assert response.status_code == 503
    assert "unavailable" in response.text.lower()


# =====================
# POST /review
# =====================
def _review_page_html(confidence=0.3, **result_overrides):
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(
            confidence=confidence, **result_overrides)):
        response = client.post("/convert", data=RAW_ATTACK_FORM)

    return response.text


def test_review_approve_keeps_original_result():
    semantic_result_json = _extract_semantic_result_json(_review_page_html())

    response = client.post("/review", data={
        "raw_attack_name": "Bite", "raw_attack_modifier": "+5",
        "raw_attack_attack_type": "melee", "raw_attack_attack_effect": "1d6+3",
        "semantic_result_json": semantic_result_json, "decision": "approve",
    })

    assert response.status_code == 200
    assert "BITE" in response.text.upper()


def test_review_correct_uses_edited_fields():
    semantic_result_json = _extract_semantic_result_json(_review_page_html())

    response = client.post("/review", data={
        "raw_attack_name": "Bite", "raw_attack_modifier": "+5",
        "raw_attack_attack_type": "melee", "raw_attack_attack_effect": "1d6+3",
        "semantic_result_json": semantic_result_json, "decision": "correct",
        "description": "A hand-corrected bite.", "move_type": "magical",
        "range_value": "", "range_unit": "metric",
    })

    assert response.status_code == 200
    assert "a hand-corrected bite" in response.text.lower()


def test_review_correct_with_a_range_value_builds_effect_range():
    semantic_result_json = _extract_semantic_result_json(
        _review_page_html(move_range=EffectRange(effect_range=10, range_unit_system=UnitSystem.IMPERIAL))
    )

    # Just confirming the route accepts and processes a numeric range
    # value without error — the rendered card reduces range to a badge,
    # not asserted here in detail (already covered by rendering's own tests).
    response = client.post("/review", data={
        "raw_attack_name": "Bite", "raw_attack_modifier": "+5",
        "raw_attack_attack_type": "melee", "raw_attack_attack_effect": "1d6+3",
        "semantic_result_json": semantic_result_json, "decision": "correct",
        "description": "A ranged bite.", "move_type": "physical",
        "range_value": "60", "range_unit": "metric",
    })

    assert response.status_code == 200


def test_review_reject_produces_no_card():
    semantic_result_json = _extract_semantic_result_json(_review_page_html())

    response = client.post("/review", data={
        "raw_attack_name": "Bite", "raw_attack_modifier": "+5",
        "raw_attack_attack_type": "melee", "raw_attack_attack_effect": "1d6+3",
        "semantic_result_json": semantic_result_json, "decision": "reject",
    })

    assert response.status_code == 200
    assert "No card produced" in response.text
