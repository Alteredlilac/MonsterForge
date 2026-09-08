"""
Tests for pipeline.attack_repository_queries.
"""
import pytest

from monsterforge.llm.semantic_classification.attacks import AttackSemanticResult
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import raw_to_structured_attack
from monsterforge.pipeline.attack_repository import (
    activate_classification_event,
    record_human_review,
    record_llm_run,
    save_structured_data,
)
from monsterforge.pipeline.attack_repository_queries import (
    InconsistentActiveClassificationError,
    find_existing_card,
    list_classification_events,
    list_saved_cards,
    resolve_effective_name,
)
from monsterforge.pipeline.reference_lookups import get_human_actor, get_llm_actor
from monsterforge.structured_data.dnd.v3x.enums import MoveType
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import HumanReview
from tests.conftest import BITE, CLAW


# =====================
# FIND_EXISTING_CARD
# =====================
def test_find_existing_card_raises_when_active_event_has_no_structured_data(seeded_db_session, make_raw_field):
    raw_field = make_raw_field()
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


def test_find_existing_card_raises_when_structured_data_has_no_card(seeded_db_session, make_raw_field):
    raw_field = make_raw_field()
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


# =====================
# LIST_CLASSIFICATION_EVENTS
# =====================
def test_list_classification_events_orders_oldest_first_and_flags_the_active_one(seeded_db_session, make_raw_field):
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
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=review_event)

    events = list_classification_events(seeded_db_session, raw_field.id)

    assert [event["event_type"] for event in events] == ["llm_run", "human_review"]
    assert events[0]["is_active"] is False
    assert events[1]["is_active"] is True


def test_list_classification_events_includes_llm_run_detail_fields(seeded_db_session, make_raw_field):
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.9, rationale="Clear.")
    record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                    actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                    model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                    decision=ValidationStatus.AUTO_APPROVED)

    events = list_classification_events(seeded_db_session, raw_field.id)

    assert len(events) == 1
    event = events[0]
    assert event["actor_name"] == "llm"
    assert event["prompt_name"] == "classify_attack.jinja2"
    assert event["result"]["confidence"] == 0.9
    assert event["result"]["rationale"] == "Clear."
    assert event["decision"] == "auto_approved"


def test_list_classification_events_includes_human_review_detail_fields(seeded_db_session, make_raw_field):
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.9, rationale="Clear.")
    llm_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                                actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                model_name="gemini-flash-lite-latest", confidence_threshold=0.7, decision=None)
    approve = HumanReview(status=ValidationStatus.APPROVED, result=result, assigned_llm_score=0.6,
                           edit_note="Looks fine.")
    record_human_review(seeded_db_session, raw_field=raw_field, referenced_event=llm_event,
                         review=approve, actor=get_human_actor(seeded_db_session))

    events = list_classification_events(seeded_db_session, raw_field.id)

    review_summary = events[1]
    assert review_summary["actor_name"] == "human_reviewer"
    assert review_summary["assigned_llm_score"] == 0.6
    assert review_summary["edit_note"] == "Looks fine."
    # An approval passes the same AttackSemanticResult through unchanged,
    # so its own result still carries the original confidence/rationale.
    assert review_summary["result"]["rationale"] == "Clear."


def test_list_classification_events_result_reflects_a_correction_not_the_original(seeded_db_session, make_raw_field):
    """The exact scenario a real correction needs: a CORRECTED review's
    own result must show the corrected values, not the originating
    LLM_RUN's pre-correction answer — two different rows, two
    different results, by design."""
    raw_field = make_raw_field()
    original = AttackSemanticResult(description="A shock.", move_type=MoveType.MAGICAL, move_range=None,
                                     confidence=0.9, rationale="Elemental damage implies magic.")
    llm_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=original,
                                actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                model_name="gemini-flash-lite-latest", confidence_threshold=0.7, decision=None)
    corrected = AttackSemanticResult(description="A shock.", move_type=MoveType.PHYSICAL, move_range=None,
                                      confidence=0.9, rationale="Elemental damage implies magic.")
    correct = HumanReview(status=ValidationStatus.CORRECTED, result=corrected)
    record_human_review(seeded_db_session, raw_field=raw_field, referenced_event=llm_event,
                         review=correct, actor=get_human_actor(seeded_db_session))

    events = list_classification_events(seeded_db_session, raw_field.id)

    assert events[0]["result"]["move_type"] == "magical"  # the LLM's own answer, unchanged in its own row
    assert events[1]["result"]["move_type"] == "physical"  # the reviewer's correction


def test_list_classification_events_effective_name_defaults_to_the_raw_fields_original(
        seeded_db_session, make_raw_field):
    """No correction has ever touched the name -- every event's
    effective_name falls back to raw_fields.data["name"] (BITE's own
    "Bite", see make_raw_field())."""
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.9, rationale="Clear.")
    record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                    actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                    model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                    decision=ValidationStatus.AUTO_APPROVED)

    events = list_classification_events(seeded_db_session, raw_field.id)

    assert events[0]["corrected_name"] is None
    assert events[0]["effective_name"] == "Bite"


def test_list_classification_events_effective_name_carries_a_correction_forward(seeded_db_session, make_raw_field):
    """A later event that never touches the name (an approve, or a
    fresh rerun) must still show the corrected name as its own
    effective_name, not silently revert to the original -- the whole
    point of MVP 2.19."""
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.4, rationale="Low.")
    llm_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                                actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                model_name="gemini-flash-lite-latest", confidence_threshold=0.7, decision=None)
    correct = HumanReview(status=ValidationStatus.CORRECTED, result=result, corrected_name="Fixed Name")
    correction_event = record_human_review(seeded_db_session, raw_field=raw_field, referenced_event=llm_event,
                                            review=correct, actor=get_human_actor(seeded_db_session))
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=correction_event)

    rerun_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                                  actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                  model_name="gemini-flash-lite-latest", confidence_threshold=0.7, decision=None,
                                  rerun_note="try again")

    events = list_classification_events(seeded_db_session, raw_field.id)

    assert events[0]["effective_name"] == "Bite"        # the original LLM_RUN, before any correction
    assert events[1]["effective_name"] == "Fixed Name"  # the correction itself
    assert events[2]["effective_name"] == "Fixed Name"  # a later rerun that never touched the name
    assert events[2]["id"] == rerun_event.id


# =====================
# RESOLVE_EFFECTIVE_NAME
# =====================
def test_resolve_effective_name_returns_the_name_as_of_a_specific_past_event(seeded_db_session, make_raw_field):
    """Resolving an OLD event, from before a later correction, must
    return the name as it stood back then -- not the raw_field's
    current name overall. Needed for reopening a past event for review
    (MVP 2.18) without silently jumping its name forward in time."""
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.4, rationale="Low.")
    llm_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                                actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                model_name="gemini-flash-lite-latest", confidence_threshold=0.7, decision=None)
    correct = HumanReview(status=ValidationStatus.CORRECTED, result=result, corrected_name="Fixed Name")
    record_human_review(seeded_db_session, raw_field=raw_field, referenced_event=llm_event,
                         review=correct, actor=get_human_actor(seeded_db_session))

    assert resolve_effective_name(seeded_db_session, raw_field, llm_event.id) == "Bite"


def test_resolve_effective_name_falls_back_to_the_original_when_never_corrected(seeded_db_session, make_raw_field):
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.95, rationale="Clear.")
    event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                            actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                            model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                            decision=ValidationStatus.AUTO_APPROVED)

    assert resolve_effective_name(seeded_db_session, raw_field, event.id) == "Bite"


# =====================
# LIST_SAVED_CARDS
# =====================
def test_list_saved_cards_includes_an_auto_approved_result(seeded_db_session, make_raw_field, build_and_save_card):
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.95, rationale="Clear.")
    event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                            actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                            model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                            decision=ValidationStatus.AUTO_APPROVED)
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=event)
    card_data = build_and_save_card(raw_field, event, BITE, result)

    entries = list_saved_cards(seeded_db_session)

    assert len(entries) == 1
    entry = entries[0]
    assert entry["raw_field_id"] == raw_field.id
    assert entry["case"]["name"] == "Bite"
    assert entry["context"]["creature_subtype"] is None
    assert entry["move_card"]["id"] == card_data["id"]
    assert entry["classification_result"]["confidence"] == 0.95
    assert entry["classification_result"]["rationale"] == "Clear."
    assert entry["classification_result"]["description"] == "A bite."
    assert entry["assigned_llm_score"] is None
    assert entry["edit_note"] is None
    assert entry["revision_count"] == 1
    assert len(entry["events"]) == 1


def test_list_saved_cards_shows_confidence_and_rationale_for_an_approved_review(
        seeded_db_session, make_raw_field, build_and_save_card):
    """An APPROVED review passes the same AttackSemanticResult through
    unchanged, so the active (HUMAN_REVIEW) event's own result still
    carries the original LLM confidence/rationale."""
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="Uncertain.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.4, rationale="Low confidence.")
    llm_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                                actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                model_name="gemini-flash-lite-latest", confidence_threshold=0.7, decision=None)
    approve = HumanReview(status=ValidationStatus.APPROVED, result=result, assigned_llm_score=0.6,
                           edit_note="Looks fine.")
    review_event = record_human_review(seeded_db_session, raw_field=raw_field, referenced_event=llm_event,
                                        review=approve, actor=get_human_actor(seeded_db_session))
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=review_event)
    build_and_save_card(raw_field, review_event, BITE, result)

    entries = list_saved_cards(seeded_db_session)

    assert len(entries) == 1
    entry = entries[0]
    assert entry["classification_result"]["confidence"] == 0.4
    assert entry["classification_result"]["rationale"] == "Low confidence."
    assert entry["assigned_llm_score"] == 0.6
    assert entry["edit_note"] == "Looks fine."
    assert entry["revision_count"] == 2  # the LLM_RUN plus the HUMAN_REVIEW


def test_list_saved_cards_shows_the_corrected_values_not_the_original(
        seeded_db_session, make_raw_field, build_and_save_card):
    """The bug this guards against: a CORRECTED review's saved card
    reflects the corrected classification, so the library must read
    move_type/description/move_range from the active (HUMAN_REVIEW)
    event's own result, not from the LLM_RUN it references — otherwise
    the library would show a stale, pre-correction move_type that
    doesn't match what the card actually renders."""
    raw_field = make_raw_field()
    original = AttackSemanticResult(description="A shock.", move_type=MoveType.MAGICAL, move_range=None,
                                     confidence=0.9, rationale="Elemental damage implies magic.")
    llm_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=original,
                                actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                model_name="gemini-flash-lite-latest", confidence_threshold=0.7, decision=None)
    corrected = AttackSemanticResult(description="A shock.", move_type=MoveType.PHYSICAL, move_range=None,
                                      confidence=0.9, rationale="Elemental damage implies magic.")
    correct = HumanReview(status=ValidationStatus.CORRECTED, result=corrected)
    review_event = record_human_review(seeded_db_session, raw_field=raw_field, referenced_event=llm_event,
                                        review=correct, actor=get_human_actor(seeded_db_session))
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=review_event)
    build_and_save_card(raw_field, review_event, BITE, corrected)

    entries = list_saved_cards(seeded_db_session)

    assert entries[0]["classification_result"]["move_type"] == "physical"


def test_list_saved_cards_includes_a_rejected_raw_field_with_no_card(seeded_db_session, make_raw_field):
    """A REJECTED active event still gets an entry (unlike an earlier
    version of this function, which skipped it entirely) -- it must
    stay reachable, history included, so a reviewer can find and
    reactivate an earlier good attempt instead of the raw_field simply
    vanishing from the library. find_existing_card() is never called
    for it (a REJECTED event never has a card), so move_card/
    classification_result are both None and name falls back to
    raw_fields.data["name"]."""
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

    entries = list_saved_cards(seeded_db_session)

    assert len(entries) == 1
    assert entries[0]["name"] == "Bite"
    assert entries[0]["move_card"] is None
    assert entries[0]["classification_result"] is None
    assert entries[0]["revision_count"] == 2  # the LLM_RUN plus the rejection


def test_list_saved_cards_rejected_fallback_name_reflects_an_earlier_correction(seeded_db_session, make_raw_field):
    """The fallback display name for a rejected raw_field must still
    reflect a correction made before the rejection, not always the raw,
    original submission -- resolve_effective_name(), not
    raw_fields.data["name"] directly (MVP 2.19)."""
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="Uncertain.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.4, rationale="Low.")
    llm_event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                                actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                model_name="gemini-flash-lite-latest", confidence_threshold=0.7, decision=None)
    correct = HumanReview(status=ValidationStatus.CORRECTED, result=result, corrected_name="Fixed Name")
    correction_event = record_human_review(seeded_db_session, raw_field=raw_field, referenced_event=llm_event,
                                            review=correct, actor=get_human_actor(seeded_db_session))
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=correction_event)

    reject = HumanReview(status=ValidationStatus.REJECTED, result=None)
    reject_event = record_human_review(seeded_db_session, raw_field=raw_field, referenced_event=correction_event,
                                        review=reject, actor=get_human_actor(seeded_db_session))
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=reject_event)

    entries = list_saved_cards(seeded_db_session)

    assert entries[0]["name"] == "Fixed Name"


def test_list_saved_cards_skips_a_raw_field_with_no_active_event(seeded_db_session, make_raw_field):
    make_raw_field()  # never classified

    assert list_saved_cards(seeded_db_session) == []


def test_list_saved_cards_skips_an_active_event_with_no_saved_card(seeded_db_session, make_raw_field):
    """The InconsistentActiveClassificationError anomaly find_existing_card()
    raises for a single lookup must not break this bulk listing — the
    anomalous raw_field is skipped silently, not raised."""
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.95, rationale="Clear.")
    event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                            actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                            model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                            decision=ValidationStatus.AUTO_APPROVED)
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=event)
    # deliberately never call save_structured_data()/save_card()

    assert list_saved_cards(seeded_db_session) == []


def test_list_saved_cards_orders_most_recently_created_raw_field_first(
        seeded_db_session, make_raw_field, build_and_save_card):
    bite_field = make_raw_field(raw_attack=BITE)
    bite_result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                        confidence=0.9, rationale="Clear.")
    bite_event = record_llm_run(seeded_db_session, raw_field=bite_field, semantic_result=bite_result,
                                 actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                 model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                                 decision=ValidationStatus.AUTO_APPROVED)
    activate_classification_event(seeded_db_session, raw_field=bite_field, event=bite_event)
    build_and_save_card(bite_field, bite_event, BITE, bite_result)

    claw_field = make_raw_field(raw_attack=CLAW)
    claw_result = AttackSemanticResult(description="A claw.", move_type=MoveType.PHYSICAL, move_range=None,
                                        confidence=0.9, rationale="Clear.")
    claw_event = record_llm_run(seeded_db_session, raw_field=claw_field, semantic_result=claw_result,
                                 actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                 model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                                 decision=ValidationStatus.AUTO_APPROVED)
    activate_classification_event(seeded_db_session, raw_field=claw_field, event=claw_event)
    build_and_save_card(claw_field, claw_event, CLAW, claw_result)

    entries = list_saved_cards(seeded_db_session)

    assert [entry["raw_field_id"] for entry in entries] == [claw_field.id, bite_field.id]


def test_list_saved_cards_query_filters_by_name_substring(seeded_db_session, make_raw_field, build_and_save_card):
    bite_field = make_raw_field(raw_attack=BITE)
    bite_result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                        confidence=0.9, rationale="Clear.")
    bite_event = record_llm_run(seeded_db_session, raw_field=bite_field, semantic_result=bite_result,
                                 actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                 model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                                 decision=ValidationStatus.AUTO_APPROVED)
    activate_classification_event(seeded_db_session, raw_field=bite_field, event=bite_event)
    build_and_save_card(bite_field, bite_event, BITE, bite_result)

    claw_field = make_raw_field(raw_attack=CLAW)
    claw_result = AttackSemanticResult(description="A claw.", move_type=MoveType.PHYSICAL, move_range=None,
                                        confidence=0.9, rationale="Clear.")
    claw_event = record_llm_run(seeded_db_session, raw_field=claw_field, semantic_result=claw_result,
                                 actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                                 model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                                 decision=ValidationStatus.AUTO_APPROVED)
    activate_classification_event(seeded_db_session, raw_field=claw_field, event=claw_event)
    build_and_save_card(claw_field, claw_event, CLAW, claw_result)

    entries = list_saved_cards(seeded_db_session, query="bit")  # lowercase, partial

    assert [entry["raw_field_id"] for entry in entries] == [bite_field.id]


def test_list_saved_cards_query_matches_an_id_prefix(seeded_db_session, make_raw_field, build_and_save_card):
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.9, rationale="Clear.")
    event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                            actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                            model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                            decision=ValidationStatus.AUTO_APPROVED)
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=event)
    build_and_save_card(raw_field, event, BITE, result)

    entries = list_saved_cards(seeded_db_session, query=raw_field.id[:8])  # the short id shown in the UI

    assert [entry["raw_field_id"] for entry in entries] == [raw_field.id]


def test_list_saved_cards_query_with_no_match_returns_an_empty_list(
        seeded_db_session, make_raw_field, build_and_save_card):
    raw_field = make_raw_field()
    result = AttackSemanticResult(description="A bite.", move_type=MoveType.PHYSICAL, move_range=None,
                                   confidence=0.9, rationale="Clear.")
    event = record_llm_run(seeded_db_session, raw_field=raw_field, semantic_result=result,
                            actor=get_llm_actor(seeded_db_session), prompt_name="classify_attack.jinja2",
                            model_name="gemini-flash-lite-latest", confidence_threshold=0.7,
                            decision=ValidationStatus.AUTO_APPROVED)
    activate_classification_event(seeded_db_session, raw_field=raw_field, event=event)
    build_and_save_card(raw_field, event, BITE, result)

    assert list_saved_cards(seeded_db_session, query="nonexistent") == []
