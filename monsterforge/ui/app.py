"""
FastAPI web app for MVP 1: the same conversion + human review flow MVP
0.5 built for the CLI (entrypoints/convert_attack_cli.py,
entrypoints/_review_input.py), exposed over HTTP instead of a terminal
prompt.

Rerun is deliberately not included in this first web pass — it's left
as a later increment, once experience with the plain review flow here
shows what it should actually need. Correction otherwise has full
parity with the CLI: free text for description and the range's numeric
value, constrained dropdowns for move_type and the range's unit,
assigned_llm_score/edit_note on every decision.

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
from pathlib import Path
from typing import Literal
import jinja2
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import (
    raw_to_structured_attack,
)
from monsterforge.transformation.dnd.v3x.converters.attacks_converter import attack_converter
from monsterforge.pipeline.attack_pipeline import is_blank_attack
from monsterforge.llm.clients.gemini import ModelUnavailableError
from monsterforge.llm.semantic_classification.attacks import (
    ATTACK_PROMPT_TEMPLATE,
    AttackSemanticResult,
    SemanticContextInput,
    classify_attack,
)
from monsterforge.rendering.move_card_renderer import render_move_card_html_with_edit
from monsterforge.serialization.domain_to_json import card_to_json
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype, MoveType, UnitSystem
from monsterforge.validation.review import needs_review

app = FastAPI()
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

# NOTE:
# raw_fields.Attack.attack_type is deliberately an unconstrained str
# (see parsing/dnd/v3x/raw_fields/attacks.py), not an enum — but
# is_melee()/is_touch() in attacks_converter.py only recognize these
# exact English substrings ("melee" in attack_type.lower(), etc.). A
# free-text web input let a value like "mischia" (not matching any of
# them) silently fall through to "ranged", triggering an LLM range
# lookup for what was actually a melee attack. Constrained to a
# dropdown here for that reason — the CLI keeps free text, since a
# person typing at a terminal is already expected to match the
# parser's vocabulary.
ATTACK_TYPE_OPTIONS = ("melee", "melee touch", "ranged", "ranged touch")


# =====================
# SEMANTIC RESULT (DE)SERIALIZATION
# =====================
def _semantic_result_to_json(result: AttackSemanticResult) -> str:
    """Serialize an AttackSemanticResult for a hidden form field, to
    survive the round trip from POST /convert to POST /review — there's
    no server-side session to hold onto it instead."""
    return json.dumps({
        "description": result.description,
        "move_type": result.move_type.value,
        "move_range": (
            {
                "effect_range": result.move_range.effect_range,
                "range_unit_system": result.move_range.range_unit_system.value,
            }
            if result.move_range else None
        ),
        "confidence": result.confidence,
        "rationale": result.rationale,
    })


def _semantic_result_from_json(text: str) -> AttackSemanticResult:
    data = json.loads(text)
    move_range = None

    if data["move_range"]:
        move_range = EffectRange(
            effect_range=data["move_range"]["effect_range"],
            range_unit_system=UnitSystem(data["move_range"]["range_unit_system"]),
        )

    return AttackSemanticResult(
        description=data["description"],
        move_type=MoveType(data["move_type"]),
        move_range=move_range,
        confidence=data["confidence"],
        rationale=data["rationale"],
    )


# =====================
# SEMANTIC CONTEXT HELPERS
# =====================
def _semantic_context_from_form(
        additional_description: str,
        creature_description: str,
        creature_subtype: str) -> SemanticContextInput:
    return SemanticContextInput(
        additional_description=additional_description or None,
        creature_description=creature_description or None,
        creature_subtype=CreatureSubtype(creature_subtype) if creature_subtype else None,
    )


def _review_form_context(
        raw_attack: RawAttack,
        semantic_context: SemanticContextInput,
        semantic_result: AttackSemanticResult,
        template_name: str,
        image_uri: str) -> dict:
    """Shared template context for review_form.html.jinja2, built by
    both a fresh /convert classification and a revisit via /review/edit."""
    return {
        "raw_attack": raw_attack,
        "semantic_context": semantic_context,
        "semantic_result": semantic_result,
        "semantic_result_json": _semantic_result_to_json(semantic_result),
        "template_name": template_name,
        "image_uri": image_uri,
        "move_types": [move_type.value for move_type in MoveType],
        "unit_systems": [unit.value for unit in UnitSystem],
    }


# =====================
# DEAD-END RESPONSES
# =====================
def _message_page(message: str, status_code: int = 200) -> HTMLResponse:
    """A plain response for an outcome that produces no card (blank
    input, a classification failure, a rejected review) — always with a
    way back to /convert, rather than a bare dead-end message."""
    return HTMLResponse(f'<p>{message}</p><p><a href="/convert">Home</a></p>', status_code=status_code)


# =====================
# CARD RENDERING
# =====================
def _render_card(
        raw_attack: RawAttack,
        semantic_result: AttackSemanticResult,
        semantic_context: SemanticContextInput,
        template_name: str,
        image_uri: str) -> HTMLResponse:
    try:
        structured_attack = raw_to_structured_attack(raw_attack, semantic_result)
        move_card = attack_converter(structured_attack, attack_image_uri=image_uri or None)
    except Exception as exc:
        # NOTE:
        # Deliberately broad: raw_to_structured_attack()/attack_converter()
        # are deterministic regex/rule-based parsing over free-typed input
        # (e.g. an attack_effect like "2d80" or another malformed dice
        # expression) — without this, any parsing failure here reaches
        # the browser as FastAPI's generic, contextless 500 error page,
        # with the actual exception visible only in the server's own
        # terminal, not to whoever is using the form.
        return _message_page(f"Could not build the card: {exc}", status_code=422)

    card_data = json.loads(card_to_json(move_card))

    edit_form_fields = {
        "raw_attack_name": raw_attack.name,
        "raw_attack_modifier": raw_attack.modifier,
        "raw_attack_attack_type": raw_attack.attack_type,
        "raw_attack_attack_effect": raw_attack.attack_effect,
        "additional_description": semantic_context.additional_description or "",
        "creature_description": semantic_context.creature_description or "",
        "creature_subtype": semantic_context.creature_subtype.value if semantic_context.creature_subtype else "",
        "template_name": template_name,
        "image_uri": image_uri,
        "semantic_result_json": _semantic_result_to_json(semantic_result),
    }

    return HTMLResponse(render_move_card_html_with_edit(card_data, "/review/edit", edit_form_fields))


# =====================
# ROUTES
# =====================
@app.get("/convert", response_class=HTMLResponse)
def show_convert_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "convert_form.html.jinja2", {
        "creature_subtypes": [subtype.value for subtype in CreatureSubtype],
        "attack_types": ATTACK_TYPE_OPTIONS,
    })


@app.post("/convert", response_class=HTMLResponse)
def convert(
        request: Request,
        name: str = Form(""),
        modifier: str = Form(""),
        attack_type: Literal["", "melee", "melee touch", "ranged", "ranged touch"] = Form(""),
        attack_effect: str = Form(""),
        additional_description: str = Form(""),
        creature_description: str = Form(""),
        creature_subtype: str = Form(""),
        image_uri: str = Form(""),
        force_review: bool = Form(False),
        ) -> HTMLResponse:
    raw_attack = RawAttack(name=name, modifier=modifier, attack_type=attack_type, attack_effect=attack_effect)

    if is_blank_attack(raw_attack):
        return _message_page("No card produced: the submitted attack was blank.")

    semantic_context = _semantic_context_from_form(additional_description, creature_description, creature_subtype)

    try:
        semantic_result = classify_attack(
            raw_attack=raw_attack,
            additional_description=semantic_context.additional_description,
            creature_description=semantic_context.creature_description,
            creature_subtype=semantic_context.creature_subtype,
        )
    except ModelUnavailableError as exc:
        return _message_page(f"The configured LLM model is unavailable: {exc}", status_code=503)
    except Exception as exc:
        return _message_page(f"Classification failed: {exc}", status_code=502)

    # NOTE:
    # force_review is a per-request local value, never written to
    # config.validation_settings.ALWAYS_ON — that setting is shared,
    # process-wide, mutable state, safe for a single sequential batch
    # script (see entrypoints/collect_real_pipeline_conversions_with_simulated_review.py)
    # but not for a web server handling concurrent requests: mutating it
    # here could leak "always review" into an unrelated request that
    # never asked for it.
    if force_review or needs_review(confidence=semantic_result.confidence):
        return templates.TemplateResponse(
            request, "review_form.html.jinja2",
            _review_form_context(raw_attack, semantic_context, semantic_result, ATTACK_PROMPT_TEMPLATE, image_uri),
        )

    return _render_card(raw_attack, semantic_result, semantic_context, ATTACK_PROMPT_TEMPLATE, image_uri)


@app.post("/review/edit", response_class=HTMLResponse)
def edit_review(
        request: Request,
        raw_attack_name: str = Form(...),
        raw_attack_modifier: str = Form(...),
        raw_attack_attack_type: str = Form(...),
        raw_attack_attack_effect: str = Form(...),
        additional_description: str = Form(""),
        creature_description: str = Form(""),
        creature_subtype: str = Form(""),
        image_uri: str = Form(""),
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
    semantic_context = _semantic_context_from_form(additional_description, creature_description, creature_subtype)
    semantic_result = _semantic_result_from_json(semantic_result_json)

    return templates.TemplateResponse(
        request, "review_form.html.jinja2",
        _review_form_context(raw_attack, semantic_context, semantic_result, template_name, image_uri),
    )


@app.post("/review", response_class=HTMLResponse)
def review(
        raw_attack_name: str = Form(...),
        raw_attack_modifier: str = Form(...),
        raw_attack_attack_type: str = Form(...),
        raw_attack_attack_effect: str = Form(...),
        additional_description: str = Form(""),
        creature_description: str = Form(""),
        creature_subtype: str = Form(""),
        image_uri: str = Form(""),
        template_name: str = Form(...),
        semantic_result_json: str = Form(...),
        decision: str = Form(...),
        description: str = Form(""),
        move_type: str = Form(""),
        range_value: str = Form(""),
        range_unit: str = Form(""),
        assigned_llm_score: str = Form(""),
        edit_note: str = Form(""),
        ) -> HTMLResponse:
    raw_attack = RawAttack(
        name=raw_attack_name,
        modifier=raw_attack_modifier,
        attack_type=raw_attack_attack_type,
        attack_effect=raw_attack_attack_effect,
    )
    semantic_context = _semantic_context_from_form(additional_description, creature_description, creature_subtype)
    original_result = _semantic_result_from_json(semantic_result_json)

    # NOTE:
    # assigned_llm_score/edit_note are accepted for parity with the CLI's
    # HumanReview, but MVP 1 has no persistence layer either (same as
    # MVP 0.5) — they're read here and then discarded, not stored.

    if decision == "reject":
        return _message_page("No card produced: the classification was rejected.")

    if decision == "correct":
        corrected_range = None

        if range_value.strip():
            corrected_range = EffectRange(effect_range=int(range_value), range_unit_system=UnitSystem(range_unit))

        final_result = dataclasses.replace(
            original_result,
            description=description,
            move_type=MoveType(move_type),
            move_range=corrected_range,
        )
    else:
        final_result = original_result

    return _render_card(raw_attack, final_result, semantic_context, template_name, image_uri)
