"""
Human-in-the-loop review of an LLM semantic classification.

Sits between llm.semantic_classification.attacks.classify_attack() and
parsing.dnd.v3x.structured_conversions.attacks.attacks_converter.
raw_to_structured_attack() in the pipeline: needs_review() decides
whether a classification's confidence warrants showing it to a human
before the deterministic conversion stages proceed; HumanReview records
what came out of that review, if it happened.
"""
from dataclasses import dataclass
from monsterforge.config import validation_settings
from monsterforge.llm.semantic_classification.attacks import AttackSemanticResult
from monsterforge.validation.enums import ValidationStatus


# =====================
# REVIEW GATE
# =====================
def needs_review(*, confidence: float) -> bool:
    """
    Decide whether a classification's confidence requires human review.

    Rules:
    - Always True when validation_settings.ALWAYS_ON is set, regardless
      of confidence.
    - Otherwise True only when confidence falls below
      validation_settings.CONFIDENCE_THRESHOLD.

    NOTE:
    Reads validation_settings.ALWAYS_ON/CONFIDENCE_THRESHOLD through the
    module (not via `from ... import ALWAYS_ON`) so a value changed at
    runtime is actually picked up here — an import-by-value would freeze
    a stale copy at import time instead.
    """
    return validation_settings.ALWAYS_ON or confidence < validation_settings.CONFIDENCE_THRESHOLD


# =====================
# HUMAN REVIEW
# =====================
@dataclass(kw_only=True)
class HumanReview:
    """
    Outcome of a human review of an AttackSemanticResult.

    result is None only when status is REJECTED: no card should be
    produced downstream in that case. On APPROVED it is the original,
    unmodified classification; on CORRECTED it is the edited version
    the reviewer submitted.
    """
    status: ValidationStatus
    result: AttackSemanticResult | None
    assigned_llm_score: float | None = None  # the reviewer's own score of the classification, distinct from the LLM's own self-reported confidence
    edit_note: str | None = None             # the reviewer's explanation for a correction or rejection, the human counterpart to the LLM's own rationale
