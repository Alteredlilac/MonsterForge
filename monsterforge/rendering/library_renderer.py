"""
Renders a browsable page of every card currently saved in the database,
one entry per raw_field (see pipeline.attack_repository_queries.list_saved_cards()).

Deliberately separate from rendering/gallery_renderer.py, which renders
a curated dataset of real API runs for the public, portfolio-facing
gallery — the two consume different data sources (this module reads
the live database, that one a fixed JSON dataset) for different
audiences, and are kept independent so neither has to change when the
other does: this module never imports from gallery_renderer.py, and
gallery.html.jinja2 is never touched by anything here.

Each card fragment is rendered once, in Python, via the same
move_card_fragment template and build_card_context() used by
render_move_card_html()/gallery_renderer.py — see that module's own
docstring for why the fragment is built in Python rather than a nested
Jinja2 include.
"""
import json

from monsterforge.rendering.move_card_renderer import build_card_context, environment

_fragment_template = environment.get_template("move_card_fragment.html.jinja2")


def _format_move_range(move_range: dict | None) -> str | None:
    """None (rendered as JSON's own `null`, not a quoted placeholder
    string) for a melee attack with no range at all."""
    if not move_range:
        return None
    return f"{move_range['effect_range']} {move_range['range_unit_system']}"


def _build_history_entry(event: dict, previous_event: dict | None) -> dict:
    """
    Format one pipeline.attack_repository_queries.list_classification_events()
    summary for display: a header (type/decision/actor+authority/when)
    plus every field of that event in one JSON-look block — the four
    fields a human correction can actually change (name/description/
    move_type/move_range) each flagged as changed when they differ from
    `previous_event` (the chronologically preceding event — None for
    the very first event, so nothing is flagged there), then
    the remaining, type-specific fields: an LLM_RUN's prompt_name/
    model_name/rerun_note/confidence/rationale, or a HUMAN_REVIEW/
    MANUAL_CORRECTION's assigned_llm_score/edit_note. One block, not
    two — a single event's own detail split across two separately
    bordered boxes read as unrelated at a glance.

    name is compared via effective_name (see list_classification_events()),
    not result -- unlike description/move_type/move_range, corrected_name
    is only ever set on the specific event that changed it, so
    effective_name is what actually carries the current value forward.
    """
    result = event["result"] or {}
    has_previous = previous_event is not None
    baseline = (previous_event or {}).get("result") or {}
    previous_name = (previous_event or {}).get("effective_name")

    def _field(key: str, display_value, changed: bool = False) -> dict:
        return {"key": key, "value_json": json.dumps(display_value), "changed": changed}

    fields = [
        _field("name", event["effective_name"],
               has_previous and event["effective_name"] != previous_name),
        _field("description", result.get("description"),
               has_previous and result.get("description") != baseline.get("description")),
        _field("move_type", result.get("move_type"),
               has_previous and result.get("move_type") != baseline.get("move_type")),
        _field("move_range", _format_move_range(result.get("move_range")),
               has_previous and result.get("move_range") != baseline.get("move_range")),
    ]
    if event["event_type"] == "llm_run":
        fields += [
            _field("prompt_name", event["prompt_name"]),
            _field("model_name", event["model_name"]),
            _field("rerun_note", event["rerun_note"]),
            _field("confidence", result.get("confidence")),
            _field("rationale", result.get("rationale")),
        ]
    else:
        fields += [
            _field("assigned_llm_score", event["assigned_llm_score"]),
            _field("edit_note", event["edit_note"]),
        ]

    return {
        "id": event["id"],
        "event_type": event["event_type"],
        "decision": event["decision"] or "pending",
        "actor_name": event["actor_name"],
        "actor_authority": event["actor_authority"],
        "created_at": event["created_at"],
        "is_active": event["is_active"],
        "fields": fields,
    }


def _build_history(events: list[dict]) -> list[dict]:
    """Build display entries for every classification event, oldest
    first, each compared against the one immediately before it (None
    for the first, so nothing is flagged as changed there)."""
    history = []
    previous_event = None
    for event in events:
        history.append(_build_history_entry(event, previous_event))
        previous_event = event
    return history


def _build_library_entry(index: int, entry: dict) -> dict:
    """
    Build one modal's worth of display data from list_saved_cards()'s
    entry shape.

    has_card is False for a raw_field whose active event is REJECTED
    (see list_saved_cards()) — there is no card, and no classification
    to show: the Classification/JSON/Card tabs are omitted entirely by
    library.html.jinja2 in that case, leaving only Raw Input and
    History (always meaningful, rejection included). name falls back to
    entry["name"] (raw_fields.data["name"], promoted by
    list_saved_cards()) instead of a card's own name, since there's no
    card to read it from.
    """
    move_card = entry["move_card"]
    has_card = move_card is not None

    card_html = None
    classification_values_json = None
    classification_confidence_json = None
    human_review_json = None
    move_card_json = None
    if has_card:
        card_html = _fragment_template.render(**build_card_context(move_card))
        classification_result = entry["classification_result"] or {}
        classification_values = {
            key: classification_result.get(key) for key in ("description", "move_type", "move_range")
        }
        classification_confidence = {
            key: classification_result.get(key) for key in ("confidence", "rationale")
        }
        classification_values_json = json.dumps(classification_values, indent=2)
        classification_confidence_json = json.dumps(classification_confidence, indent=2)
        if entry["assigned_llm_score"] is not None or entry["edit_note"]:
            human_review = {"assigned_llm_score": entry["assigned_llm_score"], "edit_note": entry["edit_note"]}
            human_review_json = json.dumps(human_review, indent=2)
        move_card_json = json.dumps(move_card, indent=2)

    return {
        "index": index,
        "raw_field_id": entry["raw_field_id"],
        "short_id": entry["raw_field_id"][:8],
        "revision_count": entry["revision_count"],
        "has_card": has_card,
        "name": move_card["name"] if has_card else entry["name"],
        "move_type": move_card["move_type"] if has_card else None,
        "category": move_card["category"] if has_card else None,
        "card_html": card_html,
        "raw_input_json": json.dumps(entry["case"], indent=2),
        "context_json": json.dumps(entry["context"], indent=2),
        "classification_values_json": classification_values_json,
        "classification_confidence_json": classification_confidence_json,
        "human_review_json": human_review_json,
        "move_card_json": move_card_json,
        "history": _build_history(entry["events"]),
    }


def render_library_html(entries: list[dict], query: str = "") -> str:
    """
    Render the cards-library page from pipeline.attack_repository_queries.list_saved_cards()'s output.

    Each entry is expected to have the shape that function builds:
    {"raw_field_id", "name", "case", "context", "classification_result",
    "assigned_llm_score", "edit_note", "revision_count", "events",
    "move_card"} — "move_card"/"classification_result" are None for a
    raw_field whose active event is REJECTED, in which case "name" (not
    a card's own name) is what gets displayed, see _build_library_entry().

    query is redisplayed in the search box and drives a "no results"
    message distinct from "nothing saved at all" when entries is empty
    because of a filter rather than an actually-empty library.
    """
    template = environment.get_template("library.html.jinja2")
    built_entries = [_build_library_entry(index, entry) for index, entry in enumerate(entries, start=1)]
    return template.render(entries=built_entries, query=query)
