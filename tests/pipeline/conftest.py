"""
Shared fixtures for pipeline/ tests.
"""
import pytest

from monsterforge.db.seed import seed_reference_data


@pytest.fixture
def seeded_db_session(db_session):
    """db_session with the actor/game/site reference rows already seeded.

    Most of pipeline/attack_repository.py's functions need at least one
    of these rows to exist (get_default_game()/get_llm_actor()/
    get_human_actor(), or a game_id/actor_id foreign key) — seeding
    once here instead of repeating the same setup call in every test.
    """
    seed_reference_data(db_session)
    return db_session
