"""
Standalone entry point: run every case in SAMPLE_ATTACKS_WITH_CONTEXT
through the complete conversion pipeline (classify_attack ->
raw_to_structured_attack -> attack_converter, actual Gemini API calls,
not mocked) and save the raw LLM response, the classification metadata
that doesn't survive into the final MoveCard (confidence, rationale),
and the resulting MoveCard for human review.

Deliberately a separate script from collect_real_classifications.py,
not a variant reusing its already-collected data: this one exercises
the deterministic layers downstream of classification
(raw_to_structured_attack, attack_converter) against real LLM output,
and — since it makes its own independent round of API calls — its
results can be diffed against collect_real_classifications.py's output
to see how much a real classification varies run to run, including
whether the model's self-reported confidence is at all stable rather
than just plausible-looking.

Runs with full semantic context (additional_description,
creature_description, creature_subtype) rather than the bare attack,
unlike the original run whose output is preserved at
output/real_pipeline_conversion_samples.json — writing to a
differently-named output file here keeps that run available as the
"without context" baseline for comparison, rather than overwriting it.

NOT part of the automated test suite — see collect_real_classifications.py
for why (real API calls, non-deterministic, several minutes, quota use).

Usage:
    python -m monsterforge.entrypoints.collect_real_pipeline_conversions
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import (
    raw_to_structured_attack,
)
from monsterforge.transformation.dnd.v3x.converters.attacks_converter import attack_converter
from monsterforge.llm.client import get_llm_client
from monsterforge.serialization.domain_to_json import card_to_json
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype
from .sample_attacks_with_context import SAMPLE_ATTACKS_WITH_CONTEXT
from ._llm_model_selection import ensure_model_available, call_llm_with_model_fallback
from ._llm_response_capture import classify_with_raw_response


# =====================
# CONFIGURATION
# =====================
# NOTE:
# Deliberately independent from collect_real_classifications.py's
# DELAY_SECONDS, even though the value is currently the same — see that
# module for why 5s is a conservative default, not a confirmed quota.
DELAY_SECONDS = 5

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_PATH = OUTPUT_DIR / "real_pipeline_conversion_samples_with_context.json"


# =====================
# CONVERT WITH CAPTURE
# =====================
def _convert_with_capture(
        raw_attack: RawAttack,
        *,
        additional_description: str | None,
        creature_description: str | None,
        creature_subtype: CreatureSubtype | None,
        ) -> dict:
    """
    Run raw_attack through the full conversion pipeline, capturing the
    raw LLM response and the classification metadata (confidence,
    rationale) that classify_attack() produces but MoveCard does not
    retain, alongside the final card.

    card_to_json() is used for the final card (not to_plain()) so that
    nested reference cards (e.g. a "Trip" special attack in
    cards_to_add) are reduced to {name, id}, matching what the API will
    actually return. Their full detail is deterministic conversion
    logic already covered by its own tests, not something this
    LLM-focused review needs to re-inspect every case.
    """
    semantic_result, raw_response = classify_with_raw_response(
        raw_attack,
        additional_description=additional_description,
        creature_description=creature_description,
        creature_subtype=creature_subtype,
    )
    structured_attack = raw_to_structured_attack(raw_attack, semantic_result)
    move_card = attack_converter(structured_attack)

    return {
        "raw_response": raw_response,
        "confidence": semantic_result.confidence,
        "rationale": semantic_result.rationale,
        "move_card": json.loads(card_to_json(move_card)),
    }


# =====================
# MAIN
# =====================
def main() -> None:
    ensure_model_available()

    samples = []
    total = len(SAMPLE_ATTACKS_WITH_CONTEXT)

    for index, entry in enumerate(SAMPLE_ATTACKS_WITH_CONTEXT):
        case = entry["raw_attack"]
        context = entry["context"]
        raw_attack = RawAttack(**case)
        subtype_text = context["creature_subtype"]
        creature_subtype = CreatureSubtype(subtype_text) if subtype_text else None
        label = case.get("name") or "(blank case)"
        print(f"[{index + 1}/{total}] {label}...")

        try:
            captured = call_llm_with_model_fallback(
                lambda: _convert_with_capture(
                    raw_attack,
                    additional_description=context["additional_description"],
                    creature_description=context["creature_description"],
                    creature_subtype=creature_subtype,
                )
            )
            samples.append({"case": case, "context": context, **captured, "error": None})
        except Exception as exc:
            # NOTE:
            # Deliberately broad, same reasoning as
            # collect_real_classifications.py: this covers LLM/parsing
            # failures as well as pipeline-specific ones (e.g.
            # UnknownAttackRange for a ranged attack the LLM didn't
            # supply a range for and that isn't in KNOWN_ATTACKS) — one
            # bad case is recorded, not allowed to lose the rest of a
            # several-minute batch run.
            samples.append({
                "case": case,
                "context": context,
                "raw_response": None,
                "confidence": None,
                "rationale": None,
                "move_card": None,
                "error": str(exc),
            })

        if index < total - 1:
            time.sleep(DELAY_SECONDS)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(
        {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "model": get_llm_client().model_name,
                "sample_count": len(samples),
            },
            "samples": samples,
        },
        indent=2,
    ))

    error_count = sum(1 for sample in samples if sample["error"] is not None)
    print(f"\nWrote {len(samples)} samples to {OUTPUT_PATH} ({error_count} errors).")


if __name__ == "__main__":
    main()
