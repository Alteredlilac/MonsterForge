"""
FastAPI dependency for a per-request database session.

Split out of ui/app.py so ui/routes/ can depend on it without creating
a circular import: every route needs Depends(get_db_session), but
app.py also needs to import the route modules to register them --
keeping this function in app.py itself would make that a cycle.
"""
from monsterforge.db.session import get_session


def get_db_session():
    """FastAPI dependency: yields a session scoped to one request, always
    closed afterward. Overridden in tests (tests/ui/conftest.py) to
    yield an isolated in-memory session instead of the real database."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()
