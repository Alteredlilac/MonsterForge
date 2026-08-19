"""
Renders a browsable gallery of many MoveCards on a single static page,
with a Bootstrap modal per card exposing raw input, semantic
classification, and JSON for drill-down.

Each card fragment is rendered once, in Python, via the same
move_card_fragment template and build_card_context() used by
render_move_card_html() — so the gallery and the standalone page always
show the identical card visual. The rendered fragment is embedded as a
pre-built HTML string rather than nesting a per-entry Jinja2 include:
Jinja2's include-with-context inherits the *whole* surrounding scope, it
does not let a loop iteration cleanly hand one dict's keys to the
fragment as flat top-level variable names — composing the strings in
Python sidesteps that entirely.
"""
import json

from monsterforge.rendering.move_card_renderer import build_card_context, environment

_fragment_template = environment.get_template("move_card_fragment.html.jinja2")


def _build_gallery_entry(index: int, sample: dict) -> dict:
    move_card = sample["move_card"]
    card_html = _fragment_template.render(**build_card_context(move_card))
    return {
        "index": index,
        "name": move_card["name"],
        "move_type": move_card["move_type"],
        "category": move_card["category"],
        "card_html": card_html,
        "raw_input_json": json.dumps(sample.get("case"), indent=2),
        "context_json": json.dumps(sample.get("context"), indent=2),
        "raw_response": sample.get("raw_response") or "",
        "confidence": sample.get("confidence"),
        "rationale": sample.get("rationale") or "",
        "move_card_json": json.dumps(move_card, indent=2),
    }


def render_gallery_html(samples: list[dict]) -> str:
    """
    Render a gallery page from a list of pipeline sample entries.

    Each sample is expected to have the same shape as one item of
    real_pipeline_conversion_samples_with_context.json's "samples" list:
    {"case", "context", "raw_response", "confidence", "rationale",
    "move_card"}. Samples with move_card=None (e.g. the intentional
    blank-case placeholder) are skipped.
    """
    template = environment.get_template("gallery.html.jinja2")
    entries = [
        _build_gallery_entry(index, sample)
        for index, sample in enumerate(samples, start=1)
        if sample.get("move_card") is not None
    ]
    return template.render(entries=entries)
