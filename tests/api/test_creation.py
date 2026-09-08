"""
Tests for api/creation.py: POST /api/cards.

classify_attack is always mocked at monsterforge.api.creation (where
create_card() imports it from), not monsterforge.api.app or
monsterforge.llm itself, since patch replaces a name binding at its
import site -- the same convention tests/ui/routes/test_convert.py
already follows for ui.routes.convert.classify_attack.
"""
from unittest.mock import patch

from monsterforge.db.cards import Card
from monsterforge.llm.clients.gemini import ModelUnavailableError
from tests.api.conftest import client, make_semantic_result, save_rejected_attack

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
