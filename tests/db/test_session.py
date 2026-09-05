"""
Tests for db.session: get_engine()/get_session(), create_all_tables(),
enable_foreign_keys().
"""
import datetime
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from monsterforge.db import cards, pipeline, reference_data, scraping
from monsterforge.db import session as db_session_module
from monsterforge.db.base import Base
from monsterforge.db.pipeline import RawField

EXPECTED_TABLES = {
    "games", "sites", "actors", "pages", "raw_fields",
    "classification_events", "structured_data", "cards", "decks",
}


def _reset_engine(monkeypatch):
    """Point get_engine() at a fresh in-memory database instead of the
    real DATABASE_URL, and clear the module-level singleton so a new
    engine is actually built for this test."""
    monkeypatch.setattr(db_session_module, "_engine", None)
    monkeypatch.setattr(db_session_module, "DATABASE_URL", "sqlite:///:memory:")


def test_get_engine_returns_the_same_instance_across_calls(monkeypatch):
    _reset_engine(monkeypatch)

    engine1 = db_session_module.get_engine()
    engine2 = db_session_module.get_engine()

    assert engine1 is engine2


def test_get_session_returns_a_new_session_each_call(monkeypatch):
    _reset_engine(monkeypatch)

    session1 = db_session_module.get_session()
    session2 = db_session_module.get_session()

    assert session1 is not session2
    session1.close()
    session2.close()


def test_create_all_tables_creates_every_table(monkeypatch):
    _reset_engine(monkeypatch)

    db_session_module.create_all_tables()

    inspector = sa.inspect(db_session_module.get_engine())
    assert set(inspector.get_table_names()) == EXPECTED_TABLES


def test_enable_foreign_keys_rejects_an_invalid_foreign_key(monkeypatch):
    """Regression test: SQLite doesn't enforce FK constraints by default —
    without enable_foreign_keys(), this insert would silently succeed."""
    _reset_engine(monkeypatch)
    db_session_module.create_all_tables()

    session = db_session_module.get_session()
    session.add(RawField(
        page_id=None, game_id="does-not-exist", raw_kind="attack",
        name="Bite", fingerprint=str(uuid.uuid4()), data={}, created_at=datetime.datetime(2026, 9, 4),
    ))
    try:
        session.commit()
        assert False, "expected an IntegrityError on an unknown game_id"
    except sa.exc.IntegrityError:
        session.rollback()
    finally:
        session.close()


def test_engine_without_enable_foreign_keys_does_not_enforce_them():
    """Contrast case for the test above: confirms the enforcement really
    comes from enable_foreign_keys(), not from SQLAlchemy/SQLite by
    default — a plain engine with no pragma set lets the same invalid
    insert through."""
    plain_engine = sa.create_engine("sqlite:///:memory:")
    Base.metadata.create_all(plain_engine)
    session = Session(plain_engine)

    session.add(RawField(
        page_id=None, game_id="does-not-exist", raw_kind="attack",
        name="Bite", fingerprint=str(uuid.uuid4()), data={}, created_at=datetime.datetime(2026, 9, 4),
    ))
    session.commit()  # no error: FK enforcement is off without the pragma

    assert session.query(RawField).count() == 1
    session.close()
