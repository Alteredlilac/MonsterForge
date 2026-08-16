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
from ._semantic_context_input import prompt_for_semantic_context
from ._llm_model_selection import ensure_model_available, call_llm_with_model_fallback


# =====================
# CONFIGURATION
# =====================
PROMPTS_DIR = Path(__file__).resolve().parents[1] / "llm" / "prompts"
DEFAULT_TEMPLATE = "attacks/classify_attack.jinja2"


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
    semantic_context = prompt_for_semantic_context()

    context = {
        "raw_attack": raw_attack,
        "additional_description": semantic_context.additional_description,
        "creature_description": semantic_context.creature_description,
        "creature_subtype": semantic_context.creature_subtype,
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
