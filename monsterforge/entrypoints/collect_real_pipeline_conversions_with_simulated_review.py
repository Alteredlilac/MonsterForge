"""
Standalone entry point: run every case in SAMPLE_ATTACKS_WITH_CONTEXT
through the full conversion pipeline (pipeline.attack_pipeline.
convert_attack(), actual Gemini API calls, not mocked) with human
review forced on for every case, using a deterministic, non-interactive
review_handler instead of a real reviewer at a terminal.

This is MVP 0.6's observational run: no real human reviews these 65
cases — SimulatedReviewer exists purely to exercise the review gate's
three outcomes (APPROVED/CORRECTED/REJECTED) against real pipeline
output, and to confirm the whole mechanism (validation_settings.
ALWAYS_ON, needs_review(), the review_handler seam, the blank-attack
short-circuit) behaves correctly end to end. It is not a source of
genuine review data — see the "simulated" naming throughout, chosen
deliberately so this output is never mistaken for real human review.

NOT part of the automated test suite — see collect_real_classifications.py
for why (real API calls, non-deterministic, several minutes, quota use).

Usage:
    python -m monsterforge.entrypoints.collect_real_pipeline_conversions_with_simulated_review
"""
import dataclasses
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from monsterforge.config import validation_settings
from monsterforge.llm.client import get_llm_client
from monsterforge.llm.semantic_classification.attacks import AttackSemanticResult, SemanticContextInput
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.pipeline.attack_pipeline import convert_attack
from monsterforge.serialization.domain_to_json import card_to_json
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import HumanReview
from .sample_attacks_with_context import SAMPLE_ATTACKS_WITH_CONTEXT
from ._llm_model_selection import ensure_model_available, call_llm_with_model_fallback


# =====================
# CONFIGURATION
# =====================
DELAY_SECONDS = 5

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_PATH = OUTPUT_DIR / "real_pipeline_conversions_with_simulated_review.json"


# =====================
# SERIALIZATION HELPERS
# =====================
def _move_range_to_dict(move_range: EffectRange | None) -> dict | None:
    if move_range is None:
        return None

    return {"effect_range": move_range.effect_range, "range_unit_system": move_range.range_unit_system.value}


def _semantic_result_to_dict(semantic_result: AttackSemanticResult) -> dict:
    return {
        "description": semantic_result.description,
        "move_type": semantic_result.move_type.value,
        "move_range": _move_range_to_dict(semantic_result.move_range),
        "confidence": semantic_result.confidence,
        "rationale": semantic_result.rationale,
    }


# =====================
# SIMULATED REVIEWER
# =====================
class SimulatedReviewer:
    """
    Deterministic, non-interactive review_handler for MVP 0.6.

    Cycles through APPROVED/CORRECTED/REJECTED by call order (not
    randomly, so a run is reproducible) rather than making a judgment
    call on classification quality — there is no real reviewer here.
    Every call is logged (the classification it saw, the review it
    produced) so the caller can inspect what happened per case after
    the run completes; convert_attack() itself doesn't expose this.
    """
    _OUTCOMES = (ValidationStatus.APPROVED, ValidationStatus.CORRECTED, ValidationStatus.REJECTED)

    def __init__(self):
        self.log: list[dict] = []

    def __call__(
            self,
            raw_attack: RawAttack,
            semantic_context: SemanticContextInput,
            semantic_result: AttackSemanticResult,
            template_name: str) -> HumanReview:
        status = self._OUTCOMES[len(self.log) % len(self._OUTCOMES)]
        review = self._build_review(status, semantic_result)

        self.log.append({
            "template_name": template_name,
            "semantic_context": {
                "additional_description": semantic_context.additional_description,
                "creature_description": semantic_context.creature_description,
                "creature_subtype": (
                    semantic_context.creature_subtype.value if semantic_context.creature_subtype else None
                ),
            },
            "original_classification": _semantic_result_to_dict(semantic_result),
            "simulated_review": {
                "status": review.status.value,
                "assigned_llm_score": review.assigned_llm_score,
                "edit_note": review.edit_note,
                "result": _semantic_result_to_dict(review.result) if review.result else None,
            },
        })

        return review

    @staticmethod
    def _build_review(status: ValidationStatus, semantic_result: AttackSemanticResult) -> HumanReview:
        if status == ValidationStatus.APPROVED:
            return HumanReview(status=status, result=semantic_result, assigned_llm_score=0.8, edit_note=None)

        if status == ValidationStatus.CORRECTED:
            corrected_result = dataclasses.replace(
                semantic_result,
                description=f"{semantic_result.description} [simulated correction for MVP 0.6]",
            )
            return HumanReview(
                status=status,
                result=corrected_result,
                assigned_llm_score=0.4,
                edit_note="Simulated correction for MVP 0.6 — no real reviewer judged this case.",
            )

        return HumanReview(
            status=status,
            result=None,
            assigned_llm_score=0.1,
            edit_note="Simulated rejection for MVP 0.6 — no real reviewer judged this case.",
        )


# =====================
# MAIN
# =====================
def main() -> None:
    ensure_model_available()
    validation_settings.ALWAYS_ON = True

    reviewer = SimulatedReviewer()
    samples = []
    total = len(SAMPLE_ATTACKS_WITH_CONTEXT)

    try:
        for index, entry in enumerate(SAMPLE_ATTACKS_WITH_CONTEXT):
            case = entry["raw_attack"]
            context = entry["context"]
            raw_attack = RawAttack(**case)
            subtype_text = context["creature_subtype"]
            creature_subtype = CreatureSubtype(subtype_text) if subtype_text else None
            label = case.get("name") or "(blank case)"
            print(f"[{index + 1}/{total}] {label}...")

            log_length_before = len(reviewer.log)

            try:
                move_card = call_llm_with_model_fallback(lambda: convert_attack(
                    raw_attack,
                    additional_description=context["additional_description"],
                    creature_description=context["creature_description"],
                    creature_subtype=creature_subtype,
                    review_handler=reviewer,
                ))
                review_entry = reviewer.log[log_length_before] if len(reviewer.log) > log_length_before else None
                samples.append({
                    "case": case,
                    "context": context,
                    "review": review_entry,
                    "move_card": json.loads(card_to_json(move_card)) if move_card is not None else None,
                    "error": None,
                })
            except Exception as exc:
                # NOTE:
                # Same broad-catch reasoning as collect_real_pipeline_conversions.py:
                # one bad case is recorded, not allowed to lose the rest of a
                # several-minute batch run.
                review_entry = reviewer.log[log_length_before] if len(reviewer.log) > log_length_before else None
                samples.append({
                    "case": case,
                    "context": context,
                    "review": review_entry,
                    "move_card": None,
                    "error": str(exc),
                })

            if index < total - 1:
                time.sleep(DELAY_SECONDS)
    finally:
        validation_settings.ALWAYS_ON = False

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(
        {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model": get_llm_client().model_name,
                "sample_count": len(samples),
                "note": "review outcomes are simulated (SimulatedReviewer), not from a real human reviewer",
            },
            "samples": samples,
        },
        indent=2,
    ))

    error_count = sum(1 for sample in samples if sample["error"] is not None)
    print(f"\nWrote {len(samples)} samples to {OUTPUT_PATH} ({error_count} errors).")


if __name__ == "__main__":
    main()
