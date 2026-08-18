"""
Standalone entry point: render every move_card already collected in
output/real_pipeline_conversion_samples_with_context.json into a static
HTML page via rendering.move_card_renderer.render_move_card_html(), plus
an index page to browse the results.

Deliberately reuses already-collected real-API pipeline output instead of
making new LLM calls: this script is pure, deterministic rendering over
existing data, so it runs in well under a second for all 65 samples and
has no quota/rate-limit concerns, unlike collect_real_pipeline_conversions.py.

This is a manual visual QA tool, not part of the automated test suite —
tests/rendering/test_move_card_renderer.py is the actual regression
safety net for render_move_card_html() itself (see that file for why: an
exact-match assertion against 65 rendered pages would break on every
template/CSS tweak, which is noise, not signal). This script exists so a
person can eyeball the renderer against real, varied pipeline output —
range/no range, bonus cards/no bonus cards, physical/magical — rather
than only the handful of hand-built cases used in the pytest suite.

Usage:
    python -m monsterforge.entrypoints.render_sample_cards
"""
import json
import re
from pathlib import Path

from monsterforge.rendering.move_card_renderer import render_move_card_html

INPUT_PATH = Path(__file__).parent / "output" / "real_pipeline_conversion_samples_with_context.json"
OUTPUT_DIR = Path(__file__).parent / "output" / "rendered_cards"


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "unnamed"


def _build_index_html(entries: list[dict]) -> str:
    rows = "\n".join(
        f'<li><a href="{entry["filename"]}">{entry["name"]}</a>'
        f' <span class="meta">{entry["move_type"]} / {entry["category"]}</span></li>'
        for entry in entries
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Rendered MoveCard samples</title>
<style>
  body {{ font-family: Georgia, serif; background: #2b2b2b; color: #e8ddc4; padding: 2rem; }}
  h1 {{ font-size: 1.2rem; }}
  ul {{ list-style: none; padding: 0; max-width: 480px; }}
  li {{ padding: 6px 0; border-bottom: 1px solid #555; }}
  a {{ color: #e8ddc4; text-decoration: none; font-weight: bold; }}
  a:hover {{ text-decoration: underline; }}
  .meta {{ color: #999; font-size: 0.8rem; margin-left: 8px; }}
</style>
</head>
<body>
<h1>Rendered MoveCard samples ({len(entries)})</h1>
<ul>
{rows}
</ul>
</body>
</html>
"""


def render_sample_cards() -> None:
    data = json.loads(INPUT_PATH.read_text())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    index_entries = []
    skipped = 0
    for position, sample in enumerate(data["samples"], start=1):
        move_card = sample["move_card"]
        if move_card is None:
            skipped += 1
            continue

        filename = f"{position:02d}_{_slugify(move_card['name'])}.html"
        html = render_move_card_html(move_card)
        (OUTPUT_DIR / filename).write_text(html)
        index_entries.append({
            "filename": filename,
            "name": move_card["name"],
            "move_type": move_card["move_type"],
            "category": move_card["category"],
        })

    (OUTPUT_DIR / "index.html").write_text(_build_index_html(index_entries))
    print(f"Rendered {len(index_entries)} cards, skipped {skipped} (no move_card), "
          f"index at {OUTPUT_DIR / 'index.html'}")


if __name__ == "__main__":
    render_sample_cards()
