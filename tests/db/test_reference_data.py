"""
Tests for db.reference_data: Game, Site, Actor.
"""
from monsterforge.db.reference_data import Actor, Game, Site


def test_game_round_trips_with_required_and_optional_fields(db_session):
    db_session.add(Game(name="D&D 3.x", version="3.5", data={"language": "en"}))
    db_session.commit()

    result = db_session.query(Game).one()

    assert result.name == "D&D 3.x"
    assert result.version == "3.5"
    assert result.data == {"language": "en"}
    assert result.id is not None


def test_game_version_and_data_default_to_none(db_session):
    db_session.add(Game(name="D&D 3.x"))
    db_session.commit()

    result = db_session.query(Game).one()

    assert result.version is None
    assert result.data is None


def test_site_round_trips_with_required_and_optional_fields(db_session):
    db_session.add(Site(name="d20srd.org", base_url="https://www.d20srd.org", scraping_config={"delay": 1}))
    db_session.commit()

    result = db_session.query(Site).one()

    assert result.name == "d20srd.org"
    assert result.base_url == "https://www.d20srd.org"
    assert result.scraping_config == {"delay": 1}


def test_site_scraping_config_defaults_to_none(db_session):
    db_session.add(Site(name="d20srd.org", base_url="https://www.d20srd.org"))
    db_session.commit()

    result = db_session.query(Site).one()

    assert result.scraping_config is None


def test_actor_round_trips_with_authority(db_session):
    db_session.add(Actor(actor_name="llm", authority=0, actor_data={"provider": "gemini"}))
    db_session.commit()

    result = db_session.query(Actor).one()

    assert result.actor_name == "llm"
    assert result.authority == 0
    assert result.actor_data == {"provider": "gemini"}
