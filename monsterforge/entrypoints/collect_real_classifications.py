"""
Standalone entry point: run every case in SAMPLE_ATTACKS through the
real classify_attack() pipeline (actual Gemini API calls, not mocked)
and save both the raw LLM response and the parsed AttackSemanticResult
for human review.

NOT part of the automated test suite. This makes ~65 real, deliberate
API calls, takes several minutes, consumes API quota, and its results
are not deterministic — re-running can change rationale text, and
occasionally confidence or even move_type on borderline cases. It
exists to produce real observational data to review by hand, and to
occasionally hand-pick individual examples into mocked unit tests — the
output file itself is never imported or asserted against by a test,
unlike tests/parsing/dnd/v3x/structured_conversions/attacks/
expected_attack_effects.py (a genuine, hand-validated regression
fixture for the deterministic parser, not the LLM).

Usage:
    python -m monsterforge.entrypoints.collect_real_classifications
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.llm.client import get_llm_client
from monsterforge.serialization.plain_data import to_plain
from .sample_attacks import SAMPLE_ATTACKS
from ._llm_model_selection import ensure_model_available, call_llm_with_model_fallback
from ._llm_response_capture import classify_with_raw_response


# =====================
# CONFIGURATION
# =====================
# NOTE:
# The real per-minute rate limit for this API key/tier is unknown (free
# tier limits vary by model and account, and can change without notice
# — see docs/LLM_ARCHITECTURE.md). 5 seconds is a deliberately
# conservative default, not a value derived from a confirmed quota.
# Raise it if 429s are still observed; lower it only if the actual
# limit for this account is known to allow a faster pace.
DELAY_SECONDS = 5

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_PATH = OUTPUT_DIR / "real_llm_classification_samples.json"


# =====================
# MAIN
# =====================
def main() -> None:
    ensure_model_available()

    samples = []

    for index, case in enumerate(SAMPLE_ATTACKS):
        raw_attack = RawAttack(**case)
        label = case.get("name") or "(blank case)"
        print(f"[{index + 1}/{len(SAMPLE_ATTACKS)}] {label}...")

        try:
            result, raw_response = call_llm_with_model_fallback(
                lambda: classify_with_raw_response(raw_attack)
            )
            samples.append({
                "case": case,
                "raw_response": raw_response,
                "parsed_result": to_plain(result),
                "error": None,
            })
        except Exception as exc:
            # NOTE:
            # Deliberately broad: this is a long batch run against a
            # real, imperfect API. One case's failure (malformed JSON,
            # a transient network error, an exhausted model list) is
            # recorded and the run continues — losing everything
            # collected so far over one bad case would defeat the
            # purpose of a collection script.
            samples.append({
                "case": case,
                "raw_response": None,
                "parsed_result": None,
                "error": str(exc),
            })

        if index < len(SAMPLE_ATTACKS) - 1:
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
