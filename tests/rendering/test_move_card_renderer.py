"""
Tests for rendering/move_card_renderer.py.

Covers:
- format_move_effects()/format_bonus_cards() as pure helper functions
  (branching/limit logic worth testing directly, not just through the
  full rendered HTML)
- render_move_card_html() over the binary branches observed in the
  reference mockups: move_range present/absent x cards_to_add
  present/absent, image_uri present/absent, move_type physical/magical
  (accent color)

card_data is built the same way a real caller builds it: a MoveCard ->
card_to_json() -> json.loads(), not a hand-written dict — this exercises
the actual serialization/rendering boundary, not an assumed shape.
"""
import json

from monsterforge.domain.moves import MoveCard, MoveEffect
from monsterforge.domain.enums import (
    MoveType, MoveCategory, MoveMode, EffectType, DamageType, Target,
    MoveRange, Resource, Duration, Usage,
)
from monsterforge.serialization.domain_to_json import card_to_json
from monsterforge.rendering.move_card_renderer import (
    render_move_card_html, render_move_card_html_with_edit, format_move_effects, format_bonus_cards,
)
from monsterforge.rendering.labels import MOVE_TYPE_TO_COLOR_MAPPING


def make_move_card(**overrides):
    defaults = dict(
        name="Bite",
        description="A furious bite.",
        move_type=MoveType.PHYSICAL,
        category=MoveCategory.ATTACK,
        mode=MoveMode.ACTIVE,
        effect=EffectType.DAMAGE,
        move_effects=[MoveEffect(damage_type=DamageType.PHYSICAL, effect_value=6)],
        target=Target.SINGLE,
        resource=Resource.STAMINA,
        duration=Duration.INSTANT,
        usage=Usage.UNLIMITED,
    )
    defaults.update(overrides)
    return MoveCard(**defaults)


def make_card_data(**overrides):
    """Build the exact dict render_move_card_html() consumes in real use."""
    return json.loads(card_to_json(make_move_card(**overrides)))


# =====================
# format_move_effects
# =====================
def test_format_move_effects_joins_multiple_entries_with_plus():
    effects = [
        {"damage_type": "physical", "effect_value": 6},
        {"damage_type": "fire", "effect_value": 2},
    ]
    assert format_move_effects(effects) == "6 PHYSICAL DAMAGE + 2 FIRE DAMAGE"


def test_format_move_effects_caps_at_three_entries():
    """The card layout was only verified up to 3 move_effects entries
    (see MVP_0.2_RENDERING.md's domain gap note) — a 4th is dropped, not
    overflowed onto the card."""
    effects = [
        {"damage_type": "physical", "effect_value": 1},
        {"damage_type": "fire", "effect_value": 2},
        {"damage_type": "cold", "effect_value": 3},
        {"damage_type": "acid", "effect_value": 4},
    ]
    result = format_move_effects(effects)
    assert result == "1 PHYSICAL DAMAGE + 2 FIRE DAMAGE + 3 COLD DAMAGE"
    assert "ACID" not in result


def test_format_move_effects_skips_entries_without_damage_type():
    effects = [{"damage_type": None, "effect_value": 5}]
    assert format_move_effects(effects) == ""


# =====================
# format_bonus_cards
# =====================
def test_format_bonus_cards_uses_uppercase_name_and_short_id():
    cards = [{"name": "Trip", "id": "def8aedc-4d1d-4f65-97bc-4c7efabaaf2d"}]
    result = format_bonus_cards(cards)
    assert result == [{"name": "TRIP", "short_id": "IDdef8aedc"}]


def test_format_bonus_cards_caps_at_three_entries():
    """.body-section has a fixed height sized for at most 3 bonus card
    entries (see move_card_style.html.jinja2) — a 4th is dropped, not
    overflowed onto the card."""
    cards = [
        {"name": "Trip", "id": "aaaaaaaa-0000-0000-0000-000000000000"},
        {"name": "Confusion", "id": "bbbbbbbb-0000-0000-0000-000000000000"},
        {"name": "Daze", "id": "cccccccc-0000-0000-0000-000000000000"},
        {"name": "Push", "id": "dddddddd-0000-0000-0000-000000000000"},
    ]
    result = format_bonus_cards(cards)
    assert len(result) == 3
    assert "PUSH" not in [entry["name"] for entry in result]


# =====================
# render_move_card_html — binary branches
# =====================
def test_range_box_appears_when_move_range_is_set():
    data = make_card_data(move_range=MoveRange.RANGED, range_value=30)
    html = render_move_card_html(data)
    assert 'class="range-box"' in html
    assert ">30<" in html


def test_range_box_absent_when_move_range_is_none():
    data = make_card_data()
    html = render_move_card_html(data)
    assert 'class="range-box"' not in html


def test_bonus_cards_column_appears_when_cards_to_add_is_present():
    trip = make_move_card(name="Trip")
    data = make_card_data(cards_to_add=[trip])
    html = render_move_card_html(data)
    assert 'class="bonus-col"' in html
    assert "TRIP" in html


def test_bonus_cards_column_absent_when_cards_to_add_is_empty():
    data = make_card_data()
    html = render_move_card_html(data)
    assert 'class="bonus-col"' not in html


def test_image_label_absent_when_image_uri_is_set():
    data = make_card_data(image_uri="https://example.com/bite.png")
    html = render_move_card_html(data)
    assert 'class="image-label"' not in html
    assert "https://example.com/bite.png" in html


def test_image_label_present_when_image_uri_is_none():
    data = make_card_data()
    html = render_move_card_html(data)
    assert 'class="image-label"' in html


def test_accent_color_is_purple_for_magical_move_type():
    data = make_card_data(move_type=MoveType.MAGICAL, resource=Resource.MANA)
    html = render_move_card_html(data)
    assert MOVE_TYPE_TO_COLOR_MAPPING[MoveType.MAGICAL] in html


def test_accent_color_is_salmon_for_physical_move_type():
    data = make_card_data()
    html = render_move_card_html(data)
    assert MOVE_TYPE_TO_COLOR_MAPPING[MoveType.PHYSICAL] in html


# =====================
# WITH EDIT FORM
# =====================
def test_with_edit_includes_the_edit_form_fields_as_hidden_inputs():
    data = make_card_data()
    html = render_move_card_html_with_edit(data, "/review/edit", {"raw_attack_name": "Bite"})

    assert 'action="/review/edit"' in html
    assert '<input type="hidden" name="raw_attack_name" value="Bite">' in html


def test_with_edit_escapes_special_characters_in_field_values():
    """A hidden field value with an embedded double quote must not
    break out of the HTML attribute it's rendered inside — this broke
    once for a JSON-serialized field before the value was explicitly
    escaped in the template."""
    data = make_card_data()
    html = render_move_card_html_with_edit(data, "/review/edit", {"semantic_result_json": '{"a": "b"}'})

    assert '{"a": "b"}' not in html
    assert "&#34;a&#34;" in html


def test_with_edit_includes_print_specific_rules():
    data = make_card_data()
    html = render_move_card_html_with_edit(data, "/review/edit", {})

    assert "@page" in html
    assert "@media print" in html
    assert "display: none" in html  # hides the on-screen controls when printing
