"""
Interactive human review of an LLM attack classification (MVP 0.5).

Implements the ReviewHandler shape pipeline.attack_pipeline.convert_attack()
calls when validation.review.needs_review() says a classification's
confidence warrants a human look before the deterministic conversion
stages proceed. Only the enum-typed fields of AttackSemanticResult
(move_type, move_range.range_unit_system) are corrected via a
dropdown-style prompt; description and move_range.effect_range are free
text/numeric, since they aren't constrained to a fixed vocabulary.
"""
import dataclasses
from enum import Enum
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.llm.semantic_classification.attacks import (
    AttackSemanticResult,
    SemanticContextInput,
)
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import MoveType, UnitSystem
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import HumanReview


# =====================
# SHARED PROMPTS
# =====================
def _prompt_enum_choice(prompt: str, enum_cls: type[Enum], current: Enum) -> Enum:
    """Prompt for an enum value, defaulting to `current` on blank input."""
    valid_values = ", ".join(member.value for member in enum_cls)

    while True:
        text = input(f"{prompt} [{current.value}] ({valid_values}): ").strip().lower()

        if not text:
            return current

        try:
            return enum_cls(text)
        except ValueError:
            print(f"Unknown value {text!r}. Valid values: {valid_values}")


def _prompt_optional_float(prompt: str) -> float | None:
    text = input(prompt).strip()

    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        print("Not a valid number, skipping.")
        return None


def _prompt_optional_text(prompt: str) -> str | None:
    return input(prompt).strip() or None


# =====================
# CONTEXT DISPLAY
# =====================
def _print_review_context(
        raw_attack: RawAttack,
        semantic_context: SemanticContextInput,
        semantic_result: AttackSemanticResult,
        template_name: str) -> None:
    print("\n--- Human review requested ---")
    print(f"Template: {template_name}")
    print(f"Raw attack: name={raw_attack.name!r}, modifier={raw_attack.modifier!r}, "
          f"attack_type={raw_attack.attack_type!r}, attack_effect={raw_attack.attack_effect!r}")
    print(f"Context: additional_description={semantic_context.additional_description!r}, "
          f"creature_description={semantic_context.creature_description!r}, "
          f"creature_subtype={semantic_context.creature_subtype}")
    print(f"Classification: description={semantic_result.description!r}, "
          f"move_type={semantic_result.move_type.value}, move_range={semantic_result.move_range}")
    print(f"Confidence: {semantic_result.confidence}")
    print(f"Rationale: {semantic_result.rationale}")
    print("-------------------------------")


# =====================
# CORRECTION
# =====================
def _prompt_move_range_correction(current: EffectRange | None) -> EffectRange | None:
    current_display = f"{current.effect_range} {current.range_unit_system.value}" if current else "none"
    edit = input(f"Correct range too? current: {current_display} [y/N]: ").strip().lower()

    if edit != "y":
        return current

    value_text = input("Range value (integer): ").strip()
    value = int(value_text) if value_text else (current.effect_range if current else 0)
    default_unit = current.range_unit_system if current else UnitSystem.METRIC
    unit = _prompt_enum_choice("Range unit", UnitSystem, default_unit)

    return EffectRange(effect_range=value, range_unit_system=unit)


def _prompt_correction(current: AttackSemanticResult) -> AttackSemanticResult:
    description = input(f"Description [{current.description}]: ").strip() or current.description
    move_type = _prompt_enum_choice("Move type", MoveType, current.move_type)
    move_range = _prompt_move_range_correction(current.move_range)

    return dataclasses.replace(current, description=description, move_type=move_type, move_range=move_range)


# =====================
# REVIEW
# =====================
def prompt_for_human_review(
        raw_attack: RawAttack,
        semantic_context: SemanticContextInput,
        semantic_result: AttackSemanticResult,
        template_name: str) -> HumanReview:
    """
    Show a low-confidence classification to a human and collect their
    decision. Matches the ReviewHandler shape expected by
    pipeline.attack_pipeline.convert_attack().

    Rules:
    - [a]pprove keeps semantic_result unchanged.
    - [c]orrect lets the reviewer edit description (free text), move_type
      (dropdown), and optionally move_range (numeric value + dropdown unit).
    - [r]eject produces a HumanReview with result=None: convert_attack()
      stops there, no card is generated.
    - Every branch may optionally record assigned_llm_score and edit_note.
    """
    _print_review_context(raw_attack, semantic_context, semantic_result, template_name)

    while True:
        choice = input("[a]pprove / [c]orrect / [r]eject: ").strip().lower()

        if choice in ("a", "c", "r"):
            break

        print("Please enter 'a', 'c', or 'r'.")

    if choice == "a":
        return HumanReview(
            status=ValidationStatus.APPROVED,
            result=semantic_result,
            assigned_llm_score=_prompt_optional_float("Score for this classification (optional): "),
            edit_note=_prompt_optional_text("Note (optional): "),
        )

    if choice == "c":
        corrected_result = _prompt_correction(semantic_result)
        return HumanReview(
            status=ValidationStatus.CORRECTED,
            result=corrected_result,
            assigned_llm_score=_prompt_optional_float("Score for the original classification (optional): "),
            edit_note=_prompt_optional_text("Why did you correct it? (optional): "),
        )

    return HumanReview(
        status=ValidationStatus.REJECTED,
        result=None,
        assigned_llm_score=_prompt_optional_float("Score for this classification (optional): "),
        edit_note=_prompt_optional_text("Why did you reject it? (optional): "),
    )
