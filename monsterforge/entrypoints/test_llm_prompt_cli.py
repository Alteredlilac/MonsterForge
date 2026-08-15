"""
Standalone entry point: render a Jinja2 prompt template with real input
and send it to the configured LLM client, printing both the rendered
prompt and the raw response.

render_prompt() is not limited to the attack-classification template —
template path and context are both parameters — so it stays usable as
new templates (feats, spells, special qualities...) are added. The
interactive main() below only knows how to collect context for the one
template that exists today.

Usage:
    python -m monsterforge.entrypoints.test_llm_prompt_cli
"""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from monsterforge.llm.client import get_llm_client
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype
from ._raw_attack_input import prompt_for_raw_attack
from ._llm_model_selection import ensure_model_available, call_llm_with_model_fallback


# =====================
# CONFIGURATION
# =====================
PROMPTS_DIR = Path(__file__).resolve().parents[1] / "llm" / "prompts"
DEFAULT_TEMPLATE = "attacks/classify_attack.jinja2"


# =====================
# HELPERS
# =====================
def prompt_for_creature_subtype() -> CreatureSubtype | None:
    """Ask for an optional creature subtype, re-prompting on invalid input.

    CreatureSubtype is a (str, Enum), so the raw text maps directly onto
    a member's value (e.g. "incorporeal" -> CreatureSubtype.INCORPOREAL).
    """
    while True:
        text = input("Creature subtype (optional, e.g. incorporeal): ").strip().lower()

        if not text:
            return None

        try:
            return CreatureSubtype(text)
        except ValueError:
            valid_values = ", ".join(member.value for member in CreatureSubtype)
            print(f"Unknown creature subtype {text!r}. Valid values: {valid_values}")


def prompt_for_multiple_creature_subtypes() -> list[CreatureSubtype]:
    """
    Ask for multiple optional creature subtypes until an empty input.

    Each subtype is validated individually by prompt_for_creature_subtype().
    """
    subtypes = []

    while True:
        print("Enter creature subtypes one at a time (press Enter to finish).")
        subtype = prompt_for_creature_subtype()

        if subtype is None:
            return subtypes

        subtypes.append(subtype)


def resolve_relevant_creature_subtype(
        subtypes: list[CreatureSubtype]) -> CreatureSubtype | None:
    """
    Reduce a list of entered subtypes to the single value
    classify_attack.jinja2 actually branches on.

    NOTE:
    The template's classification rule currently only checks for
    "incorporeal" ("always classify as magical"). Only that subtype is
    surfaced here, even if the user enters several — matching what
    AttackSemanticContext.creature_subtype (a single optional value, not
    a list) can express in the real classify_attack() pipeline today.
    A creature having multiple subtypes at once is common in D&D, but
    modeling that properly belongs to AttackSemanticContext itself, not
    to this test entry point. If the template's rules grow to depend on
    other subtypes, extend this function accordingly.
    """
    if CreatureSubtype.INCORPOREAL in subtypes:
        return CreatureSubtype.INCORPOREAL

    return None

# =====================
# RENDER PROMPT
# =====================
def render_prompt(template_relative_path: str, context: dict) -> str:
    """Render a Jinja2 template from llm/prompts/ with the given context."""
    environment = Environment(
        loader=FileSystemLoader(PROMPTS_DIR),
        autoescape=False,  # Prompts are plain text, not HTML
    )
    template = environment.get_template(template_relative_path)
    return template.render(**context)


# =====================
# MAIN
# =====================
def main() -> None:
    ensure_model_available()

    template_path = input(
        f"Template path relative to llm/prompts/ [{DEFAULT_TEMPLATE}]: "
    ).strip() or DEFAULT_TEMPLATE

    print("Provide the attack used to build the prompt context:")
    raw_attack = prompt_for_raw_attack()
    additional_description = input("Additional description (optional): ").strip() or None
    creature_description = input("Creature description (optional): ").strip() or None
    entered_subtypes = prompt_for_multiple_creature_subtypes()
    creature_subtype = resolve_relevant_creature_subtype(entered_subtypes)

    context = {
        "raw_attack": raw_attack,
        "additional_description": additional_description,
        "creature_description": creature_description,
        "creature_subtype": creature_subtype,
    }

    prompt = render_prompt(template_path, context)
    print("\n--- PROMPT ---")
    print(prompt)

    response = call_llm_with_model_fallback(
        lambda: get_llm_client().generate_text(prompt)
    )
    print("\n--- LLM RESPONSE ---")
    print(response)


if __name__ == "__main__":
    main()
