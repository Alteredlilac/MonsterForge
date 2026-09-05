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
    """
    engine = sa.create_engine("sqlite:///:memory:")
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
