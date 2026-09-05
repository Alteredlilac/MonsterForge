"""
Shared fixtures used across more than one test package.
"""
import sqlalchemy as sa
import pytest
from sqlalchemy.orm import Session

from monsterforge.db.base import Base
from monsterforge.db import cards, pipeline, reference_data, scraping
from monsterforge.db.session import enable_foreign_keys


@pytest.fixture
def db_session():
    """A fresh in-memory SQLite session, FK enforcement on, every table created.

    Isolated per test — a new engine/database each call, not the shared
    process-level engine from db.session.get_engine(). Used by both
    tests/db/ and tests/pipeline/, hence living at the project root
    rather than duplicated in either package's own conftest.py.
    """
    engine = sa.create_engine("sqlite:///:memory:")
    enable_foreign_keys(engine)
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
