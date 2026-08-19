"""
Tests for rendering/gallery_renderer.py.

Covers the aggregation logic specific to the gallery (skipping samples
with no move_card, one modal per remaining entry, embedding raw
input/classification/JSON for drill-down) — the card's own visual
rendering is already covered by test_move_card_renderer.py, since both
the gallery and the standalone page render through the same
move_card_fragment template and build_card_context().
"""
import json

from monsterforge.rendering.gallery_renderer import render_gallery_html


def make_sample(name="Bite", move_card_overrides=None, move_card=...):
    if move_card is ...:
        move_card = {
            "id": "124557a3-5384-44bb-a28a-5e1ca86dbcbb",
            "name": name,
            "description": "A furious bite.",
            "image_uri": None,
            "move_type": "physical",
            "category": "attack",
            "mode": "active",
            "effect": "damage",
            "move_effects": [{"damage_type": "physical", "effect_unit": None, "effect_value": 6}],
            "entity_effect": [],
            "cards_to_add": [],
            "cards_to_remove": [],
            "target": "single",
            "effect_radius": None,
            "move_range": None,
            "range_value": None,
            "resource": "stamina",
            "resource_value": 1,
            "duration": "instant",
            "duration_unit": None,
            "duration_value": None,
            "usage": "unlimited",
        }
        if move_card_overrides:
            move_card.update(move_card_overrides)

    return {
        "case": {"name": name, "modifier": "+5", "attack_type": "melee", "attack_effect": "1d6+3"},
        "context": {"additional_description": None, "creature_description": None, "creature_subtype": None},
        "raw_response": '{"description": "A furious bite.", "rationale": "Standard melee natural attack."}',
        "confidence": 0.9,
        "rationale": "Standard melee natural attack.",
        "move_card": move_card,
    }


def test_render_gallery_html_skips_entries_with_no_move_card():
    samples = [make_sample("Bite"), make_sample("Claw", move_card=None)]
    html = render_gallery_html(samples)
    assert "BITE" in html.upper()
    assert 'id="cardModal-2"' not in html


def test_render_gallery_html_produces_one_modal_per_entry():
    samples = [make_sample("Bite"), make_sample("Claw")]
    html = render_gallery_html(samples)
    assert html.count('class="modal fade"') == 2
    assert 'id="cardModal-1"' in html
    assert 'id="cardModal-2"' in html


def test_render_gallery_html_embeds_raw_input_and_classification_and_json():
    samples = [make_sample("Bite")]
    html = render_gallery_html(samples)
    assert "1d6+3" in html
    assert "Standard melee natural attack." in html
    assert json.dumps(samples[0]["move_card"], indent=2) in html


def test_render_gallery_html_mixes_accent_colors_for_different_move_types():
    samples = [
        make_sample("Bite", move_card_overrides={"move_type": "physical", "resource": "stamina"}),
        make_sample("Touch", move_card_overrides={"move_type": "magical", "resource": "mana"}),
    ]
    html = render_gallery_html(samples)
    assert "#c17f68" in html
    assert "#8f8fc2" in html


def test_render_gallery_html_with_no_valid_entries_renders_empty_gallery():
    html = render_gallery_html([make_sample("Bite", move_card=None)])
    assert "0 MoveCards" in html
