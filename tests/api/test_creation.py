"""
Tests for api/creation.py: POST /api/cards and
POST /api/cards/{raw_field_id}/rerun.

classify_attack is always mocked at monsterforge.api.creation (where
both routes import it from), not monsterforge.api.app or
monsterforge.llm itself, since patch replaces a name binding at its
import site -- the same convention tests/ui/routes/test_convert.py
already follows for ui.routes.convert.classify_attack.
"""
from unittest.mock import patch

from monsterforge.db.cards import Card
from monsterforge.db.pipeline import ClassificationEvent, RawField
from monsterforge.llm.clients.gemini import ModelUnavailableError
from monsterforge.pipeline.attack_repository import activate_classification_event, record_human_review
from monsterforge.pipeline.reference_lookups import get_human_actor
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import HumanReview
from tests.api.conftest import client, make_semantic_result, save_auto_approved_card, save_rejected_attack

CREATE_PATCH = "monsterforge.api.creation.classify_attack"
# Same fields as tests.conftest.BITE (name/modifier/attack_type/attack_effect
# are exactly what compute_fingerprint() hashes) -- so a test that saves a
# card via save_auto_approved_card()/save_rejected_attack() (which use
# BITE) and then posts BITE_BODY hits the very same fingerprint, the same
# way two independent submissions of the identical attack would.
BITE_BODY = {"name": "Bite", "modifier": "+7", "attack_type": "melee", "attack_effect": "1d6+3"}


def test_create_card_auto_approves_a_high_confidence_attack():
    with patch(CREATE_PATCH, return_value=make_semantic_result(confidence=0.95)):
        response = client.post("/api/cards", json=BITE_BODY)

    assert response.status_code == 201
    assert response.json()["name"] == "Bite"


def test_create_card_reports_pending_review_for_a_low_confidence_attack():
    with patch(CREATE_PATCH, return_value=make_semantic_result(confidence=0.1)) as mock_classify:
        response = client.post("/api/cards", json=BITE_BODY)

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending_review"
    assert "event_id" in body
    mock_classify.assert_called_once()


def test_create_card_is_a_cache_hit_on_a_repeat_submission():
    with patch(CREATE_PATCH, return_value=make_semantic_result(confidence=0.95)):
        first = client.post("/api/cards", json=BITE_BODY)

    with patch(CREATE_PATCH) as mock_classify:
        second = client.post("/api/cards", json=BITE_BODY)

    assert second.status_code == 200
    assert second.json() == first.json()
    mock_classify.assert_not_called()


def test_create_card_reports_model_unavailable_error():
    with patch(CREATE_PATCH, side_effect=ModelUnavailableError("no model available")):
        response = client.post("/api/cards", json=BITE_BODY)

    assert response.status_code == 503
    assert "no model available" in response.json()["error"]


def test_create_card_reports_other_classification_failures_too():
    with patch(CREATE_PATCH, side_effect=RuntimeError("boom")):
        response = client.post("/api/cards", json=BITE_BODY)

    assert response.status_code == 502
    assert "boom" in response.json()["error"]


def test_create_card_rejects_an_unknown_prompt_template():
    with patch(CREATE_PATCH) as mock_classify:
        response = client.post("/api/cards", json={**BITE_BODY, "template_name": "nope.jinja2"})

    mock_classify.assert_not_called()
    assert response.status_code == 422


def test_create_card_rejects_a_previously_rejected_attack_without_reclassifying(seeded_db_session, make_raw_field):
    save_rejected_attack(seeded_db_session, make_raw_field)

    with patch(CREATE_PATCH) as mock_classify:
        response = client.post("/api/cards", json=BITE_BODY)

    mock_classify.assert_not_called()
    assert response.status_code == 422
    assert response.json() == {"error": "This attack was previously rejected."}


def test_create_card_reports_a_missing_saved_card_instead_of_silently_reclassifying(seeded_db_session):
    """InconsistentActiveClassificationError's whole reason to exist,
    reached this time through the create route's own cache-hit branch."""
    with patch(CREATE_PATCH, return_value=make_semantic_result(confidence=0.95)) as mock_classify:
        client.post("/api/cards", json=BITE_BODY)

        seeded_db_session.query(Card).delete()
        seeded_db_session.commit()

        second = client.post("/api/cards", json=BITE_BODY)

    assert mock_classify.call_count == 1  # still not reclassified
    assert second.status_code == 500
    assert "Could not load the saved card" in second.json()["error"]


def test_create_card_ranged_attack_without_context_or_range_is_rejected():
    with patch(CREATE_PATCH) as mock_classify:
        response = client.post("/api/cards", json={
            "name": "Web", "attack_type": "ranged", "attack_effect": "entangle",
        })

    mock_classify.assert_not_called()
    assert response.status_code == 422


def test_create_card_ranged_attack_with_range_fields_overrides_the_llm_move_range():
    """The request's own range/unit is trusted over whatever the LLM
    returns for move_range, even though it's also handed to the LLM as
    context (so its confidence reflects that it had the value)."""
    with patch(CREATE_PATCH, return_value=make_semantic_result(confidence=0.95)) as mock_classify:
        response = client.post("/api/cards", json={
            "name": "Web", "attack_type": "ranged", "attack_effect": "entangle",
            "range_value": 45, "range_unit": "metric",
        })

    assert response.status_code == 201
    assert response.json()["range_value"] == 45
    assert "Range: 45 meters." in mock_classify.call_args.kwargs["additional_description"]


def test_create_card_melee_attack_ignores_range_fields_even_if_provided():
    with patch(CREATE_PATCH, return_value=make_semantic_result(confidence=0.95)):
        response = client.post("/api/cards", json={**BITE_BODY, "range_value": 10, "range_unit": "imperial"})

    assert response.status_code == 201


def test_create_card_rejects_an_attack_type_outside_the_known_vocabulary():
    with patch(CREATE_PATCH) as mock_classify:
        response = client.post("/api/cards", json={**BITE_BODY, "attack_type": "mischia"})

    mock_classify.assert_not_called()
    assert response.status_code == 422


def test_create_card_rejects_a_range_value_given_without_its_unit():
    with patch(CREATE_PATCH) as mock_classify:
        response = client.post("/api/cards", json={
            "name": "Web", "attack_type": "ranged", "attack_effect": "entangle", "range_value": 30,
        })

    mock_classify.assert_not_called()
    assert response.status_code == 422


def test_create_card_includes_the_submitted_image_uri():
    with patch(CREATE_PATCH, return_value=make_semantic_result(confidence=0.95)):
        response = client.post("/api/cards", json={**BITE_BODY, "image_uri": "https://example.com/bite.png"})

    assert response.json()["image_uri"] == "https://example.com/bite.png"


# =====================
# POST /api/cards/{raw_field_id}/rerun
# =====================
def test_rerun_card_auto_approves_a_high_confidence_reclassification(seeded_db_session, make_raw_field, build_and_save_card):
    raw_field, _card_data = save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card)

    with patch(CREATE_PATCH, return_value=make_semantic_result(confidence=0.95, description="Reclassified.")):
        response = client.post(f"/api/cards/{raw_field.id}/rerun")

    assert response.status_code == 201
    assert response.json()["description"] == "Reclassified."


def test_rerun_card_reports_pending_review_for_a_low_confidence_reclassification(
        seeded_db_session, make_raw_field, build_and_save_card):
    raw_field, _card_data = save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card)

    with patch(CREATE_PATCH, return_value=make_semantic_result(confidence=0.1)) as mock_classify:
        response = client.post(f"/api/cards/{raw_field.id}/rerun")

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending_review"
    assert "event_id" in body
    mock_classify.assert_called_once()


def test_rerun_card_returns_404_for_an_unknown_raw_field():
    with patch(CREATE_PATCH) as mock_classify:
        response = client.post("/api/cards/does-not-exist/rerun")

    mock_classify.assert_not_called()
    assert response.status_code == 404
    assert response.json() == {"error": "No such raw field."}


def test_rerun_card_rejects_an_unknown_prompt_template(seeded_db_session, make_raw_field, build_and_save_card):
    raw_field, _card_data = save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card)

    with patch(CREATE_PATCH) as mock_classify:
        response = client.post(f"/api/cards/{raw_field.id}/rerun", json={"template_name": "nope.jinja2"})

    mock_classify.assert_not_called()
    assert response.status_code == 422


def test_rerun_card_reports_model_unavailable_error(seeded_db_session, make_raw_field, build_and_save_card):
    raw_field, _card_data = save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card)

    with patch(CREATE_PATCH, side_effect=ModelUnavailableError("no model available")):
        response = client.post(f"/api/cards/{raw_field.id}/rerun")

    assert response.status_code == 503
    assert "no model available" in response.json()["error"]


def test_rerun_card_reports_other_classification_failures_too(seeded_db_session, make_raw_field, build_and_save_card):
    raw_field, _card_data = save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card)

    with patch(CREATE_PATCH, side_effect=RuntimeError("boom")):
        response = client.post(f"/api/cards/{raw_field.id}/rerun")

    assert response.status_code == 502
    assert "boom" in response.json()["error"]


def test_rerun_card_rejects_a_raw_field_whose_active_event_is_rejected(seeded_db_session, make_raw_field):
    raw_field = save_rejected_attack(seeded_db_session, make_raw_field)

    with patch(CREATE_PATCH) as mock_classify:
        response = client.post(f"/api/cards/{raw_field.id}/rerun")

    mock_classify.assert_not_called()
    assert response.status_code == 422
    assert response.json() == {"error": "This attack was previously rejected."}


def test_rerun_card_never_checks_the_fingerprint_cache(seeded_db_session, make_raw_field, build_and_save_card):
    """Unlike POST /api/cards, a rerun always reclassifies -- a
    deliberate manual retry must never be deduplicated against a
    fingerprint, even against the identical attack twice in a row."""
    raw_field, _card_data = save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card)

    with patch(CREATE_PATCH, return_value=make_semantic_result(confidence=0.95)) as mock_classify:
        client.post(f"/api/cards/{raw_field.id}/rerun")
        client.post(f"/api/cards/{raw_field.id}/rerun")

    assert mock_classify.call_count == 2


def test_rerun_card_appends_the_note_to_additional_description(seeded_db_session, make_raw_field, build_and_save_card):
    raw_field, _card_data = save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card)

    with patch(CREATE_PATCH, return_value=make_semantic_result(confidence=0.95)) as mock_classify:
        client.post(f"/api/cards/{raw_field.id}/rerun", json={"note": "It's actually magical."})

    assert mock_classify.call_args.kwargs["additional_description"] == "It's actually magical."


def test_rerun_card_uses_the_effective_name_after_an_earlier_correction(
        seeded_db_session, make_raw_field, build_and_save_card):
    """resolve_effective_name(), not raw_fields.data["name"] directly --
    a name corrected in an earlier review must carry forward into a
    later rerun's own reclassification."""
    raw_field, _card_data = save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card)
    original_event = seeded_db_session.get(RawField, raw_field.id).current_classification_event_id

    correction_event = record_human_review(
        seeded_db_session, raw_field=raw_field,
        referenced_event=seeded_db_session.get(ClassificationEvent, original_event),
        review=HumanReview(status=ValidationStatus.CORRECTED, result=make_semantic_result(), corrected_name="Fixed Name"),
        actor=get_human_actor(seeded_db_session),
    )
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=correction_event)

    with patch(CREATE_PATCH, return_value=make_semantic_result(confidence=0.95)) as mock_classify:
        client.post(f"/api/cards/{raw_field.id}/rerun")

    assert mock_classify.call_args.kwargs["raw_attack"].name == "Fixed Name"


def test_rerun_card_works_on_a_raw_field_whose_only_event_was_never_activated(seeded_db_session, make_raw_field):
    """A low-confidence POST /api/cards submission records an LLM_RUN
    event but never activates it (see create_card()'s own comment) --
    rerun must still work by raw_field id, falling back to the
    raw_field's own original name via resolve_effective_name()'s own
    fallback (current_classification_event_id is None, so it can't
    match any event in the raw_field's history)."""
    with patch(CREATE_PATCH, return_value=make_semantic_result(confidence=0.1)):
        create_response = client.post("/api/cards", json=BITE_BODY)
    pending_event = seeded_db_session.get(ClassificationEvent, create_response.json()["event_id"])
    raw_field = seeded_db_session.get(RawField, pending_event.raw_field_id)
    assert raw_field.current_classification_event_id is None

    with patch(CREATE_PATCH, return_value=make_semantic_result(confidence=0.95)) as mock_classify:
        response = client.post(f"/api/cards/{raw_field.id}/rerun")

    assert response.status_code == 201
    assert mock_classify.call_args.kwargs["raw_attack"].name == "Bite"
