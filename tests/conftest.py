"""
Shared fixtures used across more than one test package.
"""
import sqlalchemy as sa
import pytest
from sqlalchemy.orm import Session

from monsterforge.db.base import Base
from monsterforge.db import cards, pipeline, reference_data, scraping
from monsterforge.db.seed import seed_reference_data
from monsterforge.db.session import enable_foreign_keys


@pytest.fixture
def db_session():
    """A fresh in-memory SQLite session, FK enforcement on, every table created.

    Isolated per test — a new engine/database each call, not the shared
    process-level engine from db.session.get_engine(). Used by
    tests/db/, tests/pipeline/, and tests/ui/, hence living at the
    project root rather than duplicated in any one package's conftest.

    check_same_thread=False + StaticPool: FastAPI's TestClient
    (tests/ui/) runs route handlers in a different OS thread than the
    test itself. check_same_thread=False alone isn't enough — SQLite's
    default pool for a ":memory:" URL (SingletonThreadPool) hands out a
    separate connection per thread, and each ":memory:" connection is
    its own empty database, so the route's thread would see a
    completely different, unseeded database than the one this fixture
    just set up. StaticPool forces a single shared connection for the
    whole engine regardless of which thread asks for it — the standard
    pairing for this exact FastAPI+SQLAlchemy+TestClient combination.
    """
    engine = sa.create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=sa.pool.StaticPool,
    )
    enable_foreign_keys(engine)
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


@pytest.fixture
def seeded_db_session(db_session):
    """db_session with the actor/game/site reference rows already seeded.

    Most repository-level code needs at least one of these rows to
    exist (get_default_game()/get_llm_actor()/get_human_actor(), or a
    game_id/actor_id foreign key) — seeding once here instead of
    repeating the same setup call in every test. Used by both
    tests/pipeline/ and tests/ui/, hence living at the project root.
    """
    seed_reference_data(db_session)
    return db_session
