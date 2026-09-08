"""
POST /review and POST /review/edit -- the four review decisions
(approve/correct/reject/rerun) and reopening an already-produced card's
review form without reclassifying.

Rerun mirrors entrypoints/_review_input.py's CLI rerun as one HTTP
round trip instead of a loop inside the same process: a fresh
classify_attack() call, an optional note appended to
additional_description, and optionally a different template.
"""
import dataclasses

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from monsterforge.config import validation_settings
from monsterforge.db.pipeline import ClassificationEvent, RawField
from monsterforge.db.session import get_db_session
from monsterforge.llm.client import get_llm_client
from monsterforge.llm.clients.gemini import ModelUnavailableError
from monsterforge.llm.semantic_classification.attacks import ATTACK_PROMPT_TEMPLATE_OPTIONS, classify_attack
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import UnknownAttackRange
from monsterforge.pipeline.attack_repository import activate_classification_event, record_human_review, record_llm_run
from monsterforge.pipeline.reference_lookups import get_human_actor, get_llm_actor
from monsterforge.structured_data.dnd.v3x.enums import MoveType
from monsterforge.ui.context import parse_positive_range, semantic_context_from_form
from monsterforge.ui.hidden_fields import semantic_result_from_json
from monsterforge.ui.jinja_templating import templates
from monsterforge.ui.responses import message_page, render_card, review_form_context
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import HumanReview

router = APIRouter()


@router.post("/review/edit", response_class=HTMLResponse)
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


@router.post("/review", response_class=HTMLResponse)
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
        # No fingerprint check on this branch — rerun is a deliberate
        # manual retry, always a new attempt, never deduplicated against
        # the cache (see compute_fingerprint()). On any failure, re-shows
        # review_form.html.jinja2 with the ORIGINAL (pre-rerun)
        # classification untouched plus an error banner — same principle
        # as the UnknownAttackRange bounce-back below: a failed action
        # here must not discard the reviewer's already-reviewed state.
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
