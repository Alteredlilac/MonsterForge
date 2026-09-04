"""
Seed data for the db/ package's reference/lookup tables.

Populates the rows the rest of the schema depends on: an actor row for
the LLM and for this project's one human reviewer, the D&D 3.x game
row, and the d20srd.org site row. Idempotent — checks for an existing
row by its natural lookup value before inserting, so it's safe to call
more than once (e.g. on every app startup) without producing duplicates.
"""

from sqlalchemy.orm import Session

from monsterforge.db.reference_data import Actor, Game, Site

LLM_ACTOR_NAME = "llm"
HUMAN_REVIEWER_ACTOR_NAME = "human_reviewer"
DND_GAME_NAME = "D&D 3.x"
D20SRD_SITE_NAME = "d20srd.org"
D20SRD_BASE_URL = "https://www.d20srd.org"


def seed_reference_data(session: Session) -> None:
    """Insert the actors/games/sites rows this schema depends on, if not already present."""
    # NOTE:
    # authority=0/10 here matches the two real rows described in
    # db/reference_data.py's Actor.authority NOTE — the LLM always
    # lowest, the human operator chosen high on purpose to leave room
    # for future intermediate reviewer levels.
    _seed_actor(session, actor_name=LLM_ACTOR_NAME, authority=0)
    _seed_actor(session, actor_name=HUMAN_REVIEWER_ACTOR_NAME, authority=10)
    _seed_game(session, name=DND_GAME_NAME, version="3.5")
    _seed_site(session, name=D20SRD_SITE_NAME, base_url=D20SRD_BASE_URL)
    session.commit()


def _seed_actor(session: Session, *, actor_name: str, authority: int) -> None:
    existing = session.query(Actor).filter_by(actor_name=actor_name).first()
    if existing is None:
        session.add(Actor(actor_name=actor_name, authority=authority))


def _seed_game(session: Session, *, name: str, version: str | None) -> None:
    existing = session.query(Game).filter_by(name=name).first()
    if existing is None:
        session.add(Game(name=name, version=version))


def _seed_site(session: Session, *, name: str, base_url: str) -> None:
    existing = session.query(Site).filter_by(name=name).first()
    if existing is None:
        session.add(Site(name=name, base_url=base_url))
