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
from monsterforge.db.cards import Card
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


def _extract_hidden_field(page_html: str, field_name: str) -> str:
    """
    Matches a hidden input's value in either of its two rendered forms:
    single-quoted and raw (review_form.html.jinja2) or double-quoted and
    HTML-entity-escaped (move_card_with_edit.html.jinja2, which escapes
    it to keep an embedded value's own quotes from breaking the
    attribute). html.unescape() is a no-op on already-plain text, so
    it's safe to apply unconditionally regardless of which form matched.
    """
    match = re.search(rf"name=\"{field_name}\" value=(['\"])(.*?)\1", page_html)
    assert match is not None, f"page did not include the expected hidden field {field_name!r}"
    return html.unescape(match.group(2))


def _extract_semantic_result_json(page_html: str) -> str:
    return _extract_hidden_field(page_html, "semantic_result_json")


def _extract_review_ids(page_html: str) -> dict:
    """raw_field_id/classification_event_id, needed on every /review and
    /review/edit POST since the database wiring — extracted from a prior
    /convert (or /review) response the same way semantic_result_json is."""
    return {
        "raw_field_id": _extract_hidden_field(page_html, "raw_field_id"),
        "classification_event_id": _extract_hidden_field(page_html, "classification_event_id"),
    }


# =====================
# GET /convert
# =====================
def test_show_convert_form_lists_creature_subtypes():
    response = client.get("/convert")

    assert response.status_code == 200
    assert "incorporeal" in response.text


def test_show_convert_form_lists_prompt_templates():
    response = client.get("/convert")

    assert response.status_code == 200
    assert "Confidence guard" in response.text
    assert "attacks/classify_attack_confidence_guard.jinja2" in response.text


def test_show_convert_form_embeds_sample_attacks_for_auto_fill():
    """The Auto-fill button and its JS both depend on a sampleAttacks
    array being embedded on the page -- a missing/renamed context key
    would silently break the button with no server-side error."""
    response = client.get("/convert")

    assert response.status_code == 200
    assert 'id="auto_fill_button"' in response.text
    assert "var sampleAttacks = [" in response.text


# =====================
# POST /convert
# =====================
def test_convert_without_a_name_is_rejected_before_classification():
    """
    Name became mandatory on /convert (a nameless MoveCard is a
    degenerate case, and a blank name reaching /review also triggered a
    FastAPI quirk — see the NOTE on review()'s raw_attack_* parameters).
    A completely empty submission is now rejected by FastAPI's own
    required-field validation before classify_attack() is ever called —
    the old is_blank_attack() short-circuit is no longer reachable
    through this route, since every submission that passes validation
    already has a non-blank name.
    """
    with patch("monsterforge.ui.app.classify_attack") as mock_classify:
        response = client.post("/convert", data={})

    mock_classify.assert_not_called()
    assert response.status_code == 422


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


def test_convert_rejects_an_unknown_prompt_template():
    """Deliberately not a Literal[...] like attack_type — checked
    against ATTACK_PROMPT_TEMPLATE_OPTIONS directly instead, so that
    list stays the single source of truth."""
    with patch("monsterforge.ui.app.classify_attack") as mock_classify:
        response = client.post("/convert", data={**RAW_ATTACK_FORM, "template_name": "attacks/bogus.jinja2"})

    mock_classify.assert_not_called()
    assert response.status_code == 422


def test_convert_forwards_a_chosen_non_default_template():
    chosen = "attacks/classify_attack_confidence_guard.jinja2"

    with patch(
        "monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.95),
    ) as mock_classify:
        response = client.post("/convert", data={**RAW_ATTACK_FORM, "template_name": chosen})

    assert mock_classify.call_args.kwargs["template_name"] == chosen
    # Surfaces on the rendered card's "Edit this classification" hidden
    # field, so a later /review/edit round trip keeps using the same template.
    assert f'value="{chosen}"' in response.text


def test_convert_force_review_bypasses_high_confidence():
    """force_review is a per-request checkbox value, never written to
    config.validation_settings.ALWAYS_ON (a shared, process-wide
    global unsafe to mutate per-request under concurrent traffic)."""
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        response = client.post("/convert", data={**RAW_ATTACK_FORM, "force_review": "true"})

    assert response.status_code == 200
    assert "Human Review Requested" in response.text


# =====================
# POST /convert — range/unit
# =====================
RANGED_ATTACK_FORM = {"name": "Bow", "modifier": "+5", "attack_type": "ranged", "attack_effect": "1d8"}


def test_convert_ranged_attack_without_context_or_range_is_rejected():
    with patch("monsterforge.ui.app.classify_attack") as mock_classify:
        response = client.post("/convert", data=RANGED_ATTACK_FORM)

    mock_classify.assert_not_called()
    assert response.status_code == 422
    assert "range" in response.text.lower()


def test_convert_ranged_attack_with_description_skips_the_range_requirement():
    """A ranged attack whose range is already stated in prose doesn't
    need the structured range fields — the existing free-text path
    (classify_attack reading additional_description) already resolves
    most real attacks correctly, so the structured fields are a
    last-resort requirement, not a blanket one. move_range is set on the
    mock to stand in for a real LLM call actually resolving "Range 60
    feet." from the prose — mocking classify_attack means nothing
    downstream would resolve a range from context text otherwise."""
    mocked_result = make_semantic_result(
        confidence=0.95, move_range=EffectRange(effect_range=60, range_unit_system=UnitSystem.IMPERIAL),
    )
    with patch("monsterforge.ui.app.classify_attack", return_value=mocked_result) as mock_classify:
        response = client.post("/convert", data={
            **RANGED_ATTACK_FORM, "additional_description": "Range 60 feet.",
        })

    mock_classify.assert_called_once()
    assert response.status_code == 200


def test_convert_ranged_attack_with_range_fields_overrides_the_llm_move_range():
    """The form's own range/unit is trusted over whatever the LLM
    returns for move_range, even though it's also handed to the LLM as
    context (so its confidence reflects that it had the value)."""
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.95)) as mock_classify:
        response = client.post("/convert", data={
            **RANGED_ATTACK_FORM, "range_value": "45", "range_unit": "metric",
        })

    assert response.status_code == 200
    assert ">45<" in response.text
    _, kwargs = mock_classify.call_args
    assert "Range: 45 meters." in kwargs["additional_description"]


def test_convert_negative_range_value_is_rejected():
    with patch("monsterforge.ui.app.classify_attack") as mock_classify:
        response = client.post("/convert", data={
            **RANGED_ATTACK_FORM, "range_value": "-5", "range_unit": "metric",
        })

    mock_classify.assert_not_called()
    assert response.status_code == 422


def test_convert_melee_attack_ignores_range_fields_even_if_provided():
    """get_known_attack_range() ignores range for a melee attack
    regardless of what's supplied — a stray value here (e.g. left over
    from switching attack_type in the browser) must not error."""
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        response = client.post("/convert", data={
            **RAW_ATTACK_FORM, "range_value": "-5", "range_unit": "metric",
        })

    assert response.status_code == 200


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
    page_html = _review_page_html()
    semantic_result_json = _extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **_extract_review_ids(page_html),
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
    page_html = _review_page_html(rationale="the creature's bite is nasty")
    semantic_result_json = _extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **_extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "approve",
    })

    assert response.status_code == 200
    assert "BITE" in response.text.upper()


def test_review_correct_uses_edited_fields():
    page_html = _review_page_html()
    semantic_result_json = _extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **_extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "correct",
        "name": "Bite", "description": "A hand-corrected bite.", "move_type": "magical",
        "range_value": "", "range_unit": "metric",
    })

    assert response.status_code == 200
    assert "a hand-corrected bite" in response.text.lower()


def test_review_correct_with_a_range_value_builds_effect_range():
    page_html = _review_page_html(
        move_range=EffectRange(effect_range=10, range_unit_system=UnitSystem.IMPERIAL)
    )
    semantic_result_json = _extract_semantic_result_json(page_html)

    # Just confirming the route accepts and processes a numeric range
    # value without error — the rendered card reduces range to a badge,
    # not asserted here in detail (already covered by rendering's own tests).
    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **_extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "correct",
        "name": "Bite", "description": "A ranged bite.", "move_type": "physical",
        "range_value": "60", "range_unit": "metric",
    })

    assert response.status_code == 200


def test_review_reject_produces_no_card():
    page_html = _review_page_html()
    semantic_result_json = _extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **_extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "reject",
    })

    assert response.status_code == 200
    assert "No card produced" in response.text
    assert 'href="/convert"' in response.text


def test_review_rerun_reclassifies_and_shows_the_new_result():
    """Mirrors _review_input.py's CLI rerun: a real second
    classify_attack() call, landing back on the review form (not a
    rendered card) with the new classification."""
    page_html = _review_page_html()
    semantic_result_json = _extract_semantic_result_json(page_html)
    chosen_template = "attacks/classify_attack_confidence_guard.jinja2"

    with patch(
        "monsterforge.ui.app.classify_attack",
        return_value=make_semantic_result(confidence=0.2, description="reclassified description"),
    ) as mock_classify:
        response = client.post("/review", data={
            **REVIEW_HIDDEN_BASE, **_extract_review_ids(page_html),
            "semantic_result_json": semantic_result_json, "decision": "rerun",
            "rerun_template_name": chosen_template,
        })

    assert response.status_code == 200
    assert "Human Review Requested" in response.text
    assert "reclassified description" in response.text
    assert mock_classify.call_args.kwargs["template_name"] == chosen_template


def test_review_rerun_appends_note_to_additional_description():
    page_html = _review_page_html(rationale="original rationale")
    semantic_result_json = _extract_semantic_result_json(page_html)

    with patch(
        "monsterforge.ui.app.classify_attack", return_value=make_semantic_result(),
    ) as mock_classify:
        client.post("/review", data={
            **REVIEW_HIDDEN_BASE, **_extract_review_ids(page_html),
            "semantic_result_json": semantic_result_json, "decision": "rerun",
            "rerun_template_name": TEMPLATE_NAME, "rerun_note": "double-check this one",
        })

    assert mock_classify.call_args.kwargs["additional_description"] == "double-check this one"


def test_review_rerun_unknown_template_keeps_the_original_result():
    page_html = _review_page_html(description="original description")
    semantic_result_json = _extract_semantic_result_json(page_html)

    with patch("monsterforge.ui.app.classify_attack") as mock_classify:
        response = client.post("/review", data={
            **REVIEW_HIDDEN_BASE, **_extract_review_ids(page_html),
            "semantic_result_json": semantic_result_json, "decision": "rerun",
            "rerun_template_name": "attacks/bogus.jinja2",
        })

    mock_classify.assert_not_called()
    assert response.status_code == 200
    assert "original description" in response.text
    assert "Unknown prompt template" in response.text


def test_review_rerun_model_unavailable_keeps_the_original_result():
    page_html = _review_page_html(description="original description")
    semantic_result_json = _extract_semantic_result_json(page_html)

    with patch("monsterforge.ui.app.classify_attack", side_effect=ModelUnavailableError("gone")):
        response = client.post("/review", data={
            **REVIEW_HIDDEN_BASE, **_extract_review_ids(page_html),
            "semantic_result_json": semantic_result_json, "decision": "rerun",
            "rerun_template_name": TEMPLATE_NAME,
        })

    assert response.status_code == 200
    assert "original description" in response.text
    assert "unavailable" in response.text.lower()


def test_review_rerun_classification_failure_keeps_the_original_result():
    page_html = _review_page_html(description="original description")
    semantic_result_json = _extract_semantic_result_json(page_html)

    with patch("monsterforge.ui.app.classify_attack", side_effect=RuntimeError("boom")):
        response = client.post("/review", data={
            **REVIEW_HIDDEN_BASE, **_extract_review_ids(page_html),
            "semantic_result_json": semantic_result_json, "decision": "rerun",
            "rerun_template_name": TEMPLATE_NAME,
        })

    assert response.status_code == 200
    assert "original description" in response.text
    assert "Rerun failed" in response.text


def test_review_approve_carries_image_uri_through_to_the_card():
    page_html = _review_page_html()
    semantic_result_json = _extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **_extract_review_ids(page_html),
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
            **REVIEW_HIDDEN_BASE, **_extract_review_ids(card_html),
            "semantic_result_json": semantic_result_json,
        })

    mock_classify.assert_not_called()
    assert response.status_code == 200
    assert "Human Review Requested" in response.text


def test_review_edit_then_correct_updates_the_card():
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        card_html = client.post("/convert", data=RAW_ATTACK_FORM).text

    semantic_result_json = _extract_semantic_result_json(card_html)
    card_ids = _extract_review_ids(card_html)
    review_html = client.post("/review/edit", data={
        **REVIEW_HIDDEN_BASE, **card_ids,
        "semantic_result_json": semantic_result_json,
    }).text
    semantic_result_json_again = _extract_semantic_result_json(review_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **_extract_review_ids(review_html),
        "semantic_result_json": semantic_result_json_again, "decision": "correct",
        "name": "Bite", "description": "Edited after the fact.", "move_type": "physical",
        "range_value": "", "range_unit": "metric",
    })

    assert response.status_code == 200
    assert "edited after the fact" in response.text.lower()


def test_review_correct_rejects_a_negative_range_value():
    page_html = _review_page_html(
        move_range=EffectRange(effect_range=10, range_unit_system=UnitSystem.IMPERIAL)
    )
    semantic_result_json = _extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **_extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "correct",
        "name": "Bite", "description": "A ranged bite.", "move_type": "physical",
        "range_value": "-10", "range_unit": "metric",
    })

    assert response.status_code == 422


def test_review_page_hides_range_fields_for_a_melee_attack():
    """get_known_attack_range() ignores range for melee regardless of
    what's supplied — showing an editable-but-inert field there is
    confusing, not just unnecessary."""
    page = _review_page_html()  # REVIEW_HIDDEN_BASE / RAW_ATTACK_FORM default attack_type is "melee"

    assert 'name="range_value"' not in page


def test_review_page_shows_range_fields_for_a_ranged_attack():
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.3)):
        response = client.post("/convert", data={
            **RANGED_ATTACK_FORM, "additional_description": "Range 60 feet.",
        })

    assert 'name="range_value"' in response.text


def test_review_correct_can_fix_the_name():
    page_html = _review_page_html()
    semantic_result_json = _extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **_extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "correct",
        "name": "Fixed Name", "description": "A vicious bite.", "move_type": "physical",
        "range_value": "", "range_unit": "metric",
    })

    assert response.status_code == 200
    assert "FIXED NAME" in response.text.upper()


def test_review_correct_with_a_blank_name_is_rejected():
    """Server-side backstop for the same rule the review form enforces
    client-side (required + formnovalidate on Approve/Reject) — a
    non-browser client could still submit a blank name on Correct."""
    page_html = _review_page_html()
    semantic_result_json = _extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **_extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "correct",
        "name": "", "description": "A vicious bite.", "move_type": "physical",
        "range_value": "", "range_unit": "metric",
    })

    assert response.status_code == 422


def test_review_survives_a_blank_modifier():
    """Regression test for the FastAPI quirk fixed on review()'s
    raw_attack_* parameters: a legitimately blank modifier
    (get_modifier() treats it as "no attack bonus") was being treated as
    a missing required field, 422ing every decision — including Reject —
    whenever the original attack had no modifier."""
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.3)):
        response = client.post("/convert", data={**RAW_ATTACK_FORM, "modifier": ""})

    semantic_result_json = _extract_semantic_result_json(response.text)

    review_response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **_extract_review_ids(response.text), "raw_attack_modifier": "",
        "semantic_result_json": semantic_result_json, "decision": "approve",
    })

    assert review_response.status_code == 200
    assert "BITE" in review_response.text.upper()


# =====================
# UnknownAttackRange bounce-back
# =====================
def test_convert_unresolvable_range_bounces_back_to_review_with_a_message():
    """A ranged attack whose name isn't in KNOWN_ATTACKS and whose
    context didn't let the LLM resolve a range used to dead-end with a
    generic "Could not build the card" message and no way to fix it —
    it now lands back on the review form (range is directly fixable
    there) with an explanation of what went wrong."""
    mocked_result = make_semantic_result(confidence=0.95, move_range=None)
    with patch("monsterforge.ui.app.classify_attack", return_value=mocked_result):
        response = client.post("/convert", data={
            "name": "Arco", "modifier": "+5", "attack_type": "ranged",
            "attack_effect": "1d8", "additional_description": "A bow-like weapon.",
        })

    assert response.status_code == 200
    assert "Human Review Requested" in response.text
    assert "not mapped" in response.text.lower()


def test_review_approve_with_an_unresolvable_range_bounces_back_to_review():
    """Same failure, reached by clicking Approve without filling in the
    range fields in review (they're optional there, unlike /convert) —
    arguably more likely to happen this way than via the direct
    /convert path this scenario was first found through."""
    page_html = _review_page_html(move_range=None)
    semantic_result_json = _extract_semantic_result_json(page_html)
    hidden = {**REVIEW_HIDDEN_BASE, "raw_attack_name": "Arco", "raw_attack_attack_type": "ranged"}

    response = client.post("/review", data={
        **hidden, **_extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "approve",
    })

    assert response.status_code == 200
    assert "Human Review Requested" in response.text
    assert "not mapped" in response.text.lower()


def test_convert_malformed_dice_still_dead_ends_instead_of_bouncing_back():
    """Scope check: only UnknownAttackRange bounces back to review — a
    malformed dice expression has no fixable field in the review form
    (attack_effect isn't editable there), so it must stay a dead-end
    message instead of looping the reviewer back to the same failure."""
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        response = client.post("/convert", data={**RAW_ATTACK_FORM, "attack_effect": "2d80"})

    assert response.status_code == 422
    assert "Could not build the card" in response.text
    assert "Human Review Requested" not in response.text


# =====================
# FINGERPRINT CACHE
# =====================
def test_convert_same_attack_twice_is_a_cache_hit():
    """The whole point of the fingerprint: no second LLM call, and the
    same saved card served both times (stable identity, not recomputed)."""
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.95)) as mock_classify:
        first = client.post("/convert", data=RAW_ATTACK_FORM)
        second = client.post("/convert", data=RAW_ATTACK_FORM)

    assert first.status_code == 200
    assert second.status_code == 200
    assert mock_classify.call_count == 1
    assert _extract_review_ids(first.text) == _extract_review_ids(second.text)


def test_convert_a_previously_rejected_attack_shows_a_message_without_reclassifying():
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.3)) as mock_classify:
        review_page = client.post("/convert", data=RAW_ATTACK_FORM)

        reject_response = client.post("/review", data={
            **REVIEW_HIDDEN_BASE, **_extract_review_ids(review_page.text),
            "semantic_result_json": _extract_semantic_result_json(review_page.text), "decision": "reject",
        })
        assert "No card produced" in reject_response.text

        second = client.post("/convert", data=RAW_ATTACK_FORM)

    assert mock_classify.call_count == 1
    assert second.status_code == 422
    assert "previously rejected" in second.text.lower()


def test_convert_reports_a_missing_saved_card_instead_of_silently_reclassifying(seeded_db_session):
    """InconsistentActiveClassificationError's whole reason to exist: an
    active event whose card was somehow never saved must be reported
    loudly, not silently reclassified as if nothing had happened."""
    with patch("monsterforge.ui.app.classify_attack", return_value=make_semantic_result(confidence=0.95)) as mock_classify:
        client.post("/convert", data=RAW_ATTACK_FORM)

        seeded_db_session.query(Card).delete()
        seeded_db_session.commit()

        second = client.post("/convert", data=RAW_ATTACK_FORM)

    assert mock_classify.call_count == 1  # still not reclassified
    assert second.status_code == 500
    assert "Could not load the saved card" in second.text
