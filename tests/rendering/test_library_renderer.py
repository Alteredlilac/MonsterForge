"""
Tests for rendering/library_renderer.py.

Covers the aggregation logic specific to the cards library page (the
id/revision-count display, the classification tab's active-vs-original
distinction, and the history tab's per-event change highlighting) --
the card's own visual rendering is already covered by
test_move_card_renderer.py, same reasoning as test_gallery_renderer.py.
"""
import html

from monsterforge.rendering.library_renderer import render_library_html

MOVE_CARD = {
    "id": "124557a3-5384-44bb-a28a-5e1ca86dbcbb",
    "name": "Bite",
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
DEFAULT_RESULT = {
    "description": "A furious bite.", "move_type": "physical", "move_range": None,
    "confidence": 0.9, "rationale": "Clear.",
}


def make_event(event_type="llm_run", result=None, **overrides):
    defaults = dict(
        event_type=event_type,
        status="active",
        decision="auto_approved" if event_type == "llm_run" else "approved",
        actor_name="llm" if event_type == "llm_run" else "human_reviewer",
        actor_authority=0 if event_type == "llm_run" else 10,
        created_at="2026-09-05T18:00:00",
        is_active=False,
        result=result if result is not None else dict(DEFAULT_RESULT),
        prompt_name="classify_attack.jinja2" if event_type == "llm_run" else None,
        model_name="gemini-flash-lite-latest" if event_type == "llm_run" else None,
        rerun_note=None,
        assigned_llm_score=None,
        edit_note=None,
    )
    defaults.update(overrides)
    return defaults


def make_entry(events=None, **overrides):
    events = events if events is not None else [make_event(is_active=True)]
    defaults = dict(
        raw_field_id="deadbeef-0000-0000-0000-000000000000",
        case={"name": "Bite", "modifier": "+5", "attack_type": "melee", "attack_effect": "1d6+3"},
        context={"additional_description": None, "creature_description": None, "creature_subtype": None},
        raw_response=None,
        classification_result=events[-1]["result"],
        assigned_llm_score=None,
        edit_note=None,
        revision_count=len(events),
        events=events,
        move_card=MOVE_CARD,
    )
    defaults.update(overrides)
    return defaults


def test_render_library_html_shows_the_short_id_and_revision_count():
    page = render_library_html([make_entry()])
    assert "deadbeef" in page
    assert "1 revision" in page


def test_render_library_html_pluralizes_revision_count():
    events = [make_event(is_active=False), make_event(event_type="human_review", is_active=True)]
    page = render_library_html([make_entry(events=events)])
    assert "2 revisions" in page


def test_render_library_html_shows_the_active_classification_result():
    page = render_library_html([make_entry()])
    assert '"move_type": "physical"' in html.unescape(page)


def test_render_library_html_shows_human_review_fields_only_when_present():
    page = render_library_html([make_entry(assigned_llm_score=0.6, edit_note="Looks fine.")])
    assert '"assigned_llm_score": 0.6' in html.unescape(page)


def test_render_library_html_hides_human_review_block_when_absent():
    page = render_library_html([make_entry()])
    assert "assigned_llm_score" not in page


def test_render_library_html_highlights_a_field_a_correction_changed():
    llm_event = make_event(
        event_type="llm_run", is_active=False,
        result={"description": "A shock.", "move_type": "magical", "move_range": None,
                "confidence": 0.9, "rationale": "Elemental damage implies magic."},
    )
    review_event = make_event(
        event_type="human_review", is_active=True,
        result={"description": "A shock.", "move_type": "physical", "move_range": None,
                "confidence": 0.9, "rationale": "Elemental damage implies magic."},
    )
    page = html.unescape(render_library_html([make_entry(events=[llm_event, review_event])]))

    assert '<span class="history-changed">"physical"</span>' in page
    # The LLM_RUN is the first event, nothing to compare against yet,
    # so its own move_type is never flagged even though it later changes.
    assert '<span class="">"magical"</span>' in page


def test_render_library_html_does_not_highlight_an_unchanged_field():
    llm_event = make_event(is_active=False)
    review_event = make_event(event_type="human_review", is_active=True, result=dict(DEFAULT_RESULT))
    page = render_library_html([make_entry(events=[llm_event, review_event])])

    assert page.count('class="history-changed"') == 0
