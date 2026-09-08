"""
FastAPI web app for MVP 1: the same conversion + human review flow MVP
0.5 built for the CLI (entrypoints/convert_attack_cli.py,
entrypoints/_review_input.py), exposed over HTTP instead of a terminal
prompt.

Correction has full parity with the CLI: free text for description and
the range's numeric value, constrained dropdowns for move_type and the
range's unit, assigned_llm_score/edit_note on every decision. Rerun
(reclassify, optionally with a note and/or a different prompt template)
is also supported, mirroring entrypoints/_review_input.py's CLI rerun
as one HTTP round trip instead of a loop inside the same process.

No server-side session state, matching MVP 0.5's own statelessness:
raw_attack and the original classification travel from GET/POST
/convert to POST /review as hidden form fields, not stored anywhere
between requests.

Model-availability handling (ensure_model_available()/
call_llm_with_model_fallback() in entrypoints/_llm_model_selection.py)
is deliberately NOT reused here — it's interactive, built around
input() to ask a human which model to use, which has no meaning inside
an HTTP request/response cycle. A ModelUnavailableError here is caught
and reported as a plain error response instead.
"""
import dataclasses
import json
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from monsterforge.config import validation_settings
from monsterforge.db.enums import EventType
from monsterforge.db.pipeline import ClassificationEvent, RawField
from monsterforge.db.seed import seed_reference_data
from monsterforge.db.session import create_all_tables, get_session
from monsterforge.ui.dependencies import get_db_session
from monsterforge.ui.jinja_templating import templates
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import UnknownAttackRange
from monsterforge.pipeline.attack_repository import activate_classification_event, record_human_review, record_llm_run
from monsterforge.pipeline.attack_repository_queries import (
    InconsistentActiveClassificationError,
    find_existing_card,
    list_saved_cards,
    resolve_effective_name,
)
from monsterforge.pipeline.reference_lookups import get_human_actor, get_llm_actor
from monsterforge.llm.client import get_llm_client
from monsterforge.llm.clients.gemini import ModelUnavailableError
from monsterforge.llm.semantic_classification.attacks import (
    ATTACK_PROMPT_TEMPLATE,
    ATTACK_PROMPT_TEMPLATE_OPTIONS,
    AttackSemanticResult,
    SemanticContextInput,
    classify_attack,
)
from monsterforge.rendering.library_renderer import render_library_html
from monsterforge.structured_data.dnd.v3x.enums import MoveType
from monsterforge.ui.context import parse_positive_range, semantic_context_from_form
from monsterforge.ui.hidden_fields import semantic_result_from_json
from monsterforge.ui.responses import message_page, render_card, review_form_context, serve_cached_card
from monsterforge.ui.routes.convert import router as convert_router
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import HumanReview

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create the database tables and seed reference rows once, at
    startup — this project has no migration tool, so table creation
    must be triggered explicitly rather than happening on import (see
    db/session.py::create_all_tables())."""
    create_all_tables()
    session = get_session()
    try:
        seed_reference_data(session)
    finally:
        session.close()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(convert_router)


# =====================
# ROUTES
# =====================
FAVICON_PATH = Path(__file__).resolve().parents[1] / "docs" / "images" / "Web" / "favicon.png"


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> FileResponse:
    return FileResponse(FAVICON_PATH)


@app.get("/library/cards", response_class=HTMLResponse)
def cards_library(q: str = "", session: Session = Depends(get_db_session)) -> HTMLResponse:
    """Read-only browsing of every card currently saved in the database,
    optionally filtered by `q` against the attack's name or id — see
    pipeline.attack_repository_queries.list_saved_cards() and
    rendering.library_renderer.render_library_html(). Deliberately
    separate from the public, curated gallery (rendering/gallery_renderer.py),
    which reads from a fixed JSON dataset, not the live database."""
    query = q.strip()
    entries = list_saved_cards(session, query=query or None)
    return HTMLResponse(render_library_html(entries, query=query))


@app.get("/library/cards/{raw_field_id}", response_class=HTMLResponse)
def view_saved_card(raw_field_id: str, session: Session = Depends(get_db_session)) -> HTMLResponse:
    """Reopen an already-saved card for printing or further review,
    found by raw_field_id (e.g. a link from the cards library) rather
    than through a fresh fingerprint hit. Delegates to
    serve_cached_card() for the actual rendering — the same page
    /convert's own cache-hit path already builds, with Print and "Edit
    this classification" (-> /review/edit) both already on it."""
    raw_field = session.get(RawField, raw_field_id)
    if raw_field is None or raw_field.current_classification_event_id is None:
        return message_page("No saved card found for that id.", status_code=404)

    active_event = session.get(ClassificationEvent, raw_field.current_classification_event_id)
    if active_event.decision == ValidationStatus.REJECTED:
        return message_page("This attack was previously rejected — no card to show.", status_code=422)

    try:
        _structured_data, card = find_existing_card(session, active_event)
    except InconsistentActiveClassificationError as exc:
        return message_page(f"Could not load the saved card: {exc}", status_code=500)

    # NOTE:
    # template_name isn't a column on a HUMAN_REVIEW row (see
    # db/pipeline.py) -- walk back to the LLM_RUN it references for the
    # prompt actually used, same pattern already used by
    # list_saved_cards()/list_classification_events() for confidence/
    # rationale. Always by id (referenced_event_id, a real FK), never
    # by name -- a name like "Bite" can have homonyms across raw_fields.
    origin_event = active_event
    if active_event.event_type == EventType.HUMAN_REVIEW and active_event.referenced_event_id:
        origin_event = session.get(ClassificationEvent, active_event.referenced_event_id)
    template_name = origin_event.prompt_name or ATTACK_PROMPT_TEMPLATE

    # Not stored anywhere on raw_field -- it's the saved card's own
    # column (promoted from its content, see db/cards.py).
    image_uri = card.image_uri or ""

    return serve_cached_card(session, raw_field, active_event, template_name, image_uri)


@app.get("/library/events/{classification_event_id}/review", response_class=HTMLResponse)
def reopen_event_for_review(
        request: Request, classification_event_id: str,
        session: Session = Depends(get_db_session)) -> HTMLResponse:
    """Reopen any past classification_events row for a fresh review
    decision, not just the raw_field's currently active one — approving
    or correcting it here makes it the new active result. Works
    uniformly whether or not this event ever had a card built for it (a
    superseded, never-decided LLM_RUN never does) since it reopens the
    review form directly, the same way /review/edit already does,
    rather than a rendered card. Not linked to at all from
    library.html.jinja2 for a REJECTED event, whose own result is an
    empty dict — nothing to review; rejected here too, directly, in
    case this URL is reached some other way."""
    event = session.get(ClassificationEvent, classification_event_id)
    if event is None:
        return message_page("No such classification event.", status_code=404)
    if event.decision == ValidationStatus.REJECTED:
        return message_page("This event was rejected — nothing to review.", status_code=422)

    raw_field = session.get(RawField, event.raw_field_id)
    # resolve_effective_name(), not raw_field.data["name"] -- the name
    # in effect as of THIS specific event may already reflect an
    # earlier correction (MVP 2.19), which the original, immutable
    # submission on raw_field never carries.
    raw_attack = RawAttack(
        name=resolve_effective_name(session, raw_field, event.id), modifier=raw_field.data["modifier"],
        attack_type=raw_field.data["attack_type"], attack_effect=raw_field.data["attack_effect"],
    )
    semantic_context = semantic_context_from_form(
        raw_field.data.get("additional_description") or "",
        raw_field.data.get("creature_description") or "",
        raw_field.data.get("creature_subtype") or "",
    )
    semantic_result = semantic_result_from_json(json.dumps(event.result))

    # Same by-id walk-back as view_saved_card() above, for the same reason.
    origin_event = event
    if event.event_type == EventType.HUMAN_REVIEW and event.referenced_event_id:
        origin_event = session.get(ClassificationEvent, event.referenced_event_id)
    template_name = origin_event.prompt_name or ATTACK_PROMPT_TEMPLATE

    try:
        _structured_data, card = find_existing_card(session, event)
        image_uri = card.image_uri or ""
    except InconsistentActiveClassificationError:
        # NOTE:
        # Unlike view_saved_card()'s lookup on the raw_field's ACTIVE
        # event (where a missing card is a real data-integrity anomaly),
        # a missing card here is normal, not an anomaly: a superseded
        # LLM_RUN that a rerun overtook before ever being decided, or a
        # rejected review, never had one built in the first place.
        image_uri = ""

    return templates.TemplateResponse(
        request, "review_form.html.jinja2",
        review_form_context(
            raw_attack, semantic_context, semantic_result, template_name, image_uri,
            raw_field_id=raw_field.id, classification_event_id=event.id,
        ),
    )


@app.post("/review/edit", response_class=HTMLResponse)
def edit_review(
        request: Request,
        raw_attack_name: str = Form(""),
        raw_attack_modifier: str = Form(""),
        raw_attack_attack_type: str = Form(""),
        raw_attack_attack_effect: str = Form(""),
        additional_description: str = Form(""),
        creature_description: str = Form(""),
        creature_subtype: str = Form(""),
        image_uri: str = Form(""),
        raw_field_id: str = Form(...),
        classification_event_id: str = Form(...),
        semantic_result_json: str = Form(...),
        template_name: str = Form(...),
        ) -> HTMLResponse:
    """
    Reopens the review form for an already-produced card — reachable
    from the "Edit this classification" button render_move_card_html_
    with_edit() adds to every rendered card, not just ones that already
    went through review. No LLM call here: the classification is the
    one already carried in semantic_result_json, not reclassified.
    """
    raw_attack = RawAttack(
        name=raw_attack_name,
        modifier=raw_attack_modifier,
        attack_type=raw_attack_attack_type,
        attack_effect=raw_attack_attack_effect,
    )
    semantic_context = semantic_context_from_form(additional_description, creature_description, creature_subtype)
    semantic_result = semantic_result_from_json(semantic_result_json)

    return templates.TemplateResponse(
        request, "review_form.html.jinja2",
        review_form_context(
            raw_attack, semantic_context, semantic_result, template_name, image_uri,
            raw_field_id=raw_field_id, classification_event_id=classification_event_id,
        ),
    )


def _parse_assigned_llm_score(raw_value: str) -> float | None:
    return float(raw_value) if raw_value.strip() else None


@app.post("/review", response_class=HTMLResponse)
def review(
        request: Request,
        # NOTE:
        # These four carry the original raw attack through the hidden
        # form fields, unchanged since /convert. They default to "" (not
        # required) rather than Form(...): FastAPI treats an empty
        # string on a required Form field as if it weren't sent at all,
        # which turned a legitimately blank modifier into a hard 422
        # ("Field required") instead of the empty value it actually is.
        raw_attack_name: str = Form(""),
        raw_attack_modifier: str = Form(""),
        raw_attack_attack_type: str = Form(""),
        raw_attack_attack_effect: str = Form(""),
        additional_description: str = Form(""),
        creature_description: str = Form(""),
        creature_subtype: str = Form(""),
        image_uri: str = Form(""),
        raw_field_id: str = Form(...),
        classification_event_id: str = Form(...),
        template_name: str = Form(...),
        semantic_result_json: str = Form(...),
        decision: str = Form(...),
        name: str = Form(""),
        description: str = Form(""),
        move_type: str = Form(""),
        range_value: str = Form(""),
        range_unit: str = Form(""),
        corrected_image_uri: str = Form(""),
        assigned_llm_score: str = Form(""),
        edit_note: str = Form(""),
        rerun_note: str = Form(""),
        rerun_template_name: str = Form(""),
        session: Session = Depends(get_db_session),
        ) -> HTMLResponse:
    raw_attack = RawAttack(
        name=raw_attack_name,
        modifier=raw_attack_modifier,
        attack_type=raw_attack_attack_type,
        attack_effect=raw_attack_attack_effect,
    )
    semantic_context = semantic_context_from_form(additional_description, creature_description, creature_subtype)
    original_result = semantic_result_from_json(semantic_result_json)
    raw_field = session.get(RawField, raw_field_id)
    referenced_event = session.get(ClassificationEvent, classification_event_id)

    if decision == "reject":
        review_event = record_human_review(
            session, raw_field=raw_field, referenced_event=referenced_event,
            review=HumanReview(status=ValidationStatus.REJECTED, result=None,
                                assigned_llm_score=_parse_assigned_llm_score(assigned_llm_score),
                                edit_note=edit_note or None),
            actor=get_human_actor(session),
        )
        # NOTE:
        # Only activates when rejecting the raw_field's currently active
        # event (or its very first decision, current_classification_event_id
        # still None) -- rejecting an old, already-superseded event reopened
        # via /library/events/{id}/review (MVP 2.18) must not un-activate a
        # genuinely good current result. The rejection is still recorded in
        # the history either way, via record_human_review() above.
        if raw_field.current_classification_event_id not in (None, referenced_event.id):
            return message_page(
                "This old attempt was marked as rejected. The currently active result was not affected."
            )
        activate_classification_event(session, raw_field=raw_field, event=review_event)
        return message_page("No card produced: the classification was rejected.")

    if decision == "rerun":
        # NOTE:
        # Mirrors _review_input.py's CLI rerun, but as one HTTP round
        # trip instead of a loop inside the same process: a fresh
        # classify_attack() call, an optional note appended to
        # additional_description, and optionally a different template.
        # On any failure, re-shows review_form.html.jinja2 with the
        # ORIGINAL (pre-rerun) classification untouched plus an error
        # banner — same principle as the UnknownAttackRange bounce-back
        # below: a failed action here must not discard the reviewer's
        # already-reviewed state. No fingerprint check on this branch —
        # rerun is a deliberate manual retry, always a new attempt, never
        # deduplicated against the cache (see compute_fingerprint()).
        if rerun_template_name not in {option.path for option in ATTACK_PROMPT_TEMPLATE_OPTIONS}:
            return templates.TemplateResponse(
                request, "review_form.html.jinja2",
                review_form_context(
                    raw_attack, semantic_context, original_result, template_name, image_uri,
                    raw_field_id=raw_field_id, classification_event_id=classification_event_id,
                    error_message=f"Unknown prompt template: {rerun_template_name!r}.",
                ),
            )

        rerun_context = semantic_context
        if rerun_note.strip():
            combined_description = (
                f"{semantic_context.additional_description}\n{rerun_note}"
                if semantic_context.additional_description else rerun_note
            )
            rerun_context = dataclasses.replace(semantic_context, additional_description=combined_description)

        try:
            new_result = classify_attack(
                raw_attack=raw_attack,
                additional_description=rerun_context.additional_description,
                creature_description=rerun_context.creature_description,
                creature_subtype=rerun_context.creature_subtype,
                template_name=rerun_template_name,
            )
        except ModelUnavailableError as exc:
            error_message = f"The configured LLM model is unavailable: {exc}"
        except Exception as exc:
            error_message = f"Rerun failed: {exc}"
        else:
            new_event = record_llm_run(
                session, raw_field=raw_field, semantic_result=new_result, actor=get_llm_actor(session),
                prompt_name=rerun_template_name, model_name=get_llm_client().model_name,
                confidence_threshold=validation_settings.CONFIDENCE_THRESHOLD,
                decision=None, rerun_note=rerun_note or None,
            )
            return templates.TemplateResponse(
                request, "review_form.html.jinja2",
                review_form_context(
                    raw_attack, rerun_context, new_result, rerun_template_name, image_uri,
                    raw_field_id=raw_field_id, classification_event_id=new_event.id,
                ),
            )

        return templates.TemplateResponse(
            request, "review_form.html.jinja2",
            review_form_context(
                raw_attack, semantic_context, original_result, template_name, image_uri,
                raw_field_id=raw_field_id, classification_event_id=classification_event_id,
                error_message=error_message,
            ),
        )

    if decision == "correct":
        if not name.strip():
            return message_page("Name cannot be blank.", status_code=422)

        raw_attack = dataclasses.replace(raw_attack, name=name)

        try:
            corrected_range = parse_positive_range(range_value, range_unit)
        except ValueError as exc:
            return message_page(f"Invalid range value: {exc}", status_code=422)

        final_result = dataclasses.replace(
            original_result,
            description=description,
            move_type=MoveType(move_type),
            move_range=corrected_range,
        )
        review_status = ValidationStatus.CORRECTED
        # NOTE:
        # A changed image is a visual correction, not a classification
        # decision -- only the "correct" branch reads corrected_image_uri;
        # every other decision keeps the original image_uri untouched.
        final_image_uri = corrected_image_uri
        # Recorded unconditionally on every correction, same as
        # description/move_type/move_range above, even if the reviewer
        # left the name unchanged -- MVP 2.19, see HumanReview.corrected_name.
        final_corrected_name = name
    else:
        final_result = original_result
        review_status = ValidationStatus.APPROVED
        final_image_uri = image_uri
        final_corrected_name = None

    review_event = record_human_review(
        session, raw_field=raw_field, referenced_event=referenced_event,
        review=HumanReview(status=review_status, result=final_result,
                            assigned_llm_score=_parse_assigned_llm_score(assigned_llm_score),
                            edit_note=edit_note or None, corrected_name=final_corrected_name),
        actor=get_human_actor(session),
    )

    try:
        return render_card(
            session, raw_field, review_event, raw_attack, final_result, semantic_context,
            template_name, final_image_uri,
        )
    except UnknownAttackRange as exc:
        return templates.TemplateResponse(
            request, "review_form.html.jinja2",
            review_form_context(
                raw_attack, semantic_context, final_result, template_name, final_image_uri,
                raw_field_id=raw_field_id, classification_event_id=classification_event_id,
                error_message=f"Could not build the card: {exc} Provide a range below and try again.",
            ),
        )
