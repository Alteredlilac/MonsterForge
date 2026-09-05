"""
Tests for pipeline.attack_repository.
"""
import json

import pytest

from monsterforge.db.enums import CardType, EventStatus
from monsterforge.llm.semantic_classification.attacks import AttackSemanticResult, SemanticContextInput
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import raw_to_structured_attack
from monsterforge.pipeline.attack_repository import (
    InconsistentActiveClassificationError,
    activate_classification_event,
    compute_fingerprint,
    find_existing_card,
    get_default_game,
    get_human_actor,
    get_llm_actor,
    get_or_create_raw_field,
    record_human_review,
    record_llm_run,
    save_card,
    save_structured_data,
)
from monsterforge.serialization.domain_to_json import card_to_json
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype, MoveType, UnitSystem
from monsterforge.transformation.dnd.v3x.converters.attacks_converter import attack_converter
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import HumanReview

EMPTY_CONTEXT = SemanticContextInput(additional_description=None, creature_description=None, creature_subtype=None)
BITE = RawAttack(name="Bite", modifier="+7", attack_type="melee", attack_effect="1d6+3")
CLAW = RawAttack(name="Claw", modifier="+7", attack_type="melee", attack_effect="1d4+3")


def _make_raw_field(session, raw_attack=BITE, context=EMPTY_CONTEXT):
    fingerprint = compute_fingerprint(raw_attack, context.creature_subtype, None)
    return get_or_create_raw_field(
        session, game_id=get_default_game(session).id, raw_attack=raw_attack,
        semantic_context=context, fingerprint=fingerprint,
    )


# =====================
# COMPUTE_FINGERPRINT
# =====================
def test_compute_fingerprint_is_deterministic():
    assert compute_fingerprint(BITE, None, None) == compute_fingerprint(BITE, None, None)


def test_compute_fingerprint_differs_by_raw_attack():
    assert compute_fingerprint(BITE, None, None) != compute_fingerprint(CLAW, None, None)


def test_compute_fingerprint_differs_by_creature_subtype():
    assert compute_fingerprint(BITE, None, None) != compute_fingerprint(BITE, CreatureSubtype.INCORPOREAL, None)


def test_compute_fingerprint_differs_by_range():
    range_a = EffectRange(effect_range=30, range_unit_system=UnitSystem.IMPERIAL)
    range_b = EffectRange(effect_range=60, range_unit_system=UnitSystem.IMPERIAL)
    assert compute_fingerprint(BITE, None, range_a) != compute_fingerprint(BITE, None, range_b)


def test_compute_fingerprint_ignores_free_text_context():
    """Deliberate: additional_description/creature_description never
    affect the fingerprint — see the function's own docstring for why."""
    fp = compute_fingerprint(BITE, None, None)
    assert fp == compute_fingerprint(BITE, None, None)


# =====================
# SEED-ROW LOOKUPS
# =====================
def test_get_default_game_returns_the_seeded_dnd_row(seeded_db_session):
    assert get_default_game(seeded_db_session).name == "D&D 3.x"


def test_get_llm_actor_returns_the_seeded_llm_row(seeded_db_session):
    assert get_llm_actor(seeded_db_session).actor_name == "llm"


def test_get_human_actor_returns_the_seeded_human_row(seeded_db_session):
    assert get_human_actor(seeded_db_session).actor_name == "human_reviewer"


# =====================
# GET_OR_CREATE_RAW_FIELD
# =====================
def test_get_or_create_raw_field_creates_a_new_row(seeded_db_session):
    raw_field = _make_raw_field(seeded_db_session)

    assert raw_field.name == "Bite"
    assert raw_field.data["attack_effect"] == "1d6+3"
    assert raw_field.current_classification_event_id is None


def test_get_or_create_raw_field_reuses_an_existing_row(seeded_db_session):
    first = _make_raw_field(seeded_db_session)
    second = _make_raw_field(seeded_db_session)

    assert first.id == second.id


def test_get_or_create_raw_field_does_not_duplicate_when_no_event_is_active_yet(seeded_db_session):
    """The scenario get_or_create_raw_field's own docstring calls out:
    a row already exists for this fingerprint, but with no active event
    yet (e.g. an earlier attempt interrupted before activation) — must
    still be reused, not re-inserted (which would violate fingerprint's
    UNIQUE constraint)."""
    first = _make_raw_field(seeded_db_session)
    assert first.current_classification_event_id is None

    second = _make_raw_field(seeded_db_session)  # must not raise IntegrityError
    assert first.id == second.id


# =====================
# RECORD_LLM_RUN
# =====================
def test_record_llm_run_always_starts_pending(seeded_db_session):
    raw_field = _make_raw_field(seeded_db_session)
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.95, rationale="Clear.")

    event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                            actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                            model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                            decision=ValidationStatus.AUTO_APPROVED)

    assert event.status == EventStatus.PENDING
    assert event.decision == ValidationStatus.AUTO_APPROVED
    assert event.result["description"] == "A bite."
    assert raw_field.current_classification_event_id is None  # never self-activates


def test_record_llm_run_accepts_a_none_decision_when_review_is_pending(seeded_db_session):
    raw_field = _make_raw_field(seeded_db_session)
    result = AttackSemanticResult(description="Uncertain.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.4, rationale="Low.")

    event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                            actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                            model_name="gemini-flash-lite-latest", confidence_threshold=0.7, decision=None)

    assert event.decision is None
    assert event.status == EventStatus.PENDING


# =====================
# ACTIVATE_CLASSIFICATION_EVENT
# =====================
def test_activate_classification_event_points_raw_field_at_the_event(seeded_db_session):
    raw_field = _make_raw_field(seeded_db_session)
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.95, rationale="Clear.")
    event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                            actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                            model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                            decision=ValidationStatus.AUTO_APPROVED)

    activate_classification_event(seeded_db_session, raw_field=raw_field, event=event)

    assert event.status == EventStatus.ACTIVE
    assert raw_field.current_classification_event_id == event.id


def test_activate_classification_event_archives_the_previous_active_event(seeded_db_session):
    raw_field = _make_raw_field(seeded_db_session)
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.95, rationale="Clear.")
    llm_actor = get_llm_actor(seeded_db_session)
    first_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result, actor=llm_actor,
                                  prompt_name="classify_attack.jinja2", model_name="gemini-flash-lite-latest",
                                  confidence_threshold=0.7, decision=ValidationStatus.AUTO_APPROVED)
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=first_event)

    second_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result, actor=llm_actor,
                                   prompt_name="classify_attack.jinja2", model_name="gemini-flash-lite-latest",
                                   confidence_threshold=0.7, decision=ValidationStatus.AUTO_APPROVED,
                                   rerun_note="retry")
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=second_event)

    seeded_db_session.refresh(first_event)
    assert first_event.status == EventStatus.ARCHIVED
    assert second_event.status == EventStatus.ACTIVE
    assert raw_field.current_classification_event_id == second_event.id


def test_activate_classification_event_also_activates_a_rejected_event(seeded_db_session):
    """Deliberate project decision: current_classification_event_id
    tracks the most recently resolved state, not only a usable result —
    so a rejected attack is recognized immediately on a later lookup."""
    raw_field = _make_raw_field(seeded_db_session)
    result = AttackSemanticResult(description="Uncertain.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.4, rationale="Low.")
    llm_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                                actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                model_name="gemini-flash-lite-latest", confidence_threshold=0.7, decision=None)
    reject = HumanReview(status=ValidationStatus.REJECTED, result=None)
    reject_event = record_human_review(seeded_db_session, raw_field=raw_field, referenced_event=llm_event,
                                        review=reject, actor=get_human_actor(seeded_db_session))

    activate_classification_event(seeded_db_session, raw_field=raw_field, event=reject_event)

    assert reject_event.status == EventStatus.ACTIVE
    assert raw_field.current_classification_event_id == reject_event.id


# =====================
# RECORD_HUMAN_REVIEW
# =====================
def test_record_human_review_references_the_llm_run_it_decided_on(seeded_db_session):
    raw_field = _make_raw_field(seeded_db_session)
    result = AttackSemanticResult(description="Uncertain.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.4, rationale="Low.")
    llm_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                                actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                model_name="gemini-flash-lite-latest", confidence_threshold=0.7, decision=None)
    approve = HumanReview(status=ValidationStatus.APPROVED, result=result, assigned_llm_score=0.6,
                           edit_note="Looks fine.")

    review_event = record_human_review(seeded_db_session, raw_field=raw_field, referenced_event=llm_event,
                                        review=approve, actor=get_human_actor(seeded_db_session))

    assert review_event.referenced_event_id == llm_event.id
    assert review_event.decision == ValidationStatus.APPROVED
    assert review_event.result["description"] == "Uncertain."
    assert review_event.edit_note == "Looks fine."


def test_record_human_review_rejected_stores_an_empty_dict_not_none(seeded_db_session):
    """ClassificationEvent.result is never nullable — a REJECTED review
    (HumanReview.result is None per its own contract) must still store
    something JSON-serializable, not None."""
    raw_field = _make_raw_field(seeded_db_session)
    result = AttackSemanticResult(description="Nonsense.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.3, rationale="Bad.")
    llm_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                                actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                model_name="gemini-flash-lite-latest", confidence_threshold=0.7, decision=None)
    reject = HumanReview(status=ValidationStatus.REJECTED, result=None, edit_note="Nonsense.")

    review_event = record_human_review(seeded_db_session, raw_field=raw_field, referenced_event=llm_event,
                                        review=reject, actor=get_human_actor(seeded_db_session))

    assert review_event.result == {}
    assert review_event.decision == ValidationStatus.REJECTED


# =====================
# SAVE_STRUCTURED_DATA / SAVE_CARD / FIND_EXISTING_CARD
# =====================
def test_save_structured_data_and_save_card_round_trip_through_find_existing_card(seeded_db_session):
    raw_field = _make_raw_field(seeded_db_session)
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.95, rationale="Clear.")
    event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                            actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                            model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                            decision=ValidationStatus.AUTO_APPROVED)
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=event)

    structured_attack = raw_to_structured_attack(BITE, result)
    move_card = attack_converter(structured_attack)
    card_data = json.loads(card_to_json(move_card))

    structured_data = save_structured_data(seeded_db_session, raw_field=raw_field, classification_event=event,
                                            structured_attack=structured_attack)
    save_card(seeded_db_session, structured_data=structured_data, card_data=card_data, card_type=CardType.MOVE_CARD)

    found_structured_data, found_card = find_existing_card(seeded_db_session, event)
    assert found_structured_data.classification_event_id == event.id
    assert found_card.name == move_card.name
    assert found_card.content["id"] == card_data["id"]


def test_find_existing_card_raises_when_active_event_has_no_structured_data(seeded_db_session):
    raw_field = _make_raw_field(seeded_db_session)
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.95, rationale="Clear.")
    event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                            actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                            model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                            decision=ValidationStatus.AUTO_APPROVED)
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=event)
    # deliberately never call save_structured_data()/save_card()

    with pytest.raises(InconsistentActiveClassificationError):
        find_existing_card(seeded_db_session, event)


def test_find_existing_card_raises_when_structured_data_has_no_card(seeded_db_session):
    raw_field = _make_raw_field(seeded_db_session)
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.95, rationale="Clear.")
    event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                            actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                            model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                            decision=ValidationStatus.AUTO_APPROVED)
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=event)
    structured_attack = raw_to_structured_attack(BITE, result)
    save_structured_data(seeded_db_session, raw_field=raw_field, classification_event=event,
                          structured_attack=structured_attack)
    # deliberately never call save_card()

    with pytest.raises(InconsistentActiveClassificationError):
        find_existing_card(seeded_db_session, event)
