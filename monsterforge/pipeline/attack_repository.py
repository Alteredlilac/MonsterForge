"""
Persistence operations for the Attack classification pipeline.

Sits alongside attack_pipeline.py, not inside db/: db/ defines the
schema (tables, columns, relationships), this module is the
access/orchestration logic that uses it, the same split already
established between rules/ (static data) and transformation/ (functions
consuming that data). Every function here takes an explicit
SQLAlchemy session rather than opening its own, so both ui/app.py
(today) and, later, attack_pipeline.py itself (MVP 1.3) can call the
same functions without duplicating logic.
"""
import hashlib
import json

from sqlalchemy.orm import Session

from monsterforge.db.reference_data import Actor, Game
from monsterforge.db.seed import DND_GAME_NAME, HUMAN_REVIEWER_ACTOR_NAME, LLM_ACTOR_NAME
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype


class InconsistentActiveClassificationError(ValueError):
    """A raw_field's active classification event has no corresponding
    cards row — a data-integrity anomaly, not something to silently
    paper over by reclassifying. See find_existing_card()."""


def compute_fingerprint(
        raw_attack: RawAttack,
        creature_subtype: CreatureSubtype | None,
        effect_range: EffectRange | None) -> str:
    """
    Compute a deterministic cache key for an attack submission.

    Rules:
    - Includes name/modifier/attack_type/attack_effect (always),
      creature_subtype (the only free-form context field with a rigid
      classification rule attached), and effect_range when known.
    - Deliberately excludes additional_description/creature_description
      (free text): two submissions of mechanically the same attack for
      different creatures almost always have different free-text
      context, so including it would make the cache almost never hit in
      practice, defeating its purpose. creature_subtype is the one
      context field kept, since it can carry a rigid classification rule
      (e.g. "incorporeal" forces a magical move type) rather than just
      influencing the LLM's judgment the way free text does.

    A JSON-encoded list of the components is hashed rather than a
    delimiter-joined string, so a value that happens to contain the
    delimiter can't produce a colliding fingerprint for two genuinely
    different inputs.
    """
    components = [
        raw_attack.name,
        raw_attack.modifier,
        raw_attack.attack_type,
        raw_attack.attack_effect,
        creature_subtype.value if creature_subtype else None,
        effect_range.effect_range if effect_range else None,
        effect_range.range_unit_system.value if effect_range else None,
    ]
    normalized = json.dumps(components)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_default_game(session: Session) -> Game:
    """Return the seeded D&D 3.x game row (see db/seed.py)."""
    return session.query(Game).filter_by(name=DND_GAME_NAME).one()


def get_llm_actor(session: Session) -> Actor:
    """Return the seeded actor row representing the LLM (see db/seed.py)."""
    return session.query(Actor).filter_by(actor_name=LLM_ACTOR_NAME).one()


def get_human_actor(session: Session) -> Actor:
    """Return the seeded actor row representing the human reviewer (see db/seed.py)."""
    return session.query(Actor).filter_by(actor_name=HUMAN_REVIEWER_ACTOR_NAME).one()
