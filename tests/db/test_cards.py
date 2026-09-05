"""
Tests for db.cards: Card, Deck.
"""
import datetime
import uuid

import sqlalchemy as sa

from monsterforge.db.cards import Card, Deck
from monsterforge.db.enums import CardType, EntityType, EventStatus, EventType
from monsterforge.db.pipeline import ClassificationEvent, RawField, StructuredData
from monsterforge.db.reference_data import Actor, Game
from monsterforge.validation.enums import ValidationStatus


def _make_structured_data(db_session):
    game = Game(name="D&D 3.x")
    actor = Actor(actor_name="llm", authority=0)
    db_session.add_all([game, actor])
    db_session.commit()

    raw_field = RawField(
        page_id=None, game_id=game.id, raw_kind="attack", name="Bite",
        fingerprint=str(uuid.uuid4()), data={}, created_at=datetime.datetime(2026, 9, 4),
    )
    db_session.add(raw_field)
    db_session.commit()

    event = ClassificationEvent(
        raw_field_id=raw_field.id, event_type=EventType.LLM_RUN, result={},
        actor_id=actor.id, decision=ValidationStatus.AUTO_APPROVED,
        status=EventStatus.ACTIVE, created_at=datetime.datetime(2026, 9, 4),
    )
    db_session.add(event)
    db_session.commit()

    structured = StructuredData(
        raw_field_id=raw_field.id, classification_event_id=event.id,
        entity_type=EntityType.ATTACK, name="Bite", data={},
    )
    db_session.add(structured)
    db_session.commit()
    return structured


def test_card_round_trips_with_a_valid_structured_data(db_session):
    structured = _make_structured_data(db_session)

    card = Card(
        structured_data_id=structured.id,
        card_type=CardType.MOVE_CARD,
        name="Bite",
        content={"move_type": "physical", "description": "A vicious bite."},
    )
    db_session.add(card)
    db_session.commit()

    result = db_session.query(Card).one()
    assert result.card_type == CardType.MOVE_CARD
    assert result.name == "Bite"
    assert result.content["description"] == "A vicious bite."


def test_card_rejects_an_unknown_structured_data_id(db_session):
    db_session.add(Card(
        structured_data_id="does-not-exist",
        card_type=CardType.MOVE_CARD,
        name="Bite",
        content={},
    ))
    try:
        db_session.commit()
        assert False, "expected an IntegrityError on an unknown structured_data_id"
    except sa.exc.IntegrityError:
        db_session.rollback()


def test_deck_round_trip(db_session):
    """A deck's data blob holds {name, id} references to its cards, not
    full card content — no junction table, no FK to enforce here."""
    deck = Deck(
        name="Red Dragon",
        data={
            "entity_description": "A fearsome adult red dragon.",
            "creature_cards": [{"name": "Red Dragon", "id": "abc-123"}],
            "move_cards": [{"name": "Bite", "id": "def-456"}],
            "item_cards": [],
        },
    )
    db_session.add(deck)
    db_session.commit()

    result = db_session.query(Deck).one()
    assert result.name == "Red Dragon"
    assert result.data["move_cards"] == [{"name": "Bite", "id": "def-456"}]
