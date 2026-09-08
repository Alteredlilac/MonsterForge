"""
Tests for GET/POST /convert (ui/routes/convert.py).

classify_attack is always mocked at monsterforge.ui.routes.convert
(where convert() imports it from), not monsterforge.ui.app -- patch
replaces a name binding at its import site, not the function globally,
so it has to target wherever the route module actually imported it.

A few tests here were originally filed under other section headers in
the pre-split tests/ui/test_app.py (a "POST /review" review-form-display
check, an "UnknownAttackRange bounce-back" case, "FINGERPRINT CACHE")
but, verified individually, only ever call /convert -- moved here on
that basis rather than by the section header they happened to sit
under, per this project's testing conventions.
"""
from unittest.mock import patch

from monsterforge.db.cards import Card
from monsterforge.llm.clients.gemini import ModelUnavailableError
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import UnitSystem
from tests.ui.conftest import (
    RAW_ATTACK_FORM,
    REVIEW_HIDDEN_BASE,
    client,
    extract_review_ids,
    extract_semantic_result_json,
    make_semantic_result,
)

CONVERT_PATCH = "monsterforge.ui.routes.convert.classify_attack"


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
    with patch(CONVERT_PATCH) as mock_classify:
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
    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.95)):
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
    with patch(CONVERT_PATCH) as mock_classify:
        response = client.post("/convert", data={**RAW_ATTACK_FORM, "attack_type": "mischia"})

    mock_classify.assert_not_called()
    assert response.status_code == 422


def test_convert_high_confidence_renders_card_directly():
    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.95)):
        response = client.post("/convert", data=RAW_ATTACK_FORM)

    assert response.status_code == 200
    assert "BITE" in response.text.upper()
    assert "Human Review Requested" not in response.text


def test_convert_low_confidence_shows_review_form():
    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.3)):
        response = client.post("/convert", data=RAW_ATTACK_FORM)

    assert response.status_code == 200
    assert "Human Review Requested" in response.text
    assert "test rationale" in response.text


def test_convert_reports_model_unavailable_error():
    with patch(CONVERT_PATCH, side_effect=ModelUnavailableError("gone")):
        response = client.post("/convert", data=RAW_ATTACK_FORM)

    assert response.status_code == 503
    assert "unavailable" in response.text.lower()
    assert 'href="/convert"' in response.text


def test_convert_reports_other_classification_failures_too():
    with patch(CONVERT_PATCH, side_effect=RuntimeError("boom")):
        response = client.post("/convert", data=RAW_ATTACK_FORM)

    assert response.status_code == 502
    assert "Classification failed" in response.text
    assert 'href="/convert"' in response.text


def test_convert_rejects_an_unknown_prompt_template():
    """Deliberately not a Literal[...] like attack_type — checked
    against ATTACK_PROMPT_TEMPLATE_OPTIONS directly instead, so that
    list stays the single source of truth."""
    with patch(CONVERT_PATCH) as mock_classify:
        response = client.post("/convert", data={**RAW_ATTACK_FORM, "template_name": "attacks/bogus.jinja2"})

    mock_classify.assert_not_called()
    assert response.status_code == 422


def test_convert_forwards_a_chosen_non_default_template():
    chosen = "attacks/classify_attack_confidence_guard.jinja2"

    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.95)) as mock_classify:
        response = client.post("/convert", data={**RAW_ATTACK_FORM, "template_name": chosen})

    assert mock_classify.call_args.kwargs["template_name"] == chosen
    # Surfaces on the rendered card's "Edit this classification" hidden
    # field, so a later /review/edit round trip keeps using the same template.
    assert f'value="{chosen}"' in response.text


def test_convert_force_review_bypasses_high_confidence():
    """force_review is a per-request checkbox value, never written to
    config.validation_settings.ALWAYS_ON (a shared, process-wide
    global unsafe to mutate per-request under concurrent traffic)."""
    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.95)):
        response = client.post("/convert", data={**RAW_ATTACK_FORM, "force_review": "true"})

    assert response.status_code == 200
    assert "Human Review Requested" in response.text


def test_review_form_prefills_corrected_image_uri_with_the_current_image():
    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.3)):
        response = client.post("/convert", data={**RAW_ATTACK_FORM, "image_uri": "https://example.com/bite.png"})

    assert response.status_code == 200
    assert 'name="corrected_image_uri"' in response.text
    assert 'value="https://example.com/bite.png"' in response.text


def test_rendered_card_includes_an_edit_form_back_to_review():
    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.95)):
        response = client.post("/convert", data=RAW_ATTACK_FORM)

    assert response.status_code == 200
    assert 'action="/review/edit"' in response.text
    assert "Edit this classification" in response.text


def test_review_page_hides_range_fields_for_a_melee_attack():
    """get_known_attack_range() ignores range for melee regardless of
    what's supplied — showing an editable-but-inert field there is
    confusing, not just unnecessary."""
    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.3)):
        response = client.post("/convert", data=RAW_ATTACK_FORM)

    assert 'name="range_value"' not in response.text


# =====================
# POST /convert — range/unit
# =====================
RANGED_ATTACK_FORM = {"name": "Bow", "modifier": "+5", "attack_type": "ranged", "attack_effect": "1d8"}


def test_convert_ranged_attack_without_context_or_range_is_rejected():
    with patch(CONVERT_PATCH) as mock_classify:
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
    with patch(CONVERT_PATCH, return_value=mocked_result) as mock_classify:
        response = client.post("/convert", data={
            **RANGED_ATTACK_FORM, "additional_description": "Range 60 feet.",
        })

    mock_classify.assert_called_once()
    assert response.status_code == 200


def test_convert_ranged_attack_with_range_fields_overrides_the_llm_move_range():
    """The form's own range/unit is trusted over whatever the LLM
    returns for move_range, even though it's also handed to the LLM as
    context (so its confidence reflects that it had the value)."""
    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.95)) as mock_classify:
        response = client.post("/convert", data={
            **RANGED_ATTACK_FORM, "range_value": "45", "range_unit": "metric",
        })

    assert response.status_code == 200
    assert ">45<" in response.text
    _, kwargs = mock_classify.call_args
    assert "Range: 45 meters." in kwargs["additional_description"]


def test_convert_negative_range_value_is_rejected():
    with patch(CONVERT_PATCH) as mock_classify:
        response = client.post("/convert", data={
            **RANGED_ATTACK_FORM, "range_value": "-5", "range_unit": "metric",
        })

    mock_classify.assert_not_called()
    assert response.status_code == 422


def test_convert_melee_attack_ignores_range_fields_even_if_provided():
    """get_known_attack_range() ignores range for a melee attack
    regardless of what's supplied — a stray value here (e.g. left over
    from switching attack_type in the browser) must not error."""
    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.95)):
        response = client.post("/convert", data={
            **RAW_ATTACK_FORM, "range_value": "-5", "range_unit": "metric",
        })

    assert response.status_code == 200


def test_review_page_shows_range_fields_for_a_ranged_attack():
    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.3)):
        response = client.post("/convert", data={
            **RANGED_ATTACK_FORM, "additional_description": "Range 60 feet.",
        })

    assert 'name="range_value"' in response.text


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
    with patch(CONVERT_PATCH, return_value=mocked_result):
        response = client.post("/convert", data={
            "name": "Arco", "modifier": "+5", "attack_type": "ranged",
            "attack_effect": "1d8", "additional_description": "A bow-like weapon.",
        })

    assert response.status_code == 200
    assert "Human Review Requested" in response.text
    assert "not mapped" in response.text.lower()


def test_convert_malformed_dice_still_dead_ends_instead_of_bouncing_back():
    """Scope check: only UnknownAttackRange bounces back to review — a
    malformed dice expression has no fixable field in the review form
    (attack_effect isn't editable there), so it must stay a dead-end
    message instead of looping the reviewer back to the same failure."""
    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.95)):
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
    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.95)) as mock_classify:
        first = client.post("/convert", data=RAW_ATTACK_FORM)
        second = client.post("/convert", data=RAW_ATTACK_FORM)

    assert first.status_code == 200
    assert second.status_code == 200
    assert mock_classify.call_count == 1
    assert extract_review_ids(first.text) == extract_review_ids(second.text)


def test_convert_a_previously_rejected_attack_shows_a_message_without_reclassifying():
    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.3)) as mock_classify:
        review_page = client.post("/convert", data=RAW_ATTACK_FORM)

        reject_response = client.post("/review", data={
            **REVIEW_HIDDEN_BASE, **extract_review_ids(review_page.text),
            "semantic_result_json": extract_semantic_result_json(review_page.text), "decision": "reject",
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
    with patch(CONVERT_PATCH, return_value=make_semantic_result(confidence=0.95)) as mock_classify:
        client.post("/convert", data=RAW_ATTACK_FORM)

        seeded_db_session.query(Card).delete()
        seeded_db_session.commit()

        second = client.post("/convert", data=RAW_ATTACK_FORM)

    assert mock_classify.call_count == 1  # still not reclassified
    assert second.status_code == 500
    assert "Could not load the saved card" in second.text
