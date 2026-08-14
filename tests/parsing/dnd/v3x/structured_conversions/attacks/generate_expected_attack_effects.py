"""
Driver script wiring SAMPLE_ATTACKS + get_attack_effects() into the
generic tests/tools/generate_expected_outputs.py tool.

Run manually whenever the deterministic attack-effect parsing changes on
purpose, then review and hand-correct expected_attack_effects.py before
committing it:

    python -m tests.parsing.dnd.v3x.structured_conversions.attacks.generate_expected_attack_effects
"""
from pathlib import Path
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_effects_parser import (
    get_attack_effects,
)
from tests.parsing.dnd.v3x.structured_conversions.sample_attacks import SAMPLE_ATTACKS
from tests.tools.generate_expected_outputs import generate_expected_outputs

OUTPUT_PATH = Path(__file__).parent / "expected_attack_effects.py"


def _compute(case: dict) -> object:
    return get_attack_effects(RawAttack(**case))


if __name__ == "__main__":
    generate_expected_outputs(
        cases=SAMPLE_ATTACKS,
        compute_fn=_compute,
        output_path=OUTPUT_PATH,
        variable_name="EXPECTED_ATTACK_EFFECTS",
    )
    print(f"Wrote {OUTPUT_PATH} — review by hand before trusting it.")
