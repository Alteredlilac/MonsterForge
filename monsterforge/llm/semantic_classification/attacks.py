"""
Semantic classifier for D&D 3.x attacks.

This module prepares the contextual information required by the LLM
classifier, renders the attack-classification prompt, sends it to the
LLM, and converts the structured response into an AttackSemanticResult.

The classification pipeline is organized as follows:

attacks.py
│
├── AttackSemanticContext        # TypedDict, temporary input data
│
├── AttackSemanticResult         # dataclass, classification result
│
├── _build_attack_prompt(...)    # prepares the prompt context/template
│
├── _call_attack_classifier(...) # calls the LLM classifier
│
├── _parse_attack_result(...)    # validates/converts JSON into typed result
│
└── classify_attack(...)         # public API of the module

The attack-classification prompt is defined separately in:

llm/
├── prompts/
│   └── attacks/
│       └── classify_attack.jinja2
│
└── semantic_classification/
    └── attacks.py

The expected LLM response has the following structure:

{
    "description": "A sudden ray of electricity.",
    "move_type": "magical",
    "move_range": {
        "value": 30,
        "unit": "feet"
    },
    "confidence": 0.91,
    "rationale": "The attack is a ranged touch attack that deals electricity damage."
}

The LLM response is an intermediate technical result of the semantic
classification stage and is converted into the typed AttackSemanticResult
before being consumed by the structured attack conversion pipeline.
"""

import json
from dataclasses import dataclass
from typing import TypedDict

from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from monsterforge.llm.client import get_llm_client
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.structured_data.dnd.v3x.enums import (
    CreatureSubtype,
    MoveType,
    UnitSystem,
)
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange


# =====================
# CONSTANTS
# =====================
PROMPT_TEMPLATE_DIR = (
    Path(__file__).resolve().parents[1] / "prompts"  
)
ATTACK_PROMPT_TEMPLATE = "attacks/classify_attack.jinja2"

# NOTE:
# Model selection is centralized in llm.client.get_llm_client() (see
# _DEFAULT_MODEL there), not repeated per classifier module.



# =====================
# CONTEXT
# =====================
# NOTE:
# TypedDict is used for temporary data passed between functions within the
# semantic classification pipeline. These structures represent contextual
# input data rather than standalone domain objects, so they do not require
# identity, behavior, or domain invariants.

class AttackSemanticContext(TypedDict):
    raw_attack: RawAttack
    additional_description: str | None
    creature_description: str | None
    creature_subtype: CreatureSubtype | None


# =====================
# RESULT
# =====================
@dataclass
class AttackSemanticResult:
    # Required by the structured_data representation
    description: str
    move_type: MoveType
    move_range: EffectRange | None

    # Used by the general pipeline and for logging
    confidence: float
    rationale: str


# NOTE:
# AttackSemanticResult is not simply a collection of data missing from
# StructuredAttack. It represents the technical result of the LLM semantic
# classification stage, containing both domain-relevant information and
# metadata required by the processing pipeline.


# =====================
# CONTEXT INPUT
# =====================
@dataclass(kw_only=True)
class SemanticContextInput:
    """
    The optional classification context a caller can supply, as a real
    dataclass rather than the AttackSemanticContext TypedDict above.

    AttackSemanticContext is internal, disposable input to
    _build_attack_prompt() (also carrying raw_attack, and explicitly
    documented as needing no identity/equality). SemanticContextInput is
    for callers that need to hold onto and compare this context outside
    that call — e.g. an interactive entry point collecting it, or a
    human review handler receiving it alongside a classification result.
    """
    additional_description: str | None
    creature_description: str | None
    creature_subtype: CreatureSubtype | None


# =====================
# ERRORS
# =====================
class InvalidAttackSemanticResultError(ValueError):
    """Raised when the LLM attack classification result is invalid."""
    pass

class PromptBuildingError(RuntimeError):
    """Raised when an LLM prompt cannot be built."""
    pass

class AttackClassificationError(RuntimeError):
    """Raised when the attack classification request fails."""
    pass

# =====================
# BUILD PROMPT
# =====================
def _build_attack_prompt(
    context: AttackSemanticContext,
) -> str:
    """
    Build the prompt used for semantic attack classification.

    The prompt is rendered from the dedicated Jinja2 attack-classification
    template and receives the raw attack data together with any additional
    contextual information available to the classifier.

    Args:
        context: Temporary contextual data required by the prompt.

    Returns:
        The rendered prompt string.
    """
    try:
        environment = Environment(
            loader=FileSystemLoader(PROMPT_TEMPLATE_DIR),
            autoescape=False,      # Prompt is plain text, not HTML
        )

        template = environment.get_template(ATTACK_PROMPT_TEMPLATE)

        return template.render(
            raw_attack=context["raw_attack"],
            additional_description=context["additional_description"],
            creature_description=context["creature_description"],
            creature_subtype=context["creature_subtype"],
        )

    except Exception as exc:
        raise PromptBuildingError( 
            "Failed to render attack classification prompt."
        ) from exc


# =====================
# CALL LLM
# =====================
def _call_attack_classifier(
    prompt: str,
) -> str:
    """
    Call the LLM attack classifier with a rendered classification prompt.

    The LLM is expected to return a JSON response containing
    the semantic attack classification and its confidence value.

    Args:
        prompt: Rendered attack-classification prompt.

    Returns:
        The raw structured response returned by the LLM.
    """
    client = get_llm_client()

    try:
        response = client.generate_text(prompt)
    except RuntimeError as exc:
        raise AttackClassificationError(
            "Attack classification request failed."
        ) from exc

    if not response:
        raise InvalidAttackSemanticResultError(
            "Attack classification returned an empty response."
        )

    return response


# =====================
# PARSE RESULT
# =====================
def _parse_attack_result(
    response: str,
) -> AttackSemanticResult:
    """
    Validate and convert the LLM response into an AttackSemanticResult.

    The response is expected to contain the fields required by
    AttackSemanticResult and to use the corresponding structured enum and
    value representations.

    Args:
        response: Raw structured response returned by the LLM.

    Returns:
        A validated AttackSemanticResult.

    Raises:
        InvalidAttackSemanticResultError:
            If the response cannot be parsed or does not contain valid
            attack classification data.
    """
    try:
        data = json.loads(response)
    except json.JSONDecodeError as exc:
        raise InvalidAttackSemanticResultError(  
            "LLM response is not valid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise InvalidAttackSemanticResultError(
            "LLM response must be a JSON object."
        )

    required_fields = {
        "description",
        "move_type",
        "move_range",
        "confidence",
        "rationale",
    }

    if set(data) != required_fields:   
        raise InvalidAttackSemanticResultError(
            "LLM response contains invalid or missing fields."
        )

    description = data["description"]
    move_type_value = data["move_type"]
    move_range_data = data["move_range"]
    confidence = data["confidence"]
    rationale = data["rationale"]

    if not isinstance(description, str):
        raise InvalidAttackSemanticResultError( 
            "'description' must be a string."
        )

    if not isinstance(rationale, str):
        raise InvalidAttackSemanticResultError( 
            "'rationale' must be a string."
        )

    try:
        move_type = MoveType(move_type_value)
    except (ValueError, TypeError) as exc:
        raise InvalidAttackSemanticResultError(
            f"Invalid move_type: {move_type_value!r}"
        ) from exc

    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise InvalidAttackSemanticResultError(
            "'confidence' must be a number."
        )

    if not 0.0 <= confidence <= 1.0:
        raise InvalidAttackSemanticResultError(
            "'confidence' must be between 0.0 and 1.0."
        )

    move_range = _parse_effect_range(move_range_data)

    return AttackSemanticResult(
        description=description,
        move_type=move_type,
        move_range=move_range,
        confidence=float(confidence),
        rationale=rationale,
    )


# =====================
# PARSE EFFECT RANGE
# =====================
def _parse_effect_range(
    data: object,
) -> EffectRange | None:
    """
    Convert the LLM move-range object into an EffectRange.

    The LLM represents distance units using human-readable values:
    ``feet`` or ``meters``. These are converted into the corresponding
    UnitSystem enum used by the structured D&D 3.x model.

    Args:
        data: Raw ``move_range`` value returned by the LLM.

    Returns:
        An EffectRange instance, or ``None`` when no reliable range exists.

    Raises:
        InvalidAttackSemanticResultError:
            If the range object is malformed or contains an unsupported unit.
    """
    if data is None:
        return None

    if not isinstance(data, dict):
        raise InvalidAttackSemanticResultError(
            "'move_range' must be an object or null."
        )

    if set(data) != {"value", "unit"}:
        raise InvalidAttackSemanticResultError(
            "'move_range' must contain exactly 'value' and 'unit'."
        )

    value = data["value"]
    unit = data["unit"]

    if not isinstance(value, (int, float)):
        raise InvalidAttackSemanticResultError(
            "Move range value must be numeric."
        )

    if value < 0:
        raise InvalidAttackSemanticResultError(
            "Move range value cannot be negative."
        )

    unit_mapping = {
        "feet": UnitSystem.IMPERIAL,
        "meters": UnitSystem.METRIC,
    }

    if unit not in unit_mapping:
        raise InvalidAttackSemanticResultError(
            f"Unsupported move range unit: {unit!r}"
        )

    return EffectRange(
        effect_range=value,
        range_unit_system=unit_mapping[unit],
    )


# =====================
# CLASSIFY ATTACK
# =====================
def classify_attack(
    *,
    raw_attack: RawAttack,
    additional_description: str | None = None,
    creature_description: str | None = None,
    creature_subtype: CreatureSubtype | None = None,
) -> AttackSemanticResult:
    """
    Classify a D&D 3.x attack using the semantic LLM pipeline.

    This is the public entry point for attack semantic classification.
    It prepares the classification context, builds the LLM prompt, calls
    the classifier, and converts the response into an AttackSemanticResult.

    Args:
        raw_attack: Raw D&D 3.x attack definition.
        additional_description: Optional additional description or context
            associated with the attack.
        creature_description: Optional description of the creature using
            the attack.
        creature_subtype: Optional D&D 3.x creature subtype.

    Returns:
        The semantic classification result for the attack.
    """
    context: AttackSemanticContext = {
        "raw_attack": raw_attack,
        "additional_description": additional_description,
        "creature_description": creature_description,
        "creature_subtype": creature_subtype,
    }

    prompt = _build_attack_prompt(context)
    response = _call_attack_classifier(prompt)

    return _parse_attack_result(response)
