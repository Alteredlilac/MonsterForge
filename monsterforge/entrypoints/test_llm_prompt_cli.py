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
from ._raw_attack_input import prompt_for_raw_attack

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "llm" / "prompts"
DEFAULT_TEMPLATE = "attacks/classify_attack.jinja2"


def render_prompt(template_relative_path: str, context: dict) -> str:
    """Render a Jinja2 template from llm/prompts/ with the given context."""
    environment = Environment(
        loader=FileSystemLoader(PROMPTS_DIR),
        autoescape=False,  # Prompts are plain text, not HTML
    )
    template = environment.get_template(template_relative_path)
    return template.render(**context)


def main() -> None:
    template_path = input(
        f"Template path relative to llm/prompts/ [{DEFAULT_TEMPLATE}]: "
    ).strip() or DEFAULT_TEMPLATE

    print("Provide the attack used to build the prompt context:")
    raw_attack = prompt_for_raw_attack()
    additional_description = input("Additional description (optional): ").strip() or None
    creature_description = input("Creature description (optional): ").strip() or None

    context = {
        "raw_attack": raw_attack,
        "additional_description": additional_description,
        "creature_description": creature_description,
        "creature_subtype": None,
    }

    prompt = render_prompt(template_path, context)
    print("\n--- PROMPT ---")
    print(prompt)

    response = get_llm_client().generate_text(prompt)
    print("\n--- LLM RESPONSE ---")
    print(response)


if __name__ == "__main__":
    main()
