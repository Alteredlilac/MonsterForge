"""
Shared interactive helper for choosing which classify_attack prompt
template a classification should run against, from the curated set in
llm.semantic_classification.attacks.ATTACK_PROMPT_TEMPLATE_OPTIONS.

Public (not underscore-prefixed) function: used by convert_attack_cli.py
for the initial classification and by _review_input.py's rerun for a
reclassification — two separate modules from the start, unlike most of
this package's helpers which start private and get promoted later.
"""
from monsterforge.llm.semantic_classification.attacks import ATTACK_PROMPT_TEMPLATE_OPTIONS


def prompt_for_template_choice() -> str:
    """
    Ask which classify_attack prompt template to use, numbered by
    ATTACK_PROMPT_TEMPLATE_OPTIONS order. Blank input keeps the default
    (option 1). Re-prompts on anything that isn't a valid option number
    — template paths are long enough that typing one out exactly isn't
    a realistic alternative input style here.
    """
    print("Available prompt templates:")
    for index, option in enumerate(ATTACK_PROMPT_TEMPLATE_OPTIONS, start=1):
        print(f"  {index}. {option.label} — {option.description}")

    default_path = ATTACK_PROMPT_TEMPLATE_OPTIONS[0].path

    while True:
        text = input(f"Template [1-{len(ATTACK_PROMPT_TEMPLATE_OPTIONS)}, default 1]: ").strip()

        if not text:
            return default_path

        if text.isdigit() and 1 <= int(text) <= len(ATTACK_PROMPT_TEMPLATE_OPTIONS):
            return ATTACK_PROMPT_TEMPLATE_OPTIONS[int(text) - 1].path

        print(f"Enter a number between 1 and {len(ATTACK_PROMPT_TEMPLATE_OPTIONS)}, or press Enter for the default.")
