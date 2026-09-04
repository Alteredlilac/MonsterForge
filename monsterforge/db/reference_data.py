"""
Reference/lookup tables for the db/ package: games, sites, actors.

These three tables share one category, distinct from the append-only
event pipeline (db/pipeline.py) and its scraped input (db/scraping.py):
each normalizes a piece of information that would otherwise repeat on
every row of a downstream table (game/edition, scraping source, and who
or what produced a classification event), the same normalization
rationale for all three.
"""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from monsterforge.db.base import Base, uuid4_str


# =====================
# GAME
# =====================
class Game(Base):
    """A game system/edition (e.g. D&D 3.x, Pathfinder 1E)."""

    __tablename__ = "games"

    id: Mapped[str] = mapped_column(sa.Text, primary_key=True, default=uuid4_str)
    name: Mapped[str] = mapped_column(sa.Text)
    # NOTE:
    # Not a numeric type: some systems have a numeric version ("3.5"),
    # others a proper name ("Advanced", "Revised"), others none at all.
    # Any numeric comparison, if ever needed, happens in Python when it's
    # needed, not in the column type.
    version: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    data: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)


# =====================
# SITE
# =====================
class Site(Base):
    """A scraping source site (e.g. d20srd.org)."""

    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(sa.Text, primary_key=True, default=uuid4_str)
    name: Mapped[str] = mapped_column(sa.Text)
    base_url: Mapped[str] = mapped_column(sa.Text)
    # NOTE:
    # Stays NULL as long as only one site (d20srd.org) is scraped, with
    # request delay/User-Agent/base-URL override kept as flat constants
    # in config/scraping_settings.py instead. Reserved here from the
    # start rather than added later because this project deliberately
    # excludes schema migrations (Alembic) — adding a column once a
    # second site actually needed one wouldn't be free. If/when that
    # second site arrives, those values move here, per-site, instead of
    # staying global constants.
    scraping_config: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)


# =====================
# ACTOR
# =====================
class Actor(Base):
    """Who or what produces a classification_events row (an LLM run counts too)."""

    __tablename__ = "actors"

    id: Mapped[str] = mapped_column(sa.Text, primary_key=True, default=uuid4_str)
    actor_name: Mapped[str] = mapped_column(sa.Text)
    # NOTE:
    # Plain integer, not an enum: used for numeric comparisons between
    # authority levels to resolve conflicting classifications (higher
    # wins), a future feature this column reserves space for now rather
    # than a closed vocabulary. Today only two rows exist for real: the
    # LLM itself (authority=0, always lowest) and the project's one human
    # operator (authority=10, chosen high on purpose to leave room for
    # future intermediate levels — e.g. base reviewer=1, editor=2, senior
    # editor=3 — without renumbering anything). No conflict-resolution
    # logic reads this column yet — with a single human actor, there's no
    # real conflict to resolve today.
    authority: Mapped[int] = mapped_column(sa.Integer)
    actor_data: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
