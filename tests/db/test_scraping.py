"""
Tests for db.scraping: Page.
"""
import datetime

import sqlalchemy as sa

from monsterforge.db.reference_data import Game, Site
from monsterforge.db.scraping import Page
from monsterforge.scraping.enums import PageType


def _make_game_and_site(db_session):
    game = Game(name="D&D 3.x")
    site = Site(name="d20srd.org", base_url="https://www.d20srd.org")
    db_session.add_all([game, site])
    db_session.commit()
    return game, site


def test_page_round_trips_with_a_valid_site_and_game(db_session):
    game, site = _make_game_and_site(db_session)

    page = Page(
        site_id=site.id,
        game_id=game.id,
        url="https://www.d20srd.org/srd/monsters/wolf.htm",
        page_type=PageType.MONSTER,
        html_content="<html></html>",
        status_code=200,
        scraped_at=datetime.datetime(2026, 9, 4),
    )
    db_session.add(page)
    db_session.commit()

    result = db_session.query(Page).one()

    assert result.url == "https://www.d20srd.org/srd/monsters/wolf.htm"
    assert result.page_type == PageType.MONSTER
    assert result.status_code == 200


def test_page_html_content_is_nullable_for_a_failed_scrape(db_session):
    game, site = _make_game_and_site(db_session)

    page = Page(
        site_id=site.id,
        game_id=game.id,
        url="https://www.d20srd.org/srd/monsters/does-not-exist.htm",
        page_type=PageType.MONSTER,
        html_content=None,
        status_code=404,
        scraped_at=datetime.datetime(2026, 9, 4),
    )
    db_session.add(page)
    db_session.commit()

    result = db_session.query(Page).one()

    assert result.html_content is None


def test_page_type_is_stored_as_its_string_value_not_its_enum_name(db_session):
    """The values_callable configuration must store "monster", not "MONSTER" —
    reading the raw column value (not through the ORM's enum coercion)
    confirms this."""
    game, site = _make_game_and_site(db_session)

    page = Page(
        site_id=site.id,
        game_id=game.id,
        url="https://www.d20srd.org/srd/monsters/wolf.htm",
        page_type=PageType.MONSTER,
        status_code=200,
        scraped_at=datetime.datetime(2026, 9, 4),
    )
    db_session.add(page)
    db_session.commit()

    raw_value = db_session.execute(sa.text("SELECT page_type FROM pages")).scalar_one()

    assert raw_value == "monster"


def test_page_url_must_be_unique(db_session):
    game, site = _make_game_and_site(db_session)
    url = "https://www.d20srd.org/srd/monsters/wolf.htm"
    db_session.add(Page(
        site_id=site.id, game_id=game.id, url=url,
        page_type=PageType.MONSTER, status_code=200,
        scraped_at=datetime.datetime(2026, 9, 4),
    ))
    db_session.commit()

    db_session.add(Page(
        site_id=site.id, game_id=game.id, url=url,
        page_type=PageType.MONSTER, status_code=200,
        scraped_at=datetime.datetime(2026, 9, 4),
    ))
    try:
        db_session.commit()
        assert False, "expected an IntegrityError on duplicate url"
    except sa.exc.IntegrityError:
        db_session.rollback()


def test_page_rejects_an_unknown_site_id(db_session):
    game, _site = _make_game_and_site(db_session)

    db_session.add(Page(
        site_id="does-not-exist", game_id=game.id,
        url="https://www.d20srd.org/srd/monsters/wolf.htm",
        page_type=PageType.MONSTER, status_code=200,
        scraped_at=datetime.datetime(2026, 9, 4),
    ))
    try:
        db_session.commit()
        assert False, "expected an IntegrityError on an unknown site_id"
    except sa.exc.IntegrityError:
        db_session.rollback()
