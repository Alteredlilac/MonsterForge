"""
Populate the public demo deployment with a handful of real, already-
classified cards, so GET /api/cards returns something on a fresh
instance instead of an empty list -- api/'s equivalent of the web
form's Auto-fill button, except this writes persisted cards rather
than just filling a form.

Never calls classify_attack(): each entry in entrypoints.
api_demo_seed_data.DEMO_SEED_ATTACKS already carries a real, verified
classification from a past Gemini run, so this module only replays it
through the same deterministic build steps api/creation.py's own
_build_and_persist_card() uses (raw_to_structured_attack(),
attack_converter()) -- no network call, no quota spent, no risk of a
different confidence landing a demo card in pending review instead of
auto-approved.

Only invoked from api/app.py's lifespan, behind the SEED_DEMO_DATA
environment variable -- never in local development or tests.
"""
import json

from monsterforge.db.enums import CardType
from monsterforge.entrypoints.api_demo_seed_data import DEMO_SEED_ATTACKS
from monsterforge.llm.semantic_classification.attacks import AttackSemanticResult, SemanticContextInput
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import raw_to_structured_attack
from monsterforge.pipeline.attack_repository import (
    activate_classification_event,
    compute_fingerprint,
    get_or_create_raw_field,
    record_llm_run,
    save_card,
    save_structured_data,
)
from monsterforge.pipeline.reference_lookups import get_default_game, get_llm_actor
from monsterforge.serialization.domain_to_json import card_to_json
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype, MoveType, UnitSystem
from monsterforge.transformation.dnd.v3x.converters.attacks_converter import attack_converter
from monsterforge.validation.enums import ValidationStatus


def seed_demo_cards(session) -> None:
    """
    Build and persist a card for every entry in DEMO_SEED_ATTACKS that
    doesn't already have one -- idempotent by construction, since
    get_or_create_raw_field() looks up by fingerprint: running this
    twice (e.g. a Render restart that didn't actually wipe the disk)
    finds an existing, already-active raw_field for each entry and
    skips it rather than creating a duplicate.
    """
    game_id = get_default_game(session).id
    llm_actor = get_llm_actor(session)

    for entry in DEMO_SEED_ATTACKS:
        raw_attack = RawAttack(**entry["case"])
        context = entry["context"]
        semantic_context = SemanticContextInput(
            additional_description=context["additional_description"],
            creature_description=context["creature_description"],
            creature_subtype=CreatureSubtype(context["creature_subtype"]) if context["creature_subtype"] else None,
        )

        classification = entry["classification"]
        move_range = None
        if classification["range_value"] is not None:
            move_range = EffectRange(
                effect_range=classification["range_value"],
                range_unit_system=UnitSystem(classification["range_unit"]),
            )
        semantic_result = AttackSemanticResult(
            description=classification["description"],
            move_type=MoveType(classification["move_type"]),
            move_range=move_range,
            confidence=classification["confidence"],
            rationale=classification["rationale"],
        )

        fingerprint = compute_fingerprint(raw_attack, semantic_context.creature_subtype, move_range)
        raw_field = get_or_create_raw_field(
            session, game_id=game_id, raw_attack=raw_attack,
            semantic_context=semantic_context, fingerprint=fingerprint,
        )

        if raw_field.current_classification_event_id is not None:
            continue

        llm_event = record_llm_run(
            session, raw_field=raw_field, semantic_result=semantic_result, actor=llm_actor,
            prompt_name="attacks/classify_attack.jinja2", model_name="gemini-flash-lite-latest",
            confidence_threshold=1.0, decision=ValidationStatus.AUTO_APPROVED,
        )

        structured_attack = raw_to_structured_attack(raw_attack, semantic_result)
        move_card = attack_converter(structured_attack)
        card_data = json.loads(card_to_json(move_card))

        structured_data = save_structured_data(
            session, raw_field=raw_field, classification_event=llm_event, structured_attack=structured_attack,
        )
        save_card(session, structured_data=structured_data, card_data=card_data, card_type=CardType.MOVE_CARD)
        activate_classification_event(session, raw_field=raw_field, event=llm_event)
