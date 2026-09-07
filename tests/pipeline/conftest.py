"""
Shared fixtures for tests/pipeline/: a couple of sample raw attacks and
factory fixtures for the setup sequence ("build a raw_field", "build and
save a card for one") that most repository tests need, regardless of
whether they're exercising the write side (test_attack_repository.py)
or the read side (test_attack_repository_queries.py).

Promoted here from test_attack_repository.py once a second test file
needed the same helpers -- previously make_raw_field()/build_and_save_card()
were private (_make_raw_field()/_build_and_save_card()) to that one
file. A leading underscore signals "used only within this module"; once
a second real caller exists, the function is promoted (underscore
dropped) rather than imported across files under its private name or
duplicated in the new caller's module.
"""
import json

import pytest

from monsterforge.db.enums import CardType
from monsterforge.llm.semantic_classification.attacks import SemanticContextInput
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import raw_to_structured_attack
from monsterforge.pipeline.attack_repository import (
    compute_fingerprint,
    get_default_game,
    get_or_create_raw_field,
    save_card,
    save_structured_data,
)
from monsterforge.serialization.domain_to_json import card_to_json
from monsterforge.transformation.dnd.v3x.converters.attacks_converter import attack_converter

EMPTY_CONTEXT = SemanticContextInput(additional_description=None, creature_description=None, creature_subtype=None)
BITE = RawAttack(name="Bite", modifier="+7", attack_type="melee", attack_effect="1d6+3")
CLAW = RawAttack(name="Claw", modifier="+7", attack_type="melee", attack_effect="1d4+3")


@pytest.fixture
def make_raw_field(seeded_db_session):
    """Factory: get_or_create_raw_field() for `raw_attack`/`context`,
    computing the fingerprint automatically -- the setup sequence nearly
    every test in this package needs at least once."""
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
    pipeline.attack_repository's own callers (ui/app.py) go through."""
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
