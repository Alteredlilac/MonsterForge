"""
Tests for pipeline.attack_pipeline.convert_attack().

Covers the full "bite plus trip" reference scenario end to end, with
the LLM classifier mocked (no real API calls in tests).
"""
from unittest.mock import Mock, patch
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.llm.semantic_classification.attacks import AttackSemanticResult
from monsterforge.structured_data.dnd.v3x.enums import MoveType, CreatureSubtype
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import HumanReview
from monsterforge.pipeline.attack_pipeline import convert_attack


def make_semantic_result(**overrides):
    defaults = dict(
        description="A vicious bite that can knock the target down.",
        move_type=MoveType.PHYSICAL,
        move_range=None,
        confidence=0.95,
        rationale="Natural melee attack with a secondary maneuver.",
    )
    defaults.update(overrides)
    return AttackSemanticResult(**defaults)


def test_convert_attack_bite_plus_trip_end_to_end():
    raw_attack = RawAttack(
        name="Bite", modifier="+7", attack_type="melee", attack_effect="1d6+3 plus trip"
    )

    with patch(
        "monsterforge.pipeline.attack_pipeline.classify_attack",
        return_value=make_semantic_result(),
    ) as mock_classify:
        card = convert_attack(raw_attack)

    mock_classify.assert_called_once_with(
        raw_attack=raw_attack,
        additional_description=None,
        creature_description=None,
        creature_subtype=None,
    )
    assert card.name == "Bite"
    assert card.move_effects[0].effect_value == 6  # 1d6 avg (3) + bonus (3)
    assert len(card.cards_to_add) == 1
    assert card.cards_to_add[0].name == "Trip"


def test_convert_attack_without_effects_has_no_cards_to_add():
    raw_attack = RawAttack(
        name="Claw", modifier="+9", attack_type="melee", attack_effect="2d6+4"
    )

    with patch(
        "monsterforge.pipeline.attack_pipeline.classify_attack",
        return_value=make_semantic_result(description="A raking claw."),
    ):
        card = convert_attack(raw_attack)

    assert card.cards_to_add == []


def test_convert_attack_forwards_optional_semantic_context():
    """The optional context params must reach classify_attack() as-is,
    not get lost or defaulted along the way — this is the seam that
    lets callers (entry points, the future real-API sample collector)
    exercise classify_attack() with realistic context."""
    raw_attack = RawAttack(
        name="Tail touch", modifier="+4", attack_type="melee touch", attack_effect="positive energy"
    )

    with patch(
        "monsterforge.pipeline.attack_pipeline.classify_attack",
        return_value=make_semantic_result(description="A ghostly touch."),
    ) as mock_classify:
        convert_attack(
            raw_attack,
            additional_description="Part of a larger grapple attempt.",
            creature_description="A translucent, drifting undead.",
            creature_subtype=CreatureSubtype.INCORPOREAL,
        )

    mock_classify.assert_called_once_with(
        raw_attack=raw_attack,
        additional_description="Part of a larger grapple attempt.",
        creature_description="A translucent, drifting undead.",
        creature_subtype=CreatureSubtype.INCORPOREAL,
    )


def test_convert_attack_returns_none_for_blank_attack():
    """A blank raw_attack is an empty submission, not a real attack —
    skip classification entirely rather than spending an LLM call on it."""
    raw_attack = RawAttack(name="", modifier="", attack_type="", attack_effect="")

    with patch("monsterforge.pipeline.attack_pipeline.classify_attack") as mock_classify:
        card = convert_attack(raw_attack)

    mock_classify.assert_not_called()
    assert card is None


def test_convert_attack_skips_review_without_a_handler_even_at_low_confidence():
    """Preserves MVP zero's behavior: without review_handler, no review
    is ever triggered regardless of confidence, so batch scripts and
    other non-interactive callers are unaffected by this feature."""
    raw_attack = RawAttack(name="Claw", modifier="+9", attack_type="melee", attack_effect="2d6+4")

    with patch(
        "monsterforge.pipeline.attack_pipeline.classify_attack",
        return_value=make_semantic_result(confidence=0.1),
    ):
        card = convert_attack(raw_attack)

    assert card is not None


def test_convert_attack_skips_review_handler_at_high_confidence():
    raw_attack = RawAttack(name="Claw", modifier="+9", attack_type="melee", attack_effect="2d6+4")
    review_handler = Mock()

    with patch(
        "monsterforge.pipeline.attack_pipeline.classify_attack",
        return_value=make_semantic_result(confidence=0.95),
    ):
        convert_attack(raw_attack, review_handler=review_handler)

    review_handler.assert_not_called()


def test_convert_attack_rejected_review_returns_none():
    raw_attack = RawAttack(name="Claw", modifier="+9", attack_type="melee", attack_effect="2d6+4")
    review_handler = Mock(return_value=HumanReview(status=ValidationStatus.REJECTED, result=None))

    with patch(
        "monsterforge.pipeline.attack_pipeline.classify_attack",
        return_value=make_semantic_result(confidence=0.1),
    ):
        card = convert_attack(raw_attack, review_handler=review_handler)

    review_handler.assert_called_once()
    assert card is None


def test_convert_attack_corrected_review_uses_edited_result():
    raw_attack = RawAttack(name="Claw", modifier="+9", attack_type="melee", attack_effect="2d6+4")
    corrected_result = make_semantic_result(confidence=0.1, description="A hand-corrected claw strike.")
    review_handler = Mock(return_value=HumanReview(status=ValidationStatus.CORRECTED, result=corrected_result))

    with patch(
        "monsterforge.pipeline.attack_pipeline.classify_attack",
        return_value=make_semantic_result(confidence=0.1, description="original description"),
    ):
        card = convert_attack(raw_attack, review_handler=review_handler)

    assert card.description == "A hand-corrected claw strike."


def test_convert_attack_approved_review_keeps_original_result():
    raw_attack = RawAttack(name="Claw", modifier="+9", attack_type="melee", attack_effect="2d6+4")
    original_result = make_semantic_result(confidence=0.1, description="original description")
    review_handler = Mock(return_value=HumanReview(status=ValidationStatus.APPROVED, result=original_result))

    with patch(
        "monsterforge.pipeline.attack_pipeline.classify_attack",
        return_value=original_result,
    ):
        card = convert_attack(raw_attack, review_handler=review_handler)

    assert card.description == "original description"
