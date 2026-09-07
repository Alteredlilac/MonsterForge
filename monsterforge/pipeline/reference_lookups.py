"""
Lookups for this project's seeded reference-data rows: the current
game and the two fixed actors (the LLM, the human reviewer) every
classification event is attributed to.

Split out of pipeline/attack_repository.py: these three functions
answer a different domain question ("what is the row for this seeded
name?") than either the write-path functions there (record a new
event/row) or the read-only queries in pipeline/attack_repository_queries.py
(what has already been saved for this attack?). They're also not
specific to attacks at all — any future MoveCard source (talents,
spells) would call them identically, since they only ever look up
Game/Actor rows, never anything attack-shaped.
"""
from sqlalchemy.orm import Session

from monsterforge.db.reference_data import Actor, Game
from monsterforge.db.seed import DND_GAME_NAME, HUMAN_REVIEWER_ACTOR_NAME, LLM_ACTOR_NAME


def get_default_game(session: Session) -> Game:
    """Return the seeded D&D 3.x game row (see db/seed.py)."""
    return session.query(Game).filter_by(name=DND_GAME_NAME).one()


def get_llm_actor(session: Session) -> Actor:
    """Return the seeded actor row representing the LLM (see db/seed.py)."""
    return session.query(Actor).filter_by(actor_name=LLM_ACTOR_NAME).one()


def get_human_actor(session: Session) -> Actor:
    """Return the seeded actor row representing the human reviewer (see db/seed.py)."""
    return session.query(Actor).filter_by(actor_name=HUMAN_REVIEWER_ACTOR_NAME).one()
