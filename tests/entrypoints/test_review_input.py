"""
Tests for the interactive human review helper (MVP 0.5/rerun).

Covers:
- _prompt_enum_choice(): blank default, valid input, invalid-then-valid
- _prompt_optional_float()/_prompt_optional_text(): blank vs. real input
- _prompt_move_range_correction(): decline vs. accept an edit, including
  when there's no current range to fall back to
- _prompt_correction(): assembles a corrected AttackSemanticResult
- _rerun_classification(): note appending, template override, and a
  failed reclassification leaving the caller's state untouched
- prompt_for_human_review(): the four outcomes (approve/correct/reject/
  rerun-then-decide), plus retrying on an invalid menu choice
"""
from unittest.mock import patch
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.llm.semantic_classification.attacks import (
    AttackSemanticResult,
    ATTACK_PROMPT_TEMPLATE_OPTIONS,
    SemanticContextInput,
)
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import MoveType, UnitSystem
from monsterforge.validation.enums import ValidationStatus
from monsterforge.entrypoints._review_input import (
    _prompt_correction,
    _prompt_enum_choice,
    _prompt_move_range_correction,
    _prompt_optional_float,
    _prompt_optional_text,
    _rerun_classification,
    prompt_for_human_review,
)


def make_semantic_result(**overrides):
    defaults = dict(
        description="A vicious bite.",
        move_type=MoveType.PHYSICAL,
        move_range=None,
        confidence=0.4,
        rationale="test rationale",
    )
    defaults.update(overrides)
    return AttackSemanticResult(**defaults)


RAW_ATTACK = RawAttack(name="Bite", modifier="+5", attack_type="melee", attack_effect="1d6+3")
SEMANTIC_CONTEXT = SemanticContextInput(
    additional_description=None, creature_description="A wolf", creature_subtype=None
)
TEMPLATE_NAME = "attacks/classify_attack.jinja2"


# =====================
# _prompt_enum_choice
# =====================
def test_prompt_enum_choice_blank_keeps_current():
    with patch("builtins.input", side_effect=[""]):
        assert _prompt_enum_choice("Move type", MoveType, MoveType.PHYSICAL) == MoveType.PHYSICAL


def test_prompt_enum_choice_accepts_a_valid_value():
    with patch("builtins.input", side_effect=["magical"]):
        assert _prompt_enum_choice("Move type", MoveType, MoveType.PHYSICAL) == MoveType.MAGICAL


def test_prompt_enum_choice_reprompts_on_invalid_value():
    with patch("builtins.input", side_effect=["bogus", "magical"]):
        assert _prompt_enum_choice("Move type", MoveType, MoveType.PHYSICAL) == MoveType.MAGICAL


# =====================
# _prompt_optional_float / _prompt_optional_text
# =====================
def test_prompt_optional_float_blank_is_none():
    with patch("builtins.input", side_effect=[""]):
        assert _prompt_optional_float("Score: ") is None


def test_prompt_optional_float_parses_a_valid_number():
    with patch("builtins.input", side_effect=["0.75"]):
        assert _prompt_optional_float("Score: ") == 0.75


def test_prompt_optional_float_invalid_number_is_none():
    with patch("builtins.input", side_effect=["not-a-number"]):
        assert _prompt_optional_float("Score: ") is None


def test_prompt_optional_text_blank_is_none():
    with patch("builtins.input", side_effect=[""]):
        assert _prompt_optional_text("Note: ") is None


def test_prompt_optional_text_returns_stripped_text():
    with patch("builtins.input", side_effect=["  a note  "]):
        assert _prompt_optional_text("Note: ") == "a note"


# =====================
# _prompt_move_range_correction
# =====================
def test_prompt_move_range_correction_declined_keeps_current():
    current = EffectRange(effect_range=30, range_unit_system=UnitSystem.IMPERIAL)

    with patch("builtins.input", side_effect=["n"]):
        assert _prompt_move_range_correction(current) is current


def test_prompt_move_range_correction_declined_with_no_current_stays_none():
    with patch("builtins.input", side_effect=["n"]):
        assert _prompt_move_range_correction(None) is None


def test_prompt_move_range_correction_accepted_builds_new_range():
    current = EffectRange(effect_range=30, range_unit_system=UnitSystem.IMPERIAL)

    with patch("builtins.input", side_effect=["y", "60", "metric"]):
        result = _prompt_move_range_correction(current)

    assert result == EffectRange(effect_range=60, range_unit_system=UnitSystem.METRIC)


def test_prompt_move_range_correction_accepted_blank_value_falls_back_to_zero_when_no_current():
    with patch("builtins.input", side_effect=["y", "", "metric"]):
        result = _prompt_move_range_correction(None)

    assert result == EffectRange(effect_range=0, range_unit_system=UnitSystem.METRIC)


# =====================
# _prompt_correction
# =====================
def test_prompt_correction_assembles_edited_result():
    current = make_semantic_result(description="original", move_type=MoveType.PHYSICAL, move_range=None)

    with patch("builtins.input", side_effect=["a corrected description", "magical", "n"]):
        result = _prompt_correction(current)

    assert result.description == "a corrected description"
    assert result.move_type == MoveType.MAGICAL
    assert result.move_range is None
    assert result.confidence == current.confidence  # untouched, not part of the correction form
    assert result.rationale == current.rationale


def test_prompt_correction_blank_description_keeps_current():
    current = make_semantic_result(description="original")

    with patch("builtins.input", side_effect=["", "", "n"]):
        result = _prompt_correction(current)

    assert result.description == "original"


# =====================
# _rerun_classification
# =====================
def test_rerun_classification_appends_note_to_existing_additional_description():
    context = SemanticContextInput(
        additional_description="initial note", creature_description=None, creature_subtype=None
    )
    reclassified = make_semantic_result(description="after rerun")

    with patch("monsterforge.entrypoints._review_input.classify_attack", return_value=reclassified) as mock_classify, \
         patch("builtins.input", side_effect=["double-check this", ""]):
        result = _rerun_classification(RAW_ATTACK, context, TEMPLATE_NAME)

    assert result is not None
    new_context, new_result, new_template = result
    assert new_context.additional_description == "initial note\ndouble-check this"
    assert new_result is reclassified
    assert new_template == TEMPLATE_NAME  # blank input keeps the current template
    mock_classify.assert_called_once_with(
        raw_attack=RAW_ATTACK,
        additional_description="initial note\ndouble-check this",
        creature_description=None,
        creature_subtype=None,
        template_name=TEMPLATE_NAME,
    )


def test_rerun_classification_note_becomes_description_when_none_existed():
    context = SemanticContextInput(additional_description=None, creature_description=None, creature_subtype=None)
    chosen_option = ATTACK_PROMPT_TEMPLATE_OPTIONS[2]

    with patch("monsterforge.entrypoints._review_input.classify_attack", return_value=make_semantic_result()), \
         patch("builtins.input", side_effect=["first note ever", "3"]):
        new_context, _, new_template = _rerun_classification(RAW_ATTACK, context, TEMPLATE_NAME)

    assert new_context.additional_description == "first note ever"
    assert new_template == chosen_option.path


def test_rerun_classification_blank_note_leaves_additional_description_untouched():
    context = SemanticContextInput(
        additional_description="unchanged", creature_description=None, creature_subtype=None
    )

    with patch("monsterforge.entrypoints._review_input.classify_attack", return_value=make_semantic_result()), \
         patch("builtins.input", side_effect=["", ""]):
        new_context, _, _ = _rerun_classification(RAW_ATTACK, context, TEMPLATE_NAME)

    assert new_context.additional_description == "unchanged"


def test_rerun_classification_failure_returns_none():
    """Any classify_attack failure (a model error, a network issue —
    an unknown template path can no longer reach this point, since
    prompt_for_template_choice() validates it first) must not crash the
    review session — the caller keeps its prior state."""
    with patch(
        "monsterforge.entrypoints._review_input.classify_attack",
        side_effect=RuntimeError("boom"),
    ), patch("builtins.input", side_effect=["", ""]):
        result = _rerun_classification(RAW_ATTACK, SEMANTIC_CONTEXT, TEMPLATE_NAME)

    assert result is None


# =====================
# prompt_for_human_review
# =====================
def test_prompt_for_human_review_approve_keeps_result_unchanged():
    semantic_result = make_semantic_result()

    with patch("builtins.input", side_effect=["a", "", ""]):
        review = prompt_for_human_review(RAW_ATTACK, SEMANTIC_CONTEXT, semantic_result, TEMPLATE_NAME)

    assert review.status == ValidationStatus.APPROVED
    assert review.result is semantic_result
    assert review.assigned_llm_score is None
    assert review.edit_note is None


def test_prompt_for_human_review_correct_uses_edited_result():
    semantic_result = make_semantic_result(description="original")

    with patch("builtins.input", side_effect=["c", "edited description", "", "n", "0.5", "looked wrong"]):
        review = prompt_for_human_review(RAW_ATTACK, SEMANTIC_CONTEXT, semantic_result, TEMPLATE_NAME)

    assert review.status == ValidationStatus.CORRECTED
    assert review.result.description == "edited description"
    assert review.assigned_llm_score == 0.5
    assert review.edit_note == "looked wrong"


def test_prompt_for_human_review_reject_has_no_result():
    with patch("builtins.input", side_effect=["r", "0.1", "totally wrong"]):
        review = prompt_for_human_review(RAW_ATTACK, SEMANTIC_CONTEXT, make_semantic_result(), TEMPLATE_NAME)

    assert review.status == ValidationStatus.REJECTED
    assert review.result is None


def test_prompt_for_human_review_reprompts_on_invalid_menu_choice():
    with patch("builtins.input", side_effect=["bogus", "a", "", ""]):
        review = prompt_for_human_review(RAW_ATTACK, SEMANTIC_CONTEXT, make_semantic_result(), TEMPLATE_NAME)

    assert review.status == ValidationStatus.APPROVED


def test_prompt_for_human_review_rerun_then_approve_uses_reclassified_result():
    original_result = make_semantic_result(description="original")
    reclassified_result = make_semantic_result(description="reclassified", move_type=MoveType.MAGICAL)

    with patch(
        "monsterforge.entrypoints._review_input.classify_attack", return_value=reclassified_result,
    ), patch(
        "builtins.input",
        side_effect=[
            "re",                     # choose rerun
            "please reconsider",      # rerun note
            "",                       # keep current template
            "a",                      # approve after rerun
            "", "",                   # skip score/note
        ],
    ):
        review = prompt_for_human_review(RAW_ATTACK, SEMANTIC_CONTEXT, original_result, TEMPLATE_NAME)

    assert review.status == ValidationStatus.APPROVED
    assert review.result.description == "reclassified"
    assert review.result.move_type == MoveType.MAGICAL


def test_prompt_for_human_review_failed_rerun_keeps_original_result_and_reprompts():
    original_result = make_semantic_result(description="original")

    with patch(
        "monsterforge.entrypoints._review_input.classify_attack",
        side_effect=RuntimeError("boom"),
    ), patch(
        "builtins.input",
        side_effect=[
            "re",             # choose rerun
            "",               # no note
            "",               # keep current template
            "a",              # after the failed rerun, approve the original result
            "", "",
        ],
    ):
        review = prompt_for_human_review(RAW_ATTACK, SEMANTIC_CONTEXT, original_result, TEMPLATE_NAME)

    assert review.status == ValidationStatus.APPROVED
    assert review.result is original_result
