"""
Tests for db.pipeline: RawField, ClassificationEvent, StructuredData.
"""
import datetime

import sqlalchemy as sa

from monsterforge.db.enums import EntityType, EventStatus, EventType
from monsterforge.db.pipeline import ClassificationEvent, RawField, StructuredData
from monsterforge.db.reference_data import Actor, Game
from monsterforge.validation.enums import ValidationStatus


def _make_game_and_actor(db_session):
    game = Game(name="D&D 3.x")
    actor = Actor(actor_name="llm", authority=0)
    db_session.add_all([game, actor])
    db_session.commit()
    return game, actor


def _make_raw_field(db_session, game):
    raw_field = RawField(
        page_id=None,
        game_id=game.id,
        raw_kind="attack",
        name="Bite",
        data={"name": "Bite", "modifier": "+7", "attack_type": "melee", "attack_effect": "1d6+3"},
        created_at=datetime.datetime(2026, 9, 4),
    )
    db_session.add(raw_field)
    db_session.commit()
    return raw_field


def _make_classification_event(db_session, raw_field, actor):
    event = ClassificationEvent(
        raw_field_id=raw_field.id,
        event_type=EventType.LLM_RUN,
        result={},
        actor_id=actor.id,
        decision=ValidationStatus.AUTO_APPROVED,
        status=EventStatus.ACTIVE,
        created_at=datetime.datetime(2026, 9, 4),
    )
    db_session.add(event)
    db_session.commit()
    return event


def test_raw_field_round_trips_with_no_page(db_session):
    game, _actor = _make_game_and_actor(db_session)

    raw_field = _make_raw_field(db_session, game)

    result = db_session.query(RawField).one()
    assert result.page_id is None
    assert result.name == "Bite"
    assert result.data["attack_effect"] == "1d6+3"
    assert result.current_classification_event_id is None


def test_classification_event_round_trips_for_an_llm_run(db_session):
    game, actor = _make_game_and_actor(db_session)
    raw_field = _make_raw_field(db_session, game)

    event = ClassificationEvent(
        raw_field_id=raw_field.id,
        event_type=EventType.LLM_RUN,
        prompt_name="classify_attack.jinja2",
        model_name="gemini-flash-lite-latest",
        confidence=0.92,
        confidence_threshold_at_time=0.7,
        rerun_note=None,
        result={"move_type": "physical", "description": "A vicious bite."},
        actor_id=actor.id,
        decision=ValidationStatus.AUTO_APPROVED,
        status=EventStatus.ACTIVE,
        referenced_event_id=None,
        created_at=datetime.datetime(2026, 9, 4),
    )
    db_session.add(event)
    db_session.commit()

    result = db_session.query(ClassificationEvent).one()
    assert result.event_type == EventType.LLM_RUN
    assert result.confidence == 0.92
    assert result.decision == ValidationStatus.AUTO_APPROVED
    assert result.status == EventStatus.ACTIVE


def test_classification_event_enums_are_stored_as_their_string_values(db_session):
    game, actor = _make_game_and_actor(db_session)
    raw_field = _make_raw_field(db_session, game)

    db_session.add(ClassificationEvent(
        raw_field_id=raw_field.id,
        event_type=EventType.LLM_RUN,
        result={},
        actor_id=actor.id,
        decision=ValidationStatus.AUTO_APPROVED,
        status=EventStatus.ACTIVE,
        created_at=datetime.datetime(2026, 9, 4),
    ))
    db_session.commit()

    row = db_session.execute(
        sa.text("SELECT event_type, decision, status FROM classification_events")
    ).one()

    assert row.event_type == "llm_run"
    assert row.decision == "auto_approved"
    assert row.status == "active"


def test_raw_field_current_classification_event_id_points_back_to_the_event(db_session):
    """Exercises the circular FK between raw_fields and classification_events
    with real rows: an event must exist referencing the raw field before
    the raw field can be updated to point at it."""
    game, actor = _make_game_and_actor(db_session)
    raw_field = _make_raw_field(db_session, game)

    event = ClassificationEvent(
        raw_field_id=raw_field.id,
        event_type=EventType.LLM_RUN,
        result={},
        actor_id=actor.id,
        decision=ValidationStatus.AUTO_APPROVED,
        status=EventStatus.ACTIVE,
        created_at=datetime.datetime(2026, 9, 4),
    )
    db_session.add(event)
    db_session.commit()

    raw_field.current_classification_event_id = event.id
    db_session.commit()

    result = db_session.query(RawField).one()
    assert result.current_classification_event_id == event.id


def test_classification_event_referenced_event_id_can_point_at_an_earlier_event(db_session):
    """referenced_event_id is a semantic pointer, not a chronological one —
    a human_review event references the specific llm_run it decided on."""
    game, actor_llm = _make_game_and_actor(db_session)
    actor_human = Actor(actor_name="human_reviewer", authority=10)
    db_session.add(actor_human)
    db_session.commit()
    raw_field = _make_raw_field(db_session, game)

    llm_event = ClassificationEvent(
        raw_field_id=raw_field.id,
        event_type=EventType.LLM_RUN,
        result={},
        actor_id=actor_llm.id,
        decision=None,
        status=EventStatus.PENDING,
        created_at=datetime.datetime(2026, 9, 4, 10, 0),
    )
    db_session.add(llm_event)
    db_session.commit()

    review_event = ClassificationEvent(
        raw_field_id=raw_field.id,
        event_type=EventType.HUMAN_REVIEW,
        result={},
        assigned_llm_score=0.8,
        edit_note="looks correct",
        actor_id=actor_human.id,
        decision=ValidationStatus.APPROVED,
        status=EventStatus.ACTIVE,
        referenced_event_id=llm_event.id,
        created_at=datetime.datetime(2026, 9, 4, 10, 5),
    )
    db_session.add(review_event)
    db_session.commit()

    result = db_session.query(ClassificationEvent).filter_by(event_type=EventType.HUMAN_REVIEW).one()
    assert result.referenced_event_id == llm_event.id
    assert result.edit_note == "looks correct"


def test_classification_event_rejects_an_unknown_raw_field_id(db_session):
    _game, actor = _make_game_and_actor(db_session)

    db_session.add(ClassificationEvent(
        raw_field_id="does-not-exist",
        event_type=EventType.LLM_RUN,
        result={},
        actor_id=actor.id,
        status=EventStatus.PENDING,
        created_at=datetime.datetime(2026, 9, 4),
    ))
    try:
        db_session.commit()
        assert False, "expected an IntegrityError on an unknown raw_field_id"
    except sa.exc.IntegrityError:
        db_session.rollback()


def test_structured_data_round_trips_and_requires_a_raw_field(db_session):
    game, actor = _make_game_and_actor(db_session)
    raw_field = _make_raw_field(db_session, game)
    event = _make_classification_event(db_session, raw_field, actor)

    structured = StructuredData(
        raw_field_id=raw_field.id,
        classification_event_id=event.id,
        entity_type=EntityType.ATTACK,
        name="Bite",
        data={"move_type": "physical"},
    )
    db_session.add(structured)
    db_session.commit()

    result = db_session.query(StructuredData).one()
    assert result.entity_type == EntityType.ATTACK
    assert result.name == "Bite"
    assert result.classification_event_id == event.id


def test_structured_data_rejects_an_unknown_raw_field_id(db_session):
    game, actor = _make_game_and_actor(db_session)
    raw_field = _make_raw_field(db_session, game)
    event = _make_classification_event(db_session, raw_field, actor)

    db_session.add(StructuredData(
        raw_field_id="does-not-exist",
        classification_event_id=event.id,
        entity_type=EntityType.ATTACK,
        name="Bite",
        data={},
    ))
    try:
        db_session.commit()
        assert False, "expected an IntegrityError on an unknown raw_field_id"
    except sa.exc.IntegrityError:
        db_session.rollback()


def test_structured_data_rejects_an_unknown_classification_event_id(db_session):
    game, _actor = _make_game_and_actor(db_session)
    raw_field = _make_raw_field(db_session, game)

    db_session.add(StructuredData(
        raw_field_id=raw_field.id,
        classification_event_id="does-not-exist",
        entity_type=EntityType.ATTACK,
        name="Bite",
        data={},
    ))
    try:
        db_session.commit()
        assert False, "expected an IntegrityError on an unknown classification_event_id"
    except sa.exc.IntegrityError:
        db_session.rollback()


def test_structured_data_supports_multiple_versions_for_the_same_raw_field(db_session):
    """Versioning check: a reclassification produces a new structured_data
    row instead of overwriting the existing one — both remain queryable,
    only classification_event_id tells them apart."""
    game, actor = _make_game_and_actor(db_session)
    raw_field = _make_raw_field(db_session, game)
    first_event = _make_classification_event(db_session, raw_field, actor)
    second_event = _make_classification_event(db_session, raw_field, actor)

    db_session.add_all([
        StructuredData(
            raw_field_id=raw_field.id, classification_event_id=first_event.id,
            entity_type=EntityType.ATTACK, name="Bite", data={"move_type": "physical"},
        ),
        StructuredData(
            raw_field_id=raw_field.id, classification_event_id=second_event.id,
            entity_type=EntityType.ATTACK, name="Bite", data={"move_type": "magical"},
        ),
    ])
    db_session.commit()

    versions = db_session.query(StructuredData).filter_by(raw_field_id=raw_field.id).all()
    assert {v.classification_event_id for v in versions} == {first_event.id, second_event.id}
