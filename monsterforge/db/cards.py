"""
The final-output tables for the db/ package: cards, decks.

Distinct from db/pipeline.py's conversion stages: this is what the
pipeline actually produces — individual cards, and the full entity
("deck") they compose into.
"""

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from monsterforge.db.base import Base, uuid4_str
from monsterforge.db.enums import CardType


# =====================
# CARD
# =====================
class Card(Base):
    """A single generated card (one of domain/entity.py's three card kinds)."""

    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(sa.Text, primary_key=True, default=uuid4_str)
    structured_data_id: Mapped[str] = mapped_column(sa.Text, sa.ForeignKey("structured_data.id"))
    card_type: Mapped[CardType] = mapped_column(
        sa.Enum(CardType, values_callable=lambda x: [e.value for e in x], native_enum=False)
    )
    # Promoted from the content blob below — every domain Card already
    # has its own name field (domain/cards.py::Card.name).
    name: Mapped[str] = mapped_column(sa.Text)
    content: Mapped[dict] = mapped_column(sa.JSON)  # JSON or HTML


# =====================
# DECK
# =====================
class Deck(Base):
    """A full domain.Entity — the complete unit of play (a monster or
    character), composed of creature/move/item cards together.

    No junction table to cards: caching a classification by fingerprint
    (planned for MVP 2) avoids redundant LLM calls, it doesn't mean two
    Entity rows should share one cards row — every conversion still
    produces its own domain object with its own id. Unlike Card, there's
    no single structured_data_id equivalent here: an Entity is assembled
    from *multiple* structured_data rows together (one Creature plus
    several Attack/Item rows), not from just one.
    """

    __tablename__ = "decks"

    id: Mapped[str] = mapped_column(sa.Text, primary_key=True, default=uuid4_str)
    # NOTE:
    # domain.Entity has no name field of its own (only
    # entity_description and the base_form property), so this is
    # promoted from the base creature card's name inside the data blob
    # below — lets a deck be looked up directly (e.g. "give me the Red
    # Dragon deck") without parsing JSON.
    name: Mapped[str] = mapped_column(sa.Text)
    # NOTE:
    # entity_description plus creature_cards/move_cards/item_cards
    # nested as {name, id} references, not duplicated content — same
    # behavior domain_to_json.py's DomainJSONEncoder already establishes:
    # every Card encountered while recursing reduces to {"name": ...,
    # "id": ...}, never its full content.
    data: Mapped[dict] = mapped_column(sa.JSON)


# NOTE:
# No game_id on either table: cards/decks are domain-model concepts,
# deliberately source-agnostic — domain/ never carries system-specific
# fields, the same reason it isn't nested per system/version the way
# structured_data/rules/transformation are. Traceability back to the
# source game isn't lost — the card ids inside a deck's data blob let it
# be reconstructed (cards.id -> cards.structured_data_id ->
# structured_data.raw_field_id -> raw_fields.game_id) — just not
# enforced by a direct foreign key.
