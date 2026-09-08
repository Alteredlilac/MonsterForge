"""
Tests for the cards library (ui/routes/library.py): GET /library/cards,
GET /library/cards/{raw_field_id}, and GET /library/events/
{classification_event_id}/review.
"""
import html
from unittest.mock import patch

from monsterforge.db.enums import EventStatus
from monsterforge.db.pipeline import ClassificationEvent, RawField
from monsterforge.validation.enums import ValidationStatus
from tests.ui.conftest import (
    RAW_ATTACK_FORM,
    REVIEW_HIDDEN_BASE,
    TEMPLATE_NAME,
    client,
    extract_review_ids,
    extract_semantic_result_json,
    make_semantic_result,
    review_page_html,
)


# =====================
# GET /library/cards
# =====================
def test_library_is_empty_when_nothing_is_saved():
    response = client.get("/library/cards")

    assert response.status_code == 200
    assert "0 Cards in the Library" in response.text


def test_library_lists_a_saved_auto_approved_card():
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        client.post("/convert", data=RAW_ATTACK_FORM)

    response = client.get("/library/cards")

    assert response.status_code == 200
    assert "1 Cards in the Library" in response.text
    assert "BITE" in response.text.upper()
    assert "A vicious bite." in response.text  # classification values block


def test_library_shows_a_rejected_attack_with_no_card_or_classification_tabs():
    """A rejected raw_field must stay reachable (name, id, Raw Input and
    History tabs) instead of vanishing from the library entirely -- but
    with no Card/Classification/JSON tabs, since none of them exist for
    it (see pipeline.attack_repository.list_saved_cards())."""
    page_html = review_page_html(confidence=0.3)
    client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": extract_semantic_result_json(page_html), "decision": "reject",
    })

    response = client.get("/library/cards")

    assert "1 Cards in the Library" in response.text
    assert "BITE" in response.text.upper()
    assert "rejected" in response.text.lower()
    assert 'data-bs-target="#card-1"' not in response.text
    assert 'data-bs-target="#classification-1"' not in response.text
    assert 'data-bs-target="#json-1"' not in response.text
    assert 'data-bs-target="#history-1"' in response.text


def test_library_hides_human_review_fields_for_an_auto_approved_card():
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        client.post("/convert", data=RAW_ATTACK_FORM)

    response = client.get("/library/cards")

    assert "assigned_llm_score" not in response.text
    assert "edit_note" not in response.text


def test_library_shows_human_review_fields_when_present():
    page_html = review_page_html(confidence=0.3)
    client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": extract_semantic_result_json(page_html), "decision": "approve",
        "assigned_llm_score": "0.6", "edit_note": "Looks fine.",
    })

    response = client.get("/library/cards")
    unescaped = html.unescape(response.text)  # the JSON block is HTML-escaped by autoescape

    assert '"assigned_llm_score": 0.6' in unescaped
    assert '"edit_note": "Looks fine."' in unescaped


def test_library_search_filters_by_name():
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        client.post("/convert", data=RAW_ATTACK_FORM)
        client.post("/convert", data={**RAW_ATTACK_FORM, "name": "Claw", "attack_effect": "1d4+3"})

    response = client.get("/library/cards", params={"q": "bit"})

    assert "BITE" in response.text.upper()
    assert "CLAW" not in response.text.upper()


def test_library_search_matches_an_id_prefix(seeded_db_session):
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        client.post("/convert", data=RAW_ATTACK_FORM)

    raw_field = seeded_db_session.query(RawField).one()
    response = client.get("/library/cards", params={"q": raw_field.id[:8]})

    assert "BITE" in response.text.upper()


def test_library_search_with_no_match_shows_a_message():
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        client.post("/convert", data=RAW_ATTACK_FORM)

    response = client.get("/library/cards", params={"q": "nonexistent"})

    assert 'No cards match "nonexistent"' in response.text
    assert "BITE" not in response.text.upper()


def test_library_search_input_retains_the_query():
    response = client.get("/library/cards", params={"q": "Bite"})

    assert 'value="Bite"' in response.text


def test_library_shows_the_corrected_classification_not_the_original():
    """The bug this guards against: the LLM proposed move_type=physical
    (make_semantic_result()'s default); a human corrected it to magical.
    The library's Classification tab must show the corrected value that
    the saved card actually renders, not the LLM's pre-correction one."""
    page_html = review_page_html()
    client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": extract_semantic_result_json(page_html), "decision": "correct",
        "name": "Bite", "description": "A vicious bite.", "move_type": "magical",
        "range_value": "", "range_unit": "metric",
    })

    response = client.get("/library/cards")
    unescaped = html.unescape(response.text)

    assert '"move_type": "magical"' in unescaped


def test_library_history_highlights_the_field_a_correction_changed():
    page_html = review_page_html()  # LLM proposed move_type=physical (default)
    client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": extract_semantic_result_json(page_html), "decision": "correct",
        "name": "Bite", "description": "A vicious bite.", "move_type": "magical",
        "range_value": "", "range_unit": "metric",
    })

    unescaped = html.unescape(client.get("/library/cards").text)

    assert '<span class="history-changed">"magical"</span>' in unescaped
    # The LLM_RUN entry is first in the history, nothing to compare
    # against yet, so its own move_type is never flagged as changed.
    assert '<span class="">"physical"</span>' in unescaped


def test_library_shows_history_for_a_saved_card():
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        client.post("/convert", data=RAW_ATTACK_FORM)

    response = client.get("/library/cards")

    assert "llm_run" in response.text
    assert '<span class="badge bg-success">active</span>' in response.text


# =====================
# GET /library/cards/{raw_field_id}
# =====================
def test_view_saved_card_shows_the_card_and_edit_controls(seeded_db_session):
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        client.post("/convert", data=RAW_ATTACK_FORM)

    raw_field = seeded_db_session.query(RawField).one()
    response = client.get(f"/library/cards/{raw_field.id}")

    assert response.status_code == 200
    assert "BITE" in response.text.upper()
    assert "Edit this classification" in response.text
    assert 'onclick="window.print()"' in response.text


def test_view_saved_card_returns_404_for_an_unknown_id():
    response = client.get("/library/cards/does-not-exist")

    assert response.status_code == 404


def test_view_saved_card_reports_a_previously_rejected_attack(seeded_db_session):
    page_html = review_page_html(confidence=0.3)
    client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": extract_semantic_result_json(page_html), "decision": "reject",
    })

    raw_field = seeded_db_session.query(RawField).one()
    response = client.get(f"/library/cards/{raw_field.id}")

    assert response.status_code == 422
    assert "previously rejected" in response.text.lower()


def test_view_saved_card_resolves_template_name_for_an_auto_approved_result(seeded_db_session):
    chosen = "attacks/classify_attack_confidence_guard.jinja2"
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        client.post("/convert", data={**RAW_ATTACK_FORM, "template_name": chosen})

    raw_field = seeded_db_session.query(RawField).one()
    response = client.get(f"/library/cards/{raw_field.id}")

    assert f'value="{chosen}"' in response.text


def test_view_saved_card_resolves_template_name_from_the_referenced_llm_run_after_review(seeded_db_session):
    """The active event here is the HUMAN_REVIEW, not the LLM_RUN --
    prompt_name lives only on the LLM_RUN it references (see
    db/pipeline.py), so this must walk back to it rather than default."""
    chosen = "attacks/classify_attack_confidence_guard.jinja2"
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.3)):
        page_html = client.post("/convert", data={**RAW_ATTACK_FORM, "template_name": chosen}).text

    client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": extract_semantic_result_json(page_html), "decision": "approve",
    })

    raw_field = seeded_db_session.query(RawField).one()
    response = client.get(f"/library/cards/{raw_field.id}")

    assert f'value="{chosen}"' in response.text


# =====================
# GET /library/events/{classification_event_id}/review
# =====================
def test_reopen_event_for_review_shows_the_review_form(seeded_db_session):
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        client.post("/convert", data=RAW_ATTACK_FORM)

    raw_field = seeded_db_session.query(RawField).one()
    response = client.get(f"/library/events/{raw_field.current_classification_event_id}/review")

    assert response.status_code == 200
    assert "Human Review Requested" in response.text
    assert 'value="Bite"' in response.text


def test_reopen_event_for_review_returns_404_for_an_unknown_id():
    response = client.get("/library/events/does-not-exist/review")

    assert response.status_code == 404


def test_reopen_event_for_review_can_reactivate_an_old_event(seeded_db_session):
    """The whole point of MVP 2.18: approving a past, now-archived event
    makes it the new active result again, superseding whatever
    superseded it -- not just editing the currently active one."""
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        client.post("/convert", data=RAW_ATTACK_FORM)

    raw_field = seeded_db_session.query(RawField).one()
    original_event_id = raw_field.current_classification_event_id

    card_page = client.get(f"/library/cards/{raw_field.id}").text
    client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(card_page),
        "semantic_result_json": extract_semantic_result_json(card_page), "decision": "correct",
        "name": "Bite", "description": "A corrected bite.", "move_type": "magical",
        "range_value": "", "range_unit": "metric",
    })
    seeded_db_session.refresh(raw_field)
    assert raw_field.current_classification_event_id != original_event_id  # sanity check

    reopen_page = client.get(f"/library/events/{original_event_id}/review").text
    assert "A vicious bite." in reopen_page  # the original, pre-correction description
    assert "A corrected bite." not in reopen_page

    client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(reopen_page),
        "semantic_result_json": extract_semantic_result_json(reopen_page), "decision": "approve",
    })

    seeded_db_session.refresh(raw_field)
    reactivated_event = seeded_db_session.get(ClassificationEvent, raw_field.current_classification_event_id)
    assert reactivated_event.referenced_event_id == original_event_id


def test_reopen_event_for_review_prefills_the_image_from_that_events_own_card(seeded_db_session):
    """Regression: reopening an old, already-superseded event used to
    always show a blank image field, even when that event's own card had
    one -- the image must come from the specific event being reopened,
    not from whatever is currently active."""
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        client.post("/convert", data={**RAW_ATTACK_FORM, "image_uri": "https://example.com/original.png"})

    raw_field = seeded_db_session.query(RawField).one()
    original_event_id = raw_field.current_classification_event_id

    card_page = client.get(f"/library/cards/{raw_field.id}").text
    client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(card_page),
        "semantic_result_json": extract_semantic_result_json(card_page), "decision": "correct",
        "name": "Bite", "description": "A corrected bite.", "move_type": "magical",
        "range_value": "", "range_unit": "metric",
        "image_uri": "https://example.com/original.png",
        "corrected_image_uri": "https://example.com/updated.png",
    })

    reopen_page = client.get(f"/library/events/{original_event_id}/review")

    assert reopen_page.status_code == 200
    assert "https://example.com/original.png" in reopen_page.text
    assert "https://example.com/updated.png" not in reopen_page.text


def test_reopen_event_for_review_leaves_the_image_blank_when_that_event_has_no_card():
    """A superseded LLM_RUN overtaken by a rerun before ever being
    decided never had a card built for it -- reopening it must not
    raise (InconsistentActiveClassificationError caught as a normal,
    tolerated case here, not an anomaly), just show a blank image."""
    page_html = review_page_html()
    original_event_id = extract_review_ids(page_html)["classification_event_id"]

    with patch("monsterforge.ui.routes.review.classify_attack", return_value=make_semantic_result(confidence=0.2)):
        client.post("/review", data={
            **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
            "semantic_result_json": extract_semantic_result_json(page_html), "decision": "rerun",
            "rerun_template_name": TEMPLATE_NAME,
        })

    response = client.get(f"/library/events/{original_event_id}/review")

    assert response.status_code == 200
    assert 'name="corrected_image_uri"' in response.text


def test_reopen_event_for_review_resolves_the_name_as_of_that_specific_event(seeded_db_session):
    """Reopening an OLD event, from before a later name correction
    (MVP 2.19), must show the name as it stood back then -- not the
    raw_field's currently corrected name."""
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        client.post("/convert", data=RAW_ATTACK_FORM)

    raw_field = seeded_db_session.query(RawField).one()
    original_event_id = raw_field.current_classification_event_id

    card_page = client.get(f"/library/cards/{raw_field.id}").text
    client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(card_page),
        "semantic_result_json": extract_semantic_result_json(card_page), "decision": "correct",
        "name": "Fixed Name", "description": "A corrected bite.", "move_type": "magical",
        "range_value": "", "range_unit": "metric",
    })

    reopen_page = client.get(f"/library/events/{original_event_id}/review").text

    assert 'value="Bite"' in reopen_page
    assert 'value="Fixed Name"' not in reopen_page


def test_reopen_event_for_review_rejects_a_rejected_event(seeded_db_session):
    """Not reachable from the library UI (see library.html.jinja2's own
    "!= rejected" check), but guarded here too in case this URL is hit
    directly -- a REJECTED event's own result is an empty dict, nothing
    to build a review form from."""
    page_html = review_page_html(confidence=0.3)
    client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(page_html),
        "semantic_result_json": extract_semantic_result_json(page_html), "decision": "reject",
    })

    raw_field = seeded_db_session.query(RawField).one()
    response = client.get(f"/library/events/{raw_field.current_classification_event_id}/review")

    assert response.status_code == 422


def test_rejecting_a_reopened_old_event_does_not_deactivate_the_current_good_result(seeded_db_session):
    """Regression for a bug found testing MVP 2.18: rejecting a past,
    already-superseded event (reopened via /library/events/{id}/review)
    must not un-activate a genuinely good current result -- only
    rejecting the raw_field's currently active event (or its very first
    decision) takes over as active."""
    with patch("monsterforge.ui.routes.convert.classify_attack", return_value=make_semantic_result(confidence=0.95)):
        client.post("/convert", data=RAW_ATTACK_FORM)

    raw_field = seeded_db_session.query(RawField).one()
    original_event_id = raw_field.current_classification_event_id

    card_page = client.get(f"/library/cards/{raw_field.id}").text
    client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(card_page),
        "semantic_result_json": extract_semantic_result_json(card_page), "decision": "correct",
        "name": "Bite", "description": "A corrected bite.", "move_type": "magical",
        "range_value": "", "range_unit": "metric",
    })
    seeded_db_session.refresh(raw_field)
    corrected_event_id = raw_field.current_classification_event_id
    assert corrected_event_id != original_event_id  # sanity check

    reopen_page = client.get(f"/library/events/{original_event_id}/review").text
    response = client.post("/review", data={
        **REVIEW_HIDDEN_BASE, **extract_review_ids(reopen_page),
        "semantic_result_json": extract_semantic_result_json(reopen_page), "decision": "reject",
    })

    assert response.status_code == 200
    assert "not affected" in response.text.lower()

    seeded_db_session.refresh(raw_field)
    assert raw_field.current_classification_event_id == corrected_event_id  # still the good correction

    reject_event = (
        seeded_db_session.query(ClassificationEvent)
        .filter_by(referenced_event_id=original_event_id, decision=ValidationStatus.REJECTED)
        .one()
    )
    assert reject_event.status == EventStatus.PENDING  # recorded in history, never activated
