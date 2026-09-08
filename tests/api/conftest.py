"""
Shared fixtures for tests/api/: a TestClient bound to api.app.app --
not ui.app.app, a separate application (see monsterforge/api/app.py) --
with the same per-test database override and LLM-client mock
tests/ui/conftest.py uses for its own, independent app.
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from monsterforge.api.app import app
from monsterforge.db.session import get_db_session

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
    identical fixture for ui.routes.convert/review."""
    with patch("monsterforge.api.routes.get_llm_client") as mock_get_client:
        mock_get_client.return_value.model_name = "test-model"
        yield
