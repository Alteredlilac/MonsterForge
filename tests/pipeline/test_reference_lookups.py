"""
Tests for pipeline.reference_lookups.
"""
from monsterforge.pipeline.reference_lookups import get_default_game, get_human_actor, get_llm_actor


def test_get_default_game_returns_the_seeded_dnd_row(seeded_db_session):
    assert get_default_game(seeded_db_session).name == "D&D 3.x"


def test_get_llm_actor_returns_the_seeded_llm_row(seeded_db_session):
    assert get_llm_actor(seeded_db_session).actor_name == "llm"


def test_get_human_actor_returns_the_seeded_human_row(seeded_db_session):
    assert get_human_actor(seeded_db_session).actor_name == "human_reviewer"
