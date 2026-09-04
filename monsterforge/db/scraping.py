"""
The pages table for the db/ package: one row per scraped page.

Populated by the scraping stage, not by MVP 2 itself — a separate
category from db/reference_data.py's lookup tables, since pages is the
first table in the actual pipeline data (raw_fields, structured_data,
etc. all ultimately trace back to a page).
"""

import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from monsterforge.db.base import Base, uuid4_str
from monsterforge.scraping.enums import PageType


# =====================
# PAGE
# =====================
class Page(Base):
    """A single scraped page."""

    __tablename__ = "pages"

    id: Mapped[str] = mapped_column(sa.Text, primary_key=True, default=uuid4_str)
    site_id: Mapped[str] = mapped_column(sa.Text, sa.ForeignKey("sites.id"))
    # NOTE:
    # Not nullable, and not inherited implicitly from site_id: a site
    # could in principle host content for more than one game system, so
    # the game is established explicitly per page.
    game_id: Mapped[str] = mapped_column(sa.Text, sa.ForeignKey("games.id"))
    # Natural key for the "already present" check before every request
    # during scraping.
    url: Mapped[str] = mapped_column(sa.Text, unique=True)
    page_type: Mapped[PageType] = mapped_column(
        sa.Enum(PageType, values_callable=lambda x: [e.value for e in x], native_enum=False)
    )
    html_content: Mapped[str | None] = mapped_column(sa.Text, nullable=True)  # NULL if scraping failed
    status_code: Mapped[int] = mapped_column(sa.Integer)
    scraped_at: Mapped[datetime.datetime] = mapped_column(sa.DateTime)
