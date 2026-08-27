"""
Standalone entry point: build the portfolio-facing MoveCard gallery page
from output/real_pipeline_conversion_samples_with_context.json.

Distinct from render_sample_cards.py on purpose: that script is a manual
QA tool (one plain file per card, a bare link list), built to let a
person eyeball the renderer against real pipeline output while building
MVP 0.2. This script produces the actual portfolio artifact for MVP 0.3
— a single browsable page (grid + per-card drill-down modal) meant to be
shown, not just used for review. Same underlying data, different
purpose, so kept separate rather than folded into one script.

Usage:
    python -m monsterforge.entrypoints.render_gallery
"""
import json
from pathlib import Path

from monsterforge.rendering.gallery_renderer import render_gallery_html

INPUT_PATH = Path(__file__).parent / "output" / "real_pipeline_conversion_samples_with_context_160char_blank_fixed_damage_fixed.json"
OUTPUT_DIR = Path(__file__).parent / "output" / "gallery"
OUTPUT_PATH = OUTPUT_DIR / "gallery.html"


def render_gallery() -> None:
    data = json.loads(INPUT_PATH.read_text())
    html = render_gallery_html(data["samples"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html)
    print(f"Gallery written to {OUTPUT_PATH}")


if __name__ == "__main__":
    render_gallery()
