"""
Tests for api/routes.py: GET /api/cards, GET /api/cards/{raw_field_id},
and POST /api/cards.

GET tests build cards directly through pipeline.attack_repository (the
same factory fixtures tests/pipeline/ uses), not through ui/'s /convert
-- api/ and ui/ are independent branches (see api/app.py), and these
tests should not depend on the web UI's own routes to set up their
data. POST /api/cards tests call the route itself, the same way
tests/ui/routes/test_convert.py exercises /convert -- classify_attack
is always mocked at monsterforge.api.routes (where create_card()
imports it from), not monsterforge.api.app or monsterforge.llm itself,
since patch replaces a name binding at its import site.
"""
from unittest.mock import patch

from monsterforge.db.cards import Card
from monsterforge.llm.clients.gemini import ModelUnavailableError
from monsterforge.llm.semantic_classification.attacks import AttackSemanticResult
from monsterforge.pipeline.attack_repository import (
    activate_classification_event,
    record_human_review,
    record_llm_run,
)
from monsterforge.pipeline.reference_lookups import get_human_actor, get_llm_actor
from monsterforge.structured_data.dnd.v3x.enums import MoveType
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import HumanReview
from tests.api.conftest import client
from tests.conftest import BITE, CLAW

CREATE_PATCH = "monsterforge.api.routes.classify_attack"
# Same fields as tests.conftest.BITE (name/modifier/attack_type/attack_effect
# are exactly what compute_fingerprint() hashes) -- so a test that saves a
# card via _save_auto_approved_card()/_save_rejected_attack() (which use
# BITE) and then posts BITE_BODY hits the very same fingerprint, the same
# way two independent submissions of the identical attack would.
BITE_BODY = {"name": "Bite", "modifier": "+7", "attack_type": "melee", "attack_effect": "1d6+3"}

RESULT = AttackSemanticResult(
    description="A vicious bite.", move_type=MoveType.PHYSICAL, move_range=None,
    confidence=0.95, rationale="Clear.",
)


def make_semantic_result(**overrides):
    defaults = dict(
        description="A vicious bite.", move_type=MoveType.PHYSICAL, move_range=None,
        confidence=0.95, rationale="Clear.",
    )
    defaults.update(overrides)
    return AttackSemanticResult(**defaults)


def _save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card, raw_attack=BITE):
    raw_field = make_raw_field(raw_attack)
    event = record_llm_run(
        seeded_db_session, raw_field=raw_field, semantic_result=RESULT, actor=get_llm_actor(seeded_db_session),
        prompt_name="classify_attack.jinja2", model_name="gemini-flash-lite-latest",
        confidence_threshold=0.7, decision=ValidationStatus.AUTO_APPROVED,
    )
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=event)
    card_data = build_and_save_card(raw_field, event, raw_attack, RESULT)
    return raw_field, card_data


def _save_rejected_attack(seeded_db_session, make_raw_field):
    raw_field = make_raw_field()
    llm_event = record_llm_run(
        seeded_db_session, raw_field=raw_field, semantic_result=RESULT, actor=get_llm_actor(seeded_db_session),
        prompt_name="classify_attack.jinja2", model_name="gemini-flash-lite-latest",
        confidence_threshold=0.7, decision=None,
    )
    reject_event = record_human_review(
        seeded_db_session, raw_field=raw_field, referenced_event=llm_event,
        review=HumanReview(status=ValidationStatus.REJECTED, result=None),
        actor=get_human_actor(seeded_db_session),
    )
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=reject_event)
    return raw_field


# =====================
# GET /api/cards
# =====================
def test_list_cards_is_empty_when_nothing_is_saved():
    response = client.get("/api/cards")

    assert response.status_code == 200
    assert response.json() == []


def test_list_cards_includes_a_saved_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card):
    raw_field, card_data = _save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card)

    response = client.get("/api/cards")

    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 1
    assert entries[0]["raw_field_id"] == raw_field.id
    assert entries[0]["move_card"]["id"] == card_data["id"]


def test_list_cards_excludes_a_rejected_attack_with_no_card(seeded_db_session, make_raw_field):
    """A REJECTED active event has no card at all -- GET /library/cards
    still lists it (a reviewer can reactivate an earlier good attempt),
    but a read-only API consumer has nothing to receive for it, so it's
    filtered out here rather than returned with move_card: null."""
    _save_rejected_attack(seeded_db_session, make_raw_field)

    response = client.get("/api/cards")

    assert response.status_code == 200
    assert response.json() == []


def test_list_cards_filters_by_name(seeded_db_session, make_raw_field, build_and_save_card):
    _save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card, raw_attack=BITE)
    _save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card, raw_attack=CLAW)

    response = client.get("/api/cards", params={"q": "bit"})

    entries = response.json()
    assert len(entries) == 1
    assert entries[0]["name"] == "Bite"


def test_list_cards_filters_by_id_prefix(seeded_db_session, make_raw_field, build_and_save_card):
    raw_field, _card_data = _save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card)

    response = client.get("/api/cards", params={"q": raw_field.id[:8]})

    entries = response.json()
    assert len(entries) == 1
    assert entries[0]["raw_field_id"] == raw_field.id


# =====================
# GET /api/cards/{raw_field_id}
# =====================
def test_get_card_returns_the_full_card_content(seeded_db_session, make_raw_field, build_and_save_card):
    raw_field, card_data = _save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card)

    response = client.get(f"/api/cards/{raw_field.id}")

    assert response.status_code == 200
    assert response.json() == card_data


def test_get_card_returns_404_for_an_unknown_id():
    response = client.get("/api/cards/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"error": "No saved card found for that id."}


def test_get_card_returns_422_for_a_previously_rejected_attack(seeded_db_session, make_raw_field):
    raw_field = _save_rejected_attack(seeded_db_session, make_raw_field)

    response = client.get(f"/api/cards/{raw_field.id}")

    assert response.status_code == 422
    assert response.json() == {"error": "This attack was previously rejected — no card to show."}


def test_get_card_returns_500_when_active_event_has_no_saved_card(seeded_db_session, make_raw_field, build_and_save_card):
    """InconsistentActiveClassificationError's whole reason to exist: an
    active event whose card was somehow never saved must be reported
    loudly, not silently reclassified or treated as missing."""
    raw_field, _card_data = _save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card)
    seeded_db_session.query(Card).delete()
    seeded_db_session.commit()

    response = client.get(f"/api/cards/{raw_field.id}")

    assert response.status_code == 500
    assert "Could not load the saved card" in response.json()["error"]


# =====================
# POST /api/cards
# =====================
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
    _save_rejected_attack(seeded_db_session, make_raw_field)

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
