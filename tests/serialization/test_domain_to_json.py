"""
Tests for serialization/domain_to_json.py.

Covers:
- card_to_json() fully expands the root card's own fields (regression:
  DomainJSONEncoder checked isinstance(obj, Card) before is_dataclass(obj),
  so MoveCard — a Card subclass — collapsed to just {name, id} even when
  it was the explicit target of serialization)
- Card instances nested inside another structure (cards_to_add, or an
  Entity's move_cards) still correctly reduce to {name, id} — that part
  of the original behavior is intentional and must not regress
- Enum -> .value and UUID -> str encoding
"""
import json
import uuid
from monsterforge.domain.moves import MoveCard, MoveEffect
from monsterforge.domain.entity import Entity
from monsterforge.domain.enums import (
    MoveType, MoveCategory, MoveMode, EffectType, Target, Resource,
    Duration, Usage, DamageType, AffectedAttribute,
)
from monsterforge.serialization.domain_to_json import card_to_json, domain_entity_to_json


def make_move_card(**overrides):
    defaults = dict(
        name="Bite",
        description="A sharp bite.",
        move_type=MoveType.PHYSICAL,
        category=MoveCategory.ATTACK,
        mode=MoveMode.ACTIVE,
        effect=EffectType.DAMAGE,
        move_effects=[MoveEffect(damage_type=DamageType.PHYSICAL, effect_value=3)],
        target=Target.SINGLE,
        resource=Resource.STAMINA,
        duration=Duration.INSTANT,
        usage=Usage.UNLIMITED,
    )
    defaults.update(overrides)
    return MoveCard(**defaults)


def test_card_to_json_expands_all_fields_of_the_root():
    card = make_move_card()

    data = json.loads(card_to_json(card))

    assert data["name"] == "Bite"
    assert data["move_type"] == "physical"
    assert data["category"] == "attack"
    assert data["resource"] == "stamina"
    assert data["move_effects"][0]["effect_value"] == 3
    assert data["id"] == str(card.id)


def test_card_to_json_reduces_a_nested_card_to_a_reference():
    trip = make_move_card(name="Trip")
    bite = make_move_card(cards_to_add=[trip])

    data = json.loads(card_to_json(bite))

    assert data["cards_to_add"] == [{"name": "Trip", "id": str(trip.id)}]


def test_domain_entity_to_json_still_reduces_nested_move_cards():
    """Non-regression: Entity serialization was never affected by the
    card_to_json() fix and must keep collapsing its cards to references,
    to avoid huge/confusing entity payloads."""
    bite = make_move_card()
    entity = Entity(move_cards=[bite])

    data = json.loads(domain_entity_to_json(entity))

    assert data["move_cards"] == [{"name": "Bite", "id": str(bite.id)}]
    assert data["base_form"] is None


def test_card_to_json_encodes_enums_as_their_value():
    card = make_move_card(move_type=MoveType.MAGICAL)

    data = json.loads(card_to_json(card))

    assert data["move_type"] == "magical"


def test_card_to_json_encodes_uuid_as_string():
    card = make_move_card()

    data = json.loads(card_to_json(card))

    assert isinstance(data["id"], str)
    assert uuid.UUID(data["id"]) == card.id
