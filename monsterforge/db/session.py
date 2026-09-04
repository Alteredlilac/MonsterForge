"""
Engine and session setup for the db/ package.

Provides get_engine()/get_session() as the single source of SQLite
connection/session configuration, plus create_all_tables() for explicit
table creation. This project uses no migration tool (Alembic), so table
creation must be triggered deliberately by a caller (an init/seed
script) rather than happening implicitly on import.
"""

import sqlalchemy as sa
from sqlalchemy.orm import Session

from monsterforge.config.db_settings import DATABASE_URL
from monsterforge.db.base import Base

# Importing these registers every model class on Base.metadata, so a
# caller only needs to import db.session (not each model module
# individually) for create_all_tables() to know about every table.
from monsterforge.db import cards, pipeline, reference_data, scraping

# NOTE:
# Same lazily-built shared-singleton pattern as llm/client.py's
# get_llm_client(): one Engine (and its connection pool) for the whole
# process, not rebuilt per call. Unlike the engine, get_session() below
# deliberately does NOT reuse a singleton — a Session is meant to be
# short-lived, scoped to one unit of work (a script run, a request), not
# held open and shared across unrelated operations.
_engine: sa.Engine | None = None


def enable_foreign_keys(engine: sa.Engine) -> None:
    """Turn on SQLite's foreign-key constraint enforcement for this engine.

    SQLite disables FK enforcement by default (a SQLite engine quirk,
    not a SQLAlchemy default) — without this, an invalid foreign key
    value inserts silently instead of raising, producing orphaned rows
    instead of a loud failure at insert time. Public, not a leading-
    underscore helper: tests that build their own in-memory engine call
    this too, to exercise the same enforcement the real engine has.
    """
    @sa.event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_engine() -> sa.Engine:
    """Return the shared SQLAlchemy engine, creating it on first call."""
    global _engine

    if _engine is None:
        _engine = sa.create_engine(DATABASE_URL)
        enable_foreign_keys(_engine)

    return _engine


def get_session() -> Session:
    """Return a new SQLAlchemy session bound to the shared engine."""
    return Session(get_engine())


def create_all_tables() -> None:
    """Create every table registered on Base.metadata that doesn't already exist.

    Explicit, not automatic on import: with no migration tool in this
    project, a caller (an init script, a seed script) must invoke this
    deliberately rather than tables appearing as a side effect of
    importing db.session.
    """
    Base.metadata.create_all(get_engine())
