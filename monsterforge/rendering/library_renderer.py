"""
Renders a browsable page of every card currently saved in the database,
one entry per raw_field (see pipeline.attack_repository.list_saved_cards()).

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


def _format_move_range(move_range: dict | None) -> str:
    if not move_range:
        return "—"
    return f"{move_range['effect_range']} {move_range['range_unit_system']}"


def _build_history_entry(event: dict, previous_result: dict | None) -> dict:
    """
    Format one pipeline.attack_repository.list_classification_events()
    summary for display: a one-line header (type/decision/actor/when),
    the three fields a human correction can actually change
    (description/move_type/move_range) each flagged as changed when it
    differs from `previous_result` (the chronologically preceding
    event's own result — None for the very first event, so nothing is
    flagged there), and a JSON block of the remaining, type-specific
    fields: an LLM_RUN's prompt_name/model_name/rerun_note/confidence/
    rationale, or a HUMAN_REVIEW/MANUAL_CORRECTION's
    assigned_llm_score/edit_note.
    """
    result = event["result"] or {}
    has_previous = previous_result is not None
    baseline = previous_result or {}

    def _changed(key: str) -> bool:
        return has_previous and result.get(key) != baseline.get(key)

    if event["event_type"] == "llm_run":
        extra = {
            "prompt_name": event["prompt_name"], "model_name": event["model_name"],
            "rerun_note": event["rerun_note"], "confidence": result.get("confidence"),
            "rationale": result.get("rationale"),
        }
    else:
        extra = {"assigned_llm_score": event["assigned_llm_score"], "edit_note": event["edit_note"]}

    return {
        "event_type": event["event_type"],
        "decision": event["decision"] or "pending",
        "actor_name": event["actor_name"],
        "created_at": event["created_at"],
        "is_active": event["is_active"],
        "description": result.get("description"),
        "description_changed": _changed("description"),
        "move_type": result.get("move_type"),
        "move_type_changed": _changed("move_type"),
        "move_range": _format_move_range(result.get("move_range")),
        "move_range_changed": _changed("move_range"),
        "extra_json": json.dumps(extra, indent=2),
    }


def _build_history(events: list[dict]) -> list[dict]:
    """Build display entries for every classification event, oldest
    first, each compared against the one immediately before it (None
    for the first, so nothing is flagged as changed there)."""
    history = []
    previous_result = None
    for event in events:
        history.append(_build_history_entry(event, previous_result))
        previous_result = event["result"] or {}
    return history


def _build_library_entry(index: int, entry: dict) -> dict:
    move_card = entry["move_card"]
    card_html = _fragment_template.render(**build_card_context(move_card))
    classification_result = entry["classification_result"] or {}
    classification_values = {
        key: classification_result.get(key) for key in ("description", "move_type", "move_range")
    }
    classification_confidence = {
        key: classification_result.get(key) for key in ("confidence", "rationale")
    }
    human_review = None
    if entry["assigned_llm_score"] is not None or entry["edit_note"]:
        human_review = {"assigned_llm_score": entry["assigned_llm_score"], "edit_note": entry["edit_note"]}

    return {
        "index": index,
        "raw_field_id": entry["raw_field_id"],
        "short_id": entry["raw_field_id"][:8],
        "revision_count": entry["revision_count"],
        "name": move_card["name"],
        "move_type": move_card["move_type"],
        "category": move_card["category"],
        "card_html": card_html,
        "raw_input_json": json.dumps(entry["case"], indent=2),
        "context_json": json.dumps(entry["context"], indent=2),
        "classification_values_json": json.dumps(classification_values, indent=2),
        "classification_confidence_json": json.dumps(classification_confidence, indent=2),
        "human_review_json": json.dumps(human_review, indent=2) if human_review is not None else None,
        "move_card_json": json.dumps(move_card, indent=2),
        "history": _build_history(entry["events"]),
    }


def render_library_html(entries: list[dict], query: str = "") -> str:
    """
    Render the cards-library page from pipeline.attack_repository.list_saved_cards()'s output.

    Each entry is expected to have the shape that function builds:
    {"raw_field_id", "case", "context", "classification_result",
    "assigned_llm_score", "edit_note", "revision_count", "events",
    "move_card"}.

    query is redisplayed in the search box and drives a "no results"
    message distinct from "nothing saved at all" when entries is empty
    because of a filter rather than an actually-empty library.
    """
    template = environment.get_template("library.html.jinja2")
    built_entries = [_build_library_entry(index, entry) for index, entry in enumerate(entries, start=1)]
    return template.render(entries=built_entries, query=query)
