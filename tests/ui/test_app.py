"""
Tests for the MVP 1 FastAPI web app (ui/app.py).

Covers the four possible outcomes of the review gate (auto-approved,
approved, corrected, rejected), the blank-attack short-circuit, and a
ModelUnavailableError response. classify_attack is always mocked: no
real API calls in tests.
"""
import html
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


def _extract_semantic_result_json(page_html: str) -> str:
    """
    Matches the field in either of its two rendered forms: single-quoted
    and raw (review_form.html.jinja2) or double-quoted and HTML-entity-
    escaped (move_card_with_edit.html.jinja2, which escapes it to keep
    the embedded JSON's own quotes from breaking the attribute).
    html.unescape() is a no-op on already-plain text, so it's safe to
    apply unconditionally regardless of which form matched.
    """
    match = re.search(r"name=\"semantic_result_json\" value=(['\"])(.*?)\1", page_html)
    assert match is not None, "page did not include the expected hidden field"
    return html.unescape(match.group(2))


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
    assert 'href="/convert"' in response.text


def test_convert_malformed_attack_effect_reports_a_friendly_error():
    """
    A deterministic parsing/conversion failure downstream of
    classification (e.g. "2d80" — 80 isn't a real die type) must not
    reach the browser as FastAPI's generic, contextless 500 page, with
    the actual cause visible only in the server's own terminal.
    """
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        response = client.post("/convert", data={**RAW_ATTACK_FORM, "attack_effect": "2d80"})

    assert response.status_code == 422
    assert "Could not build the card" in response.text
    assert 'href="/convert"' in response.text


def test_convert_rejects_an_attack_type_outside_the_known_vocabulary():
    """
    is_melee()/is_touch() only recognize fixed English substrings
    ("melee", "touch", "ranged") — a value like "mischia" (Italian for
    melee) silently falls through to "ranged" instead of erroring,
    triggering an unwanted LLM range lookup for what was really a melee
    attack. Constraining attack_type to a Literal closes that off at
    the form boundary rather than the parser layer.
    """
    with patch("monsterforge.ui.app.classify_attack") as mock_classify:
        response = client.post("/convert", data={**RAW_ATTACK_FORM, "attack_type": "mischia"})

    mock_classify.assert_not_called()
    assert response.status_code == 422


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
    assert 'href="/convert"' in response.text


def test_convert_reports_other_classification_failures_too():
    with patch("monsterforge.ui.app.classify_attack", side_effect=RuntimeError("boom")):
        response = client.post("/convert", data=RAW_ATTACK_FORM)

    assert response.status_code == 502
    assert "Classification failed" in response.text
    assert 'href="/convert"' in response.text


def test_convert_force_review_bypasses_high_confidence():
    """force_review is a per-request checkbox value, never written to
    config.validation_settings.ALWAYS_ON (a shared, process-wide
    global unsafe to mutate per-request under concurrent traffic)."""
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        response = client.post("/convert", data={**RAW_ATTACK_FORM, "force_review": "true"})

    assert response.status_code == 200
    assert "Human Review Requested" in response.text


# =====================
# POST /review, POST /review/edit
# =====================
TEMPLATE_NAME = "attacks/classify_attack.jinja2"

REVIEW_HIDDEN_BASE = {
    "raw_attack_name": "Bite", "raw_attack_modifier": "+5",
    "raw_attack_attack_type": "melee", "raw_attack_attack_effect": "1d6+3",
    "template_name": TEMPLATE_NAME,
}


def _review_page_html(confidence=0.3, **result_overrides):
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(
            confidence=confidence, **result_overrides)):
        response = client.post("/convert", data=RAW_ATTACK_FORM)

    return response.text


def test_review_approve_keeps_original_result():
    semantic_result_json = _extract_semantic_result_json(_review_page_html())

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE,
        "semantic_result_json": semantic_result_json, "decision": "approve",
    })

    assert response.status_code == 200
    assert "BITE" in response.text.upper()


def test_review_survives_an_apostrophe_in_the_rationale():
    """
    review_form.html.jinja2's hidden semantic_result_json field is
    embedded in a single-quoted HTML attribute. Before this environment's
    autoescape was fixed (it was silently off, same root cause as
    rendering/'s "*.html.jinja2" gap — see move_card_renderer.py), an
    apostrophe anywhere in the LLM's rationale broke out of that
    attribute: a real browser would truncate the field's value at the
    apostrophe, and posting that truncated JSON back to /review crashed
    with an unhandled JSONDecodeError instead of a friendly error.
    """
    semantic_result_json = _extract_semantic_result_json(
        _review_page_html(rationale="the creature's bite is nasty")
    )

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE,
        "semantic_result_json": semantic_result_json, "decision": "approve",
    })

    assert response.status_code == 200
    assert "BITE" in response.text.upper()


def test_review_correct_uses_edited_fields():
    semantic_result_json = _extract_semantic_result_json(_review_page_html())

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE,
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
        **REVIEW_HIDDEN_BASE,
        "semantic_result_json": semantic_result_json, "decision": "correct",
        "description": "A ranged bite.", "move_type": "physical",
        "range_value": "60", "range_unit": "metric",
    })

    assert response.status_code == 200


def test_review_reject_produces_no_card():
    semantic_result_json = _extract_semantic_result_json(_review_page_html())

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE,
        "semantic_result_json": semantic_result_json, "decision": "reject",
    })

    assert response.status_code == 200
    assert "No card produced" in response.text
    assert 'href="/convert"' in response.text


def test_review_approve_carries_image_uri_through_to_the_card():
    semantic_result_json = _extract_semantic_result_json(_review_page_html())

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE,
        "semantic_result_json": semantic_result_json, "decision": "approve",
        "image_uri": "https://example.com/bite.png",
    })

    assert response.status_code == 200
    assert "https://example.com/bite.png" in response.text


def test_rendered_card_includes_an_edit_form_back_to_review():
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        response = client.post("/convert", data=RAW_ATTACK_FORM)

    assert response.status_code == 200
    assert 'action="/review/edit"' in response.text
    assert "Edit this classification" in response.text


def test_review_edit_reopens_the_review_form_without_reclassifying():
    """The whole point of /review/edit: revisit an already-produced
    card's classification without spending another LLM call."""
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        card_html = client.post("/convert", data=RAW_ATTACK_FORM).text

    semantic_result_json = _extract_semantic_result_json(card_html)

    with patch("monsterforge.ui.app.classify_attack") as mock_classify:
        response = client.post("/review/edit", data={
            **REVIEW_HIDDEN_BASE,
            "semantic_result_json": semantic_result_json,
        })

    mock_classify.assert_not_called()
    assert response.status_code == 200
    assert "Human Review Requested" in response.text


def test_review_edit_then_correct_updates_the_card():
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        card_html = client.post("/convert", data=RAW_ATTACK_FORM).text

    semantic_result_json = _extract_semantic_result_json(card_html)
    review_html = client.post("/review/edit", data={
        **REVIEW_HIDDEN_BASE,
        "semantic_result_json": semantic_result_json,
    }).text
    semantic_result_json_again = _extract_semantic_result_json(review_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE,
        "semantic_result_json": semantic_result_json_again, "decision": "correct",
        "description": "Edited after the fact.", "move_type": "physical",
        "range_value": "", "range_unit": "metric",
    })

    assert response.status_code == 200
    assert "edited after the fact" in response.text.lower()
