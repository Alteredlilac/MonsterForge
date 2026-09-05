"""
Shared fixtures for ui/ tests.
"""
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
