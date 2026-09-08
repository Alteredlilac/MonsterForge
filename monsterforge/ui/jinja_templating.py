"""
Jinja2 templating setup, shared by every ui/ route module.

Named jinja_templating.py rather than templates.py to avoid colliding
with the sibling ui/templates/ directory that holds the actual
.jinja2 files -- two different things with the same name in the same
package would be ambiguous.
"""
from pathlib import Path
import jinja2
from fastapi.templating import Jinja2Templates

# NOTE:
# Jinja2Templates(directory=...) hardcodes autoescape=jinja2.select_autoescape(),
# whose extension check never matches "*.html.jinja2" (every template in
# this project) — the same silent-autoescape-off gap already found in
# rendering/move_card_renderer.py, undiscovered here until a rationale
# containing an apostrophe broke the hidden semantic_result_json field.
# Passing an explicit env= with autoescape=True is the only way to
# override that default.
templates = Jinja2Templates(env=jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=True,
))
