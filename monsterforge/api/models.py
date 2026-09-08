"""
Pydantic request/response models for api/routes.py.

Kept in its own module rather than inline in routes.py: this file
answers "what shape does a request or response have", routes.py
answers "what does handling one actually do" -- two different
questions, the same split this project already draws elsewhere between
static data and the logic that consumes it (rules/ vs. transformation/).
"""
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from monsterforge.llm.semantic_classification.attacks import ATTACK_PROMPT_TEMPLATE
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import ATTACK_TYPE_OPTIONS
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype, UnitSystem


class ErrorResponse(BaseModel):
    """The one error shape used by every route in this API -- the HTTP
    status code carries the actual meaning (404 not found, 422 invalid
    state, 500 data-integrity anomaly, 502 classification failed, 503
    model unavailable), this just carries a readable message."""
    error: str


class PendingReviewResponse(BaseModel):
    """Returned instead of a card when the confidence gate requires
    human review -- this API never resolves that itself, only reports
    it. The decision (approve/correct/reject/rerun) stays exclusively
    on the web, through POST /review, against this same event_id."""
    status: Literal["pending_review"] = "pending_review"
    event_id: str


class AttackCreateRequest(BaseModel):
    """
    POST /api/cards body -- the same raw attack fields, optional
    semantic context, optional explicit range, and optional card artwork
    ui/routes/convert.py's own /convert form collects, minus a
    force-review override: this API's confidence gate is never
    request-configurable, so there's no equivalent field to expose.

    name/attack_type are required rather than defaulting to "" the way
    the web form's fields do: a JSON caller either sends a real attack
    or doesn't call this endpoint, so there's no equivalent of a
    person accidentally submitting a blank form to short-circuit.
    """
    name: str
    modifier: str = ""
    attack_type: Literal[*ATTACK_TYPE_OPTIONS]
    attack_effect: str = ""
    additional_description: str | None = None
    creature_description: str | None = None
    creature_subtype: CreatureSubtype | None = None
    range_value: int | None = Field(default=None, ge=1)
    range_unit: UnitSystem | None = None
    image_uri: str | None = None
    template_name: str = ATTACK_PROMPT_TEMPLATE

    @model_validator(mode="after")
    def _range_value_and_unit_given_together(self) -> "AttackCreateRequest":
        if (self.range_value is None) != (self.range_unit is None):
            raise ValueError("range_value and range_unit must be given together.")
        return self
