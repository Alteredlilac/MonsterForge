"""
Tests for pipeline.attack_repository.
"""
import json

from monsterforge.db.enums import CardType, EventStatus
from monsterforge.llm.semantic_classification.attacks import AttackSemanticResult
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import raw_to_structured_attack
from monsterforge.pipeline.attack_repository import (
    activate_classification_event,
    compute_fingerprint,
    get_or_create_raw_field,
    record_human_review,
    record_llm_run,
    save_card,
    save_structured_data,
)
from monsterforge.pipeline.attack_repository_queries import find_existing_card
from monsterforge.pipeline.reference_lookups import get_human_actor, get_llm_actor
from monsterforge.serialization.domain_to_json import card_to_json
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype, MoveType, UnitSystem
from monsterforge.transformation.dnd.v3x.converters.attacks_converter import attack_converter
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import HumanReview
from tests.pipeline.conftest import BITE, CLAW


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
# GET_OR_CREATE_RAW_FIELD
# =====================
def test_get_or_create_raw_field_creates_a_new_row(make_raw_field):
    raw_field = make_raw_field()

    assert raw_field.name == "Bite"
    assert raw_field.data["attack_effect"] == "1d6+3"
    assert raw_field.current_classification_event_id is None


def test_get_or_create_raw_field_reuses_an_existing_row(make_raw_field):
    first = make_raw_field()
    second = make_raw_field()

    assert first.id == second.id


def test_get_or_create_raw_field_does_not_duplicate_when_no_event_is_active_yet(make_raw_field):
    """The scenario get_or_create_raw_field's own docstring calls out:
    a row already exists for this fingerprint, but with no active event
    yet (e.g. an earlier attempt interrupted before activation) — must
    still be reused, not re-inserted (which would violate fingerprint's
    UNIQUE constraint)."""
    first = make_raw_field()
    assert first.current_classification_event_id is None

    second = make_raw_field()  # must not raise IntegrityError
    assert first.id == second.id


# =====================
# RECORD_LLM_RUN
# =====================
def test_record_llm_run_always_starts_pending(seeded_db_session, make_raw_field):
    raw_field = make_raw_field()
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


def test_record_llm_run_accepts_a_none_decision_when_review_is_pending(seeded_db_session, make_raw_field):
    raw_field = make_raw_field()
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
def test_activate_classification_event_points_raw_field_at_the_event(seeded_db_session, make_raw_field):
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.95, rationale="Clear.")
    event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                            actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                            model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                            decision=ValidationStatus.AUTO_APPROVED)

    activate_classification_event(seeded_db_session, raw_field=raw_field, event=event)

    assert event.status == EventStatus.ACTIVE
    assert raw_field.current_classification_event_id == event.id


def test_activate_classification_event_archives_the_previous_active_event(seeded_db_session, make_raw_field):
    raw_field = make_raw_field()
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


def test_activate_classification_event_also_activates_a_rejected_event(seeded_db_session, make_raw_field):
    """Deliberate project decision: current_classification_event_id
    tracks the most recently resolved state, not only a usable result —
    so a rejected attack is recognized immediately on a later lookup."""
    raw_field = make_raw_field()
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
def test_record_human_review_references_the_llm_run_it_decided_on(seeded_db_session, make_raw_field):
    raw_field = make_raw_field()
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


def test_record_human_review_rejected_stores_an_empty_dict_not_none(seeded_db_session, make_raw_field):
    """ClassificationEvent.result is never nullable — a REJECTED review
    (HumanReview.result is None per its own contract) must still store
    something JSON-serializable, not None."""
    raw_field = make_raw_field()
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


def test_record_human_review_stores_the_corrected_name(seeded_db_session, make_raw_field):
    """MVP 2.19: the corrected name has nowhere else to live -- it's
    never part of AttackSemanticResult (see HumanReview.corrected_name's
    own docstring) -- so record_human_review() must persist it onto the
    new classification_events.corrected_name column directly."""
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.4, rationale="Low.")
    llm_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                                actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                model_name="gemini-flash-lite-latest", confidence_threshold=0.7, decision=None)
    correct = HumanReview(status=ValidationStatus.CORRECTED, result=result, corrected_name="Fixed Name")

    review_event = record_human_review(seeded_db_session, raw_field=raw_field, referenced_event=llm_event,
                                        review=correct, actor=get_human_actor(seeded_db_session))

    assert review_event.corrected_name == "Fixed Name"


def test_record_human_review_leaves_corrected_name_null_when_not_given(seeded_db_session, make_raw_field):
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.9, rationale="Clear.")
    llm_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                                actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                model_name="gemini-flash-lite-latest", confidence_threshold=0.7, decision=None)
    approve = HumanReview(status=ValidationStatus.APPROVED, result=result)

    review_event = record_human_review(seeded_db_session, raw_field=raw_field, referenced_event=llm_event,
                                        review=approve, actor=get_human_actor(seeded_db_session))

    assert review_event.corrected_name is None


# =====================
# SAVE_STRUCTURED_DATA / SAVE_CARD
# =====================
def test_save_structured_data_and_save_card_round_trip_through_find_existing_card(seeded_db_session, make_raw_field):
    raw_field = make_raw_field()
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
