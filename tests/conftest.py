"""
Shared fixtures used across more than one test package.

make_raw_field()/build_and_save_card() were promoted here from
tests/pipeline/conftest.py once a third package (tests/api/) needed the
same setup sequence a saved, active card requires -- previously shared
only between tests/pipeline/'s own two test files. Same promotion
pattern already used to get them there in the first place: the most
local conftest.py that covers everywhere a fixture is needed, moved up
one level each time a wider consumer appears.
"""
import json

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from monsterforge.db import cards, pipeline, reference_data, scraping
from monsterforge.db.base import Base
from monsterforge.db.enums import CardType
from monsterforge.db.seed import seed_reference_data
from monsterforge.db.session import enable_foreign_keys
from monsterforge.llm.semantic_classification.attacks import SemanticContextInput
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import raw_to_structured_attack
from monsterforge.pipeline.attack_repository import (
    compute_fingerprint,
    get_or_create_raw_field,
    save_card,
    save_structured_data,
)
from monsterforge.pipeline.reference_lookups import get_default_game
from monsterforge.serialization.domain_to_json import card_to_json
from monsterforge.transformation.dnd.v3x.converters.attacks_converter import attack_converter

EMPTY_CONTEXT = SemanticContextInput(additional_description=None, creature_description=None, creature_subtype=None)
BITE = RawAttack(name="Bite", modifier="+7", attack_type="melee", attack_effect="1d6+3")
CLAW = RawAttack(name="Claw", modifier="+7", attack_type="melee", attack_effect="1d4+3")


@pytest.fixture
def db_session():
    """A fresh in-memory SQLite session, FK enforcement on, every table created.

    Isolated per test — a new engine/database each call, not the shared
    process-level engine from db.session.get_engine(). Used by
    tests/db/, tests/pipeline/, tests/api/, and tests/ui/, hence living
    at the project root rather than duplicated in any one package's
    conftest.

    check_same_thread=False + StaticPool: FastAPI's TestClient
    (tests/ui/, tests/api/) runs route handlers in a different OS thread
    than the test itself. check_same_thread=False alone isn't enough —
    SQLite's default pool for a ":memory:" URL (SingletonThreadPool)
    hands out a separate connection per thread, and each ":memory:"
    connection is its own empty database, so the route's thread would
    see a completely different, unseeded database than the one this
    fixture just set up. StaticPool forces a single shared connection
    for the whole engine regardless of which thread asks for it — the
    standard pairing for this exact FastAPI+SQLAlchemy+TestClient
    combination.
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
    repeating the same setup call in every test. Used by tests/pipeline/,
    tests/api/, and tests/ui/, hence living at the project root.
    """
    seed_reference_data(db_session)
    return db_session


@pytest.fixture
def make_raw_field(seeded_db_session):
    """Factory: get_or_create_raw_field() for `raw_attack`/`context`,
    computing the fingerprint automatically -- the setup sequence nearly
    every test needing a raw_field needs at least once."""
    def _make(raw_attack=BITE, context=EMPTY_CONTEXT):
        fingerprint = compute_fingerprint(raw_attack, context.creature_subtype, None)
        return get_or_create_raw_field(
            seeded_db_session, game_id=get_default_game(seeded_db_session).id, raw_attack=raw_attack,
            semantic_context=context, fingerprint=fingerprint,
        )
    return _make


@pytest.fixture
def build_and_save_card(seeded_db_session):
    """Factory: build the domain MoveCard for `raw_attack`/`result` and
    persist it as structured_data + cards for `event`, returning the
    already-serialized card dict -- the same three-call sequence
    pipeline.attack_repository's own callers (ui/routes/convert.py,
    ui/routes/review.py, api/creation.py) go through."""
    def _build(raw_field, event, raw_attack, result):
        structured_attack = raw_to_structured_attack(raw_attack, result)
        move_card = attack_converter(structured_attack)
        card_data = json.loads(card_to_json(move_card))
        structured_data = save_structured_data(
            seeded_db_session, raw_field=raw_field, classification_event=event, structured_attack=structured_attack,
        )
        save_card(seeded_db_session, structured_data=structured_data, card_data=card_data, card_type=CardType.MOVE_CARD)
        return card_data
    return _build
