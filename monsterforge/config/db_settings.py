"""
Configuration for the SQLite database connection (db/session.py).

Plain module-level constants, not a rules/ table: these are runtime
deployment configuration, not static game data.
"""

from pathlib import Path

# NOTE:
# Resolved relative to this file, not the current working directory, so
# the database path is stable regardless of where a script/entrypoint is
# invoked from. Three parents up from monsterforge/config/db_settings.py
# is the repository root, matching where .env.example already lives.
DATABASE_PATH: Path = Path(__file__).resolve().parent.parent.parent / "monsterforge.db"
DATABASE_URL: str = f"sqlite:///{DATABASE_PATH}"
