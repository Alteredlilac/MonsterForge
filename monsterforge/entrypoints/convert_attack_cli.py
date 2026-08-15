"""
Standalone entry point: collect a raw D&D 3.x attack interactively, run
it through the MVP zero conversion pipeline, and print the resulting
MoveCard as JSON.

Usage:
    python -m monsterforge.entrypoints.convert_attack_cli
"""
from monsterforge.pipeline.attack_pipeline import convert_attack
from monsterforge.serialization.domain_to_json import card_to_json
from ._raw_attack_input import prompt_for_raw_attack
from ._llm_model_selection import ensure_model_available, call_llm_with_model_fallback


def main() -> None:
    ensure_model_available()
    raw_attack = prompt_for_raw_attack()
    move_card = call_llm_with_model_fallback(lambda: convert_attack(raw_attack))
    print(card_to_json(move_card))


if __name__ == "__main__":
    main()
