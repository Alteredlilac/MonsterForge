"""
Tests for api/routes.py: GET /api/cards and GET /api/cards/{raw_field_id}.

Cards are built directly through pipeline.attack_repository (the same
factory fixtures tests/pipeline/ uses), not through ui/'s /convert --
api/ and ui/ are independent branches (see api/app.py), and these tests
should not depend on the web UI's own routes to set up their data.
"""
from monsterforge.db.cards import Card
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

RESULT = AttackSemanticResult(
    description="A vicious bite.", move_type=MoveType.PHYSICAL, move_range=None,
    confidence=0.95, rationale="Clear.",
)


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
