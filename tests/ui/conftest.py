"""
Shared fixtures for ui/ tests.
"""
from unittest.mock import patch

import pytest

from monsterforge.ui.app import app, get_db_session


@pytest.fixture(autouse=True)
def _override_db_session(seeded_db_session):
    """Replace the app's real database dependency with the isolated,
    already-seeded in-memory session for every test in this package —
    autouse so the 41+ existing route tests don't each need to opt in
    individually. Real lifespan()/get_session() are never touched."""
    def _yield_test_session():
        yield seeded_db_session

    app.dependency_overrides[get_db_session] = _yield_test_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _mock_llm_client():
    """record_llm_run() reads get_llm_client().model_name for logging —
    unlike classify_attack() (mocked per test), this is a real call the
    existing tests never anticipated, and it tries to build a real
    GeminiClient requiring a real GEMINI_API_KEY. Autouse so none of the
    41+ existing tests need their own patch for a call they don't
    otherwise care about."""
    with patch("monsterforge.ui.app.get_llm_client") as mock_get_client:
        mock_get_client.return_value.model_name = "test-model"
        yield
