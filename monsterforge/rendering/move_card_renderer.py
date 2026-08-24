"""
Renders a MoveCard's serialized data into a static HTML page.

Consumes the dict produced by serialization.domain_to_json.card_to_json()
(json.loads()'d back into a dict), not a raw domain MoveCard object. Per
PIPELINE_ARCHITECTURE.md decision 6, rendering shares the same
serialization stage as api/ rather than converting from domain/
independently, so nested card references (cards_to_add) already arrive
reduced to {"name", "id"} — no duplicate reduction logic needed here.
"""

from pathlib import Path

import jinja2

from monsterforge.rendering.labels import FIELD_LABELS, MOVE_TYPE_TO_COLOR_MAPPING

TEMPLATE_DIR = Path(__file__).parent / "templates"
MAX_EFFECT_ENTRIES = 3
MAX_BONUS_CARDS = 3

environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
    # NOTE:
    # Explicit True, not select_autoescape(["html"]) — every template in
    # this project is named "*.html.jinja2", so select_autoescape's
    # extension check (looking for a literal ".html" ending) never
    # matched and autoescape was silently off since MVP 0.2. Explicit
    # True can't regress the same way regardless of what a future
    # template is named.
    autoescape=True,
)


def format_move_effects(move_effects: list[dict]) -> str:
    """
    Join MoveEffect entries into a single EFFECT line.

    Rules:
    - Each entry with a damage_type renders as
      "{effect_value} {damage_type.upper()} DAMAGE".
    - Entries beyond MAX_EFFECT_ENTRIES are dropped, not overflowed onto
      the card — the physical layout was only verified up to 3 entries
      (see MVP_0.2_RENDERING.md's domain gap note).

    Examples:
        [{"damage_type": "physical", "effect_value": 6},
         {"damage_type": "fire", "effect_value": 2}]
        -> "6 PHYSICAL DAMAGE + 2 FIRE DAMAGE"
    """
    lines = [
        f"{entry['effect_value']} {entry['damage_type'].upper()} DAMAGE"
        for entry in move_effects[:MAX_EFFECT_ENTRIES]
        if entry.get("damage_type") is not None
    ]
    return " + ".join(lines)


def format_bonus_cards(cards_to_add: list[dict]) -> list[dict]:
    """
    Format each cards_to_add reference into a name/short-id pair for the
    BONUS CARDS list — rendered as the name in bold with its id in a
    smaller line beneath it, not on the same line.

    Entries beyond MAX_BONUS_CARDS are dropped, not overflowed onto the
    card — same reasoning as MAX_EFFECT_ENTRIES: .body-section has a
    fixed height (see move_card_style.html.jinja2) sized for at most 3
    bonus card entries, so every card has the same total height
    regardless of content instead of growing/shrinking per card.
    """
    return [
        {"name": card["name"].upper(), "short_id": f"ID{card['id'][:8]}"}
        for card in cards_to_add[:MAX_BONUS_CARDS]
    ]


def build_card_context(card_data: dict) -> dict:
    """
    Build the template context for a single MoveCard's serialized dict.

    Shared by render_move_card_html() (the standalone page) and
    rendering/gallery_renderer.py (many cards on one page) so both
    produce the exact same card fragment from the same input shape —
    see move_card_fragment.html.jinja2, which both templates include.
    """
    return {
        "labels": FIELD_LABELS,
        "accent_color": MOVE_TYPE_TO_COLOR_MAPPING[card_data["move_type"]],
        "name": card_data["name"].upper(),
        "category": card_data["category"].upper(),
        "move_type": card_data["move_type"].upper(),
        "mode": card_data["mode"].upper(),
        "image_uri": card_data.get("image_uri"),
        "resource": card_data["resource"].upper(),
        "resource_value": card_data["resource_value"],
        "move_range": card_data.get("move_range"),
        "range_value": card_data.get("range_value"),
        "effect_line": format_move_effects(card_data.get("move_effects", [])),
        "bonus_cards": format_bonus_cards(card_data.get("cards_to_add", [])),
        "description": card_data["description"],
        "card_id": card_data["id"],
    }


def render_move_card_html(card_data: dict) -> str:
    """
    Render a MoveCard's serialized dict into a static HTML page.

    card_data is the dict already produced by
    serialization.domain_to_json.card_to_json() (parsed back with
    json.loads), not a raw domain MoveCard.
    """
    template = environment.get_template("move_card.html.jinja2")
    return template.render(**build_card_context(card_data))


def render_move_card_html_with_edit(
        card_data: dict,
        edit_form_action: str,
        edit_form_fields: dict[str, str]) -> str:
    """
    Same as render_move_card_html(), but wraps the card with a small
    "Edit this classification" form beneath it, POSTing edit_form_fields
    (rendered as hidden inputs) to edit_form_action.

    Lets a consumer (ui/app.py) make a rendered card never a dead end —
    a reviewer can revisit the classification even after an
    auto-approved result, which otherwise has no correction path at all.
    Reuses move_card_fragment.html.jinja2/move_card_style.html.jinja2,
    the same shared partials move_card.html.jinja2 and the gallery
    already build on, rather than embedding a second full HTML document
    inside this one.
    """
    template = environment.get_template("move_card_with_edit.html.jinja2")
    return template.render(
        edit_form_action=edit_form_action,
        edit_form_fields=edit_form_fields,
        **build_card_context(card_data),
    )
