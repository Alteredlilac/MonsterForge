"""
Tests for api/demo_seed.py::seed_demo_cards().

No LLM mocking needed here (unlike tests/api/test_creation.py): the
whole point of this module is that it never calls classify_attack() at
all -- if it did, these tests would fail outright without a mock,
since seeded_db_session/the test environment has no real GEMINI_API_KEY.
"""
from monsterforge.api.demo_seed import seed_demo_cards
from monsterforge.entrypoints.api_demo_seed_data import DEMO_SEED_ATTACKS
from monsterforge.pipeline.attack_repository_queries import list_saved_cards
from tests.api.conftest import client


def test_seed_demo_cards_populates_every_entry(seeded_db_session):
    seed_demo_cards(seeded_db_session)

    entries = list_saved_cards(seeded_db_session)

    assert len(entries) == len(DEMO_SEED_ATTACKS)
    seeded_names = {entry["name"] for entry in entries}
    expected_names = {attack["case"]["name"] for attack in DEMO_SEED_ATTACKS}
    assert seeded_names == expected_names


def test_seed_demo_cards_is_idempotent(seeded_db_session):
    """get_or_create_raw_field()'s own fingerprint lookup means a
    second run must find every entry already active and skip it --
    the same property that makes this safe to call on every process
    restart, whether or not the disk actually survived it."""
    seed_demo_cards(seeded_db_session)
    seed_demo_cards(seeded_db_session)

    entries = list_saved_cards(seeded_db_session)

    assert len(entries) == len(DEMO_SEED_ATTACKS)


def test_seed_demo_cards_preserves_a_secondary_effect_card(seeded_db_session):
    """Tentacle's "plus slime" secondary effect must survive the
    replay -- a real check that raw_to_structured_attack()/
    attack_converter() are actually doing the full conversion, not
    just building a bare damage card."""
    seed_demo_cards(seeded_db_session)

    entries = list_saved_cards(seeded_db_session)
    tentacle = next(entry for entry in entries if entry["name"] == "Tentacle")

    assert [card["name"] for card in tentacle["move_card"]["cards_to_add"]] == ["Slime"]


def test_seed_demo_cards_data_is_visible_through_get_api_cards(seeded_db_session):
    seed_demo_cards(seeded_db_session)

    response = client.get("/api/cards")

    assert response.status_code == 200
    assert len(response.json()) == len(DEMO_SEED_ATTACKS)
