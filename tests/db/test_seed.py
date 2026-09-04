"""
Tests for db.seed: seed_reference_data().
"""
from monsterforge.db.reference_data import Actor, Game, Site
from monsterforge.db.seed import (
    D20SRD_BASE_URL,
    D20SRD_SITE_NAME,
    DND_GAME_NAME,
    HUMAN_REVIEWER_ACTOR_NAME,
    LLM_ACTOR_NAME,
    seed_reference_data,
)


def test_seed_reference_data_inserts_the_expected_rows(db_session):
    seed_reference_data(db_session)

    actors = {a.actor_name: a.authority for a in db_session.query(Actor).all()}
    games = [g.name for g in db_session.query(Game).all()]
    sites = [(s.name, s.base_url) for s in db_session.query(Site).all()]

    assert actors == {LLM_ACTOR_NAME: 0, HUMAN_REVIEWER_ACTOR_NAME: 10}
    assert games == [DND_GAME_NAME]
    assert sites == [(D20SRD_SITE_NAME, D20SRD_BASE_URL)]


def test_llm_actor_has_the_lowest_authority(db_session):
    """The LLM's authority must stay lowest so a future conflict-resolution
    rule (higher authority wins) never lets it override a human decision."""
    seed_reference_data(db_session)

    llm_authority = db_session.query(Actor).filter_by(actor_name=LLM_ACTOR_NAME).one().authority
    human_authority = db_session.query(Actor).filter_by(actor_name=HUMAN_REVIEWER_ACTOR_NAME).one().authority

    assert llm_authority < human_authority


def test_seed_reference_data_is_idempotent(db_session):
    seed_reference_data(db_session)
    seed_reference_data(db_session)

    assert db_session.query(Actor).count() == 2
    assert db_session.query(Game).count() == 1
    assert db_session.query(Site).count() == 1
