"""
Engine and session setup for the db/ package.

Provides get_engine()/get_session() as the single source of SQLite
connection/session configuration, create_all_tables() for explicit
table creation, get_db_session() for a request-scoped session any
FastAPI app can depend on, and init_database() for the one-time startup
sequence every such app needs. This project uses no migration tool
(Alembic), so table creation must be triggered deliberately by a caller
(an init/seed script, an app's own startup) rather than happening
implicitly on import.
"""

import sqlalchemy as sa
from sqlalchemy.orm import Session

from monsterforge.config.db_settings import DATABASE_URL
from monsterforge.db.base import Base
from monsterforge.db.seed import seed_reference_data

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


def get_db_session():
    """FastAPI dependency: yields a session scoped to one request, always
    closed afterward. Not specific to any one app -- ui/app.py and
    api/app.py both depend on it, the same way both depend on the schema
    itself, rather than either importing it from the other. Overridden
    in tests (tests/ui/conftest.py) to yield an isolated in-memory
    session instead of the real database."""
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def init_database() -> None:
    """Create every table and seed reference rows once, at process
    startup -- called from both ui/app.py's and api/app.py's own
    lifespan(). Each FastAPI app starts up independently, but both need
    this identical two-step sequence, so it lives here once rather than
    being copied into each app's lifespan body."""
    create_all_tables()
    session = get_session()
    try:
        seed_reference_data(session)
    finally:
        session.close()
