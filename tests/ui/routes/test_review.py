"""
Tests for POST /review and POST /review/edit (ui/routes/review.py).

Covers the four possible review decisions (approve/correct/reject/
rerun) and reopening an already-produced card's review form without
reclassifying. classify_attack is always mocked -- at
monsterforge.ui.routes.review for a rerun's own reclassification call
(where review() imports it from), or at monsterforge.ui.routes.convert
via review_page_html()'s setup call to /convert.
"""
from unittest.mock import patch

from monsterforge.db.pipeline import RawField
from monsterforge.llm.clients.gemini import ModelUnavailableError
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import UnitSystem
from tests.ui.conftest import (
    RAW_ATTACK_FORM,
    REVIEW_HIDDEN_BASE,
    TEMPLATE_NAME,
    client,
    extract_hidden_field,
    extract_review_ids,
    extract_semantic_result_json,
    make_semantic_result,
    review_page_html,
)

REVIEW_PATCH = "monsterforge.ui.routes.review.classify_attack"


def test_review_approve_keeps_original_result():
    page_html = review_page_html()
    semantic_result_json = extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
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
    page_html = review_page_html(rationale="the creature's bite is nasty")
    semantic_result_json = extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "approve",
    })

    assert response.status_code == 200
    assert "BITE" in response.text.upper()


def test_review_correct_uses_edited_fields():
    page_html = review_page_html()
    semantic_result_json = extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "correct",
        "name": "Bite", "description": "A hand-corrected bite.", "move_type": "magical",
        "range_value": "", "range_unit": "metric",
    })

    assert response.status_code == 200
    assert "a hand-corrected bite" in response.text.lower()


def test_review_correct_with_a_range_value_builds_effect_range():
    page_html = review_page_html(
        move_range=EffectRange(effect_range=10, range_unit_system=UnitSystem.IMPERIAL)
    )
    semantic_result_json = extract_semantic_result_json(page_html)

    # Just confirming the route accepts and processes a numeric range
    # value without error — the rendered card reduces range to a badge,
    # not asserted here in detail (already covered by rendering's own tests).
    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "correct",
        "name": "Bite", "description": "A ranged bite.", "move_type": "physical",
        "range_value": "60", "range_unit": "metric",
    })

    assert response.status_code == 200


def test_review_reject_produces_no_card():
    page_html = review_page_html()
    semantic_result_json = extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "reject",
    })

    assert response.status_code == 200
    assert "No card produced" in response.text
    assert 'href="/convert"' in response.text


def test_review_rerun_reclassifies_and_shows_the_new_result():
    """Mirrors _review_input.py's CLI rerun: a real second
    classify_attack() call, landing back on the review form (not a
    rendered card) with the new classification."""
    page_html = review_page_html()
    semantic_result_json = extract_semantic_result_json(page_html)
    chosen_template = "attacks/classify_attack_confidence_guard.jinja2"

    with patch(
        REVIEW_PATCH,
        return_value=make_semantic_result(confidence=0.2, description="reclassified description"),
    ) as mock_classify:
        response = client.post("/review", data={
            **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
            "semantic_result_json": semantic_result_json, "decision": "rerun",
            "rerun_template_name": chosen_template,
        })

    assert response.status_code == 200
    assert "Human Review Requested" in response.text
    assert "reclassified description" in response.text
    assert mock_classify.call_args.kwargs["template_name"] == chosen_template


def test_review_rerun_appends_note_to_additional_description():
    page_html = review_page_html(rationale="original rationale")
    semantic_result_json = extract_semantic_result_json(page_html)

    with patch(REVIEW_PATCH, return_value=make_semantic_result()) as mock_classify:
        client.post("/review", data={
            **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
            "semantic_result_json": semantic_result_json, "decision": "rerun",
            "rerun_template_name": TEMPLATE_NAME, "rerun_note": "double-check this one",
        })

    assert mock_classify.call_args.kwargs["additional_description"] == "double-check this one"


def test_review_rerun_unknown_template_keeps_the_original_result():
    page_html = review_page_html(description="original description")
    semantic_result_json = extract_semantic_result_json(page_html)

    with patch(REVIEW_PATCH) as mock_classify:
        response = client.post("/review", data={
            **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
            "semantic_result_json": semantic_result_json, "decision": "rerun",
            "rerun_template_name": "attacks/bogus.jinja2",
        })

    mock_classify.assert_not_called()
    assert response.status_code == 200
    assert "original description" in response.text
    assert "Unknown prompt template" in response.text


def test_review_rerun_model_unavailable_keeps_the_original_result():
    page_html = review_page_html(description="original description")
    semantic_result_json = extract_semantic_result_json(page_html)

    with patch(REVIEW_PATCH, side_effect=ModelUnavailableError("gone")):
        response = client.post("/review", data={
            **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
            "semantic_result_json": semantic_result_json, "decision": "rerun",
            "rerun_template_name": TEMPLATE_NAME,
        })

    assert response.status_code == 200
    assert "original description" in response.text
    assert "unavailable" in response.text.lower()


def test_review_rerun_classification_failure_keeps_the_original_result():
    page_html = review_page_html(description="original description")
    semantic_result_json = extract_semantic_result_json(page_html)

    with patch(REVIEW_PATCH, side_effect=RuntimeError("boom")):
        response = client.post("/review", data={
            **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
            "semantic_result_json": semantic_result_json, "decision": "rerun",
            "rerun_template_name": TEMPLATE_NAME,
        })

    assert response.status_code == 200
    assert "original description" in response.text
    assert "Rerun failed" in response.text


def test_review_approve_carries_image_uri_through_to_the_card():
    page_html = review_page_html()
    semantic_result_json = extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "approve",
        "image_uri": "https://example.com/bite.png",
    })

    assert response.status_code == 200
    assert "https://example.com/bite.png" in response.text


def test_review_correct_uses_the_corrected_image_uri_not_the_original():
    """Changing the image is a visual correction, only meaningful on the
    "correct" branch -- the corrected value must win over whatever the
    original, unchanged image_uri hidden field still carries."""
    page_html = review_page_html()
    semantic_result_json = extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "correct",
        "name": "Bite", "description": "A vicious bite.", "move_type": "physical",
        "range_value": "", "range_unit": "metric",
        "image_uri": "https://example.com/original.png",
        "corrected_image_uri": "https://example.com/new.png",
    })

    assert response.status_code == 200
    assert "https://example.com/new.png" in response.text
    assert "https://example.com/original.png" not in response.text


def test_review_approve_ignores_a_stray_corrected_image_uri():
    """corrected_image_uri is only ever read on the "correct" branch
    (see ui/routes/review.py::review()) -- Approve must keep the
    original image_uri untouched even if a value happens to be present
    in that field."""
    page_html = review_page_html()
    semantic_result_json = extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "approve",
        "image_uri": "https://example.com/original.png",
        "corrected_image_uri": "https://example.com/should-be-ignored.png",
    })

    assert response.status_code == 200
    assert "https://example.com/original.png" in response.text
    assert "https://example.com/should-be-ignored.png" not in response.text


def test_review_edit_reopens_the_review_form_without_reclassifying():
    """The whole point of /review/edit: revisit an already-produced
    card's classification without spending another LLM call."""
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        card_html = client.post("/convert", data=RAW_ATTACK_FORM).text

    semantic_result_json = extract_semantic_result_json(card_html)

    with patch(REVIEW_PATCH) as mock_classify:
        response = client.post("/review/edit", data={
            **REVIEW_HIDDEN_BASE, **extract_review_ids(card_html),
            "semantic_result_json": semantic_result_json,
        })

    mock_classify.assert_not_called()
    assert response.status_code == 200
    assert "Human Review Requested" in response.text


def test_review_edit_then_correct_updates_the_card():
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        card_html = client.post("/convert", data=RAW_ATTACK_FORM).text

    semantic_result_json = extract_semantic_result_json(card_html)
    card_ids = extract_review_ids(card_html)
    review_html = client.post("/review/edit", data={
        **REVIEW_HIDDEN_BASE, **card_ids,
        "semantic_result_json": semantic_result_json,
    }).text
    semantic_result_json_again = extract_semantic_result_json(review_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(review_html),
        "semantic_result_json": semantic_result_json_again, "decision": "correct",
        "name": "Bite", "description": "Edited after the fact.", "move_type": "physical",
        "range_value": "", "range_unit": "metric",
    })

    assert response.status_code == 200
    assert "edited after the fact" in response.text.lower()


def test_review_correct_rejects_a_negative_range_value():
    page_html = review_page_html(
        move_range=EffectRange(effect_range=10, range_unit_system=UnitSystem.IMPERIAL)
    )
    semantic_result_json = extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "correct",
        "name": "Bite", "description": "A ranged bite.", "move_type": "physical",
        "range_value": "-10", "range_unit": "metric",
    })

    assert response.status_code == 422


def test_review_correct_can_fix_the_name():
    page_html = review_page_html()
    semantic_result_json = extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "correct",
        "name": "Fixed Name", "description": "A vicious bite.", "move_type": "physical",
        "range_value": "", "range_unit": "metric",
    })

    assert response.status_code == 200
    assert "FIXED NAME" in response.text.upper()


def test_review_correct_persists_the_name_for_later_reopening(seeded_db_session):
    """Regression for MVP 2.19: a name correction used to be lost the
    moment the card was rendered -- reopening it later (e.g. from the
    library) would silently revert the edit form to the original name.
    Now persisted via classification_events.corrected_name."""
    page_html = review_page_html()
    semantic_result_json = extract_semantic_result_json(page_html)

    client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "correct",
        "name": "Fixed Name", "description": "A vicious bite.", "move_type": "physical",
        "range_value": "", "range_unit": "metric",
    })

    raw_field = seeded_db_session.query(RawField).one()
    view_page = client.get(f"/library/cards/{raw_field.id}").text

    assert extract_hidden_field(view_page, "raw_attack_name") == "Fixed Name"


def test_review_correct_with_a_blank_name_is_rejected():
    """Server-side backstop for the same rule the review form enforces
    client-side (required + formnovalidate on Approve/Reject) — a
    non-browser client could still submit a blank name on Correct."""
    page_html = review_page_html()
    semantic_result_json = extract_semantic_result_json(page_html)

    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
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
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.3)):
        response = client.post("/convert", data={**RAW_ATTACK_FORM, "modifier": ""})

    semantic_result_json = extract_semantic_result_json(response.text)

    review_response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(response.text), "raw_attack_modifier": "",
        "semantic_result_json": semantic_result_json, "decision": "approve",
    })

    assert review_response.status_code == 200
    assert "BITE" in review_response.text.upper()


def test_review_approve_with_an_unresolvable_range_bounces_back_to_review():
    """Same failure UnknownAttackRange bounce-back covers on /convert,
    reached by clicking Approve without filling in the range fields in
    review (they're optional there, unlike /convert) — arguably more
    likely to happen this way than via the direct /convert path this
    scenario was first found through."""
    page_html = review_page_html(move_range=None)
    semantic_result_json = extract_semantic_result_json(page_html)
    hidden = {**REVIEW_HIDDEN_BASE, "raw_attack_name": "Arco", "raw_attack_attack_type": "ranged"}

    response = client.post("/review", data={
        **hidden, **extract_review_ids(page_html),
        "semantic_result_json": semantic_result_json, "decision": "approve",
    })

    assert response.status_code == 200
    assert "Human Review Requested" in response.text
    assert "not mapped" in response.text.lower()
