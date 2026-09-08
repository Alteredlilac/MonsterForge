"""
Shared fixtures for tests/api/: a TestClient bound to api.app.app --
not ui.app.app, a separate application (see monsterforge/api/app.py) --
with the same per-test database override tests/ui/conftest.py uses for
its own, independent app.
"""
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
