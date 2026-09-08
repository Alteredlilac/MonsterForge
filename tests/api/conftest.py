"""
Shared fixtures and test helpers for tests/api/: a TestClient bound to
api.app.app -- not ui.app.app, a separate application (see
monsterforge/api/app.py) -- with the same per-test database override
and LLM-client mock tests/ui/conftest.py uses for its own, independent
app, plus the setup sequences both tests/api/test_reads.py and
tests/api/test_creation.py need for a saved (auto-approved or
rejected) attack.
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from monsterforge.api.app import app
from monsterforge.db.session import get_db_session
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
from tests.conftest import BITE

client = TestClient(app)


@pytest.fixture(autouse=True)
def _override_db_session(seeded_db_session):
    """Replace the app's real database dependency with the isolated,
    already-seeded in-memory session for every test in this package."""
    def _yield_test_session():
        yield seeded_db_session

    app.dependency_overrides[get_db_session] = _yield_test_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _mock_llm_client():
    """record_llm_run() reads get_llm_client().model_name for logging on
    every real classification -- a real call none of these tests
    anticipate, and it tries to build a real GeminiClient requiring a
    real GEMINI_API_KEY. Autouse so no test needs its own patch for a
    call it doesn't otherwise care about, mirroring tests/ui/conftest.py's
    identical fixture for ui.routes.convert/review. get_llm_client is
    imported into api.creation only (api.reads never classifies)."""
    with patch("monsterforge.api.creation.get_llm_client") as mock_get_client:
        mock_get_client.return_value.model_name = "test-model"
        yield


def make_semantic_result(**overrides):
    defaults = dict(
        description="A vicious bite.", move_type=MoveType.PHYSICAL, move_range=None,
        confidence=0.95, rationale="Clear.",
    )
    defaults.update(overrides)
    return AttackSemanticResult(**defaults)


RESULT = make_semantic_result()


def save_auto_approved_card(seeded_db_session, make_raw_field, build_and_save_card, raw_attack=BITE):
    raw_field = make_raw_field(raw_attack)
    event = record_llm_run(
        seeded_db_session, raw_field=raw_field, semantic_result=RESULT, actor=get_llm_actor(seeded_db_session),
        prompt_name="classify_attack.jinja2", model_name="gemini-flash-lite-latest",
        confidence_threshold=0.7, decision=ValidationStatus.AUTO_APPROVED,
    )
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=event)
    card_data = build_and_save_card(raw_field, event, raw_attack, RESULT)
    return raw_field, card_data


def save_rejected_attack(seeded_db_session, make_raw_field):
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
