"""
Orchestrate the D&D 3.x Attack -> MoveCard conversion pipeline.

This module composes the independently-testable stages already
implemented elsewhere (LLM classification, optional human review,
raw->structured conversion, structured->domain conversion) into the
single entry point consumed by the CLI entry points and, later, the API
layer.

No persistence or deduplication is performed here yet — every call
re-invokes the LLM classifier and produces a MoveCard with a fresh
random id. This is the intentional seam where those features get added
later, by wrapping this same function, without changing the stages it
composes.
"""
from typing import Callable
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.llm.semantic_classification.attacks import (
    ATTACK_PROMPT_TEMPLATE,
    AttackSemanticResult,
    SemanticContextInput,
    classify_attack,
)
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import (
    raw_to_structured_attack,
)
from monsterforge.transformation.dnd.v3x.converters.attacks_converter import attack_converter
from monsterforge.domain.moves import MoveCard
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype
from monsterforge.validation.enums import ValidationStatus
from monsterforge.validation.review import HumanReview, needs_review

# A caller-supplied handler that shows a classification to a human and
# returns the review outcome. Only invoked when needs_review() says the
# confidence warrants it; None (the default) skips review entirely,
# preserving MVP zero's behavior for callers that don't want one (batch
# scripts, tests).
ReviewHandler = Callable[[RawAttack, SemanticContextInput, AttackSemanticResult, str], HumanReview]


def is_blank_attack(raw_attack: RawAttack) -> bool:
    """A raw_attack with every field empty is an empty submission, not
    a real attack — nothing to classify or convert. Public (not
    underscore-prefixed) because collect_real_pipeline_conversions.py
    reuses it too, bypassing convert_attack() to capture raw_response."""
    return not any((raw_attack.name, raw_attack.modifier, raw_attack.attack_type, raw_attack.attack_effect))


def convert_attack(
        raw_attack: RawAttack,
        *,
        additional_description: str | None = None,
        creature_description: str | None = None,
        creature_subtype: CreatureSubtype | None = None,
        review_handler: ReviewHandler | None = None,
        template_name: str = ATTACK_PROMPT_TEMPLATE) -> MoveCard | None:
    """
    Convert a raw D&D 3.x attack into a domain MoveCard.

    Rules:
    - A blank raw_attack (every field empty) produces no card:
      classification is skipped entirely rather than spending an LLM
      call on an empty submission.
    - Otherwise, classify the attack semantically via the LLM
      (description, move type, range), using whatever optional context
      is supplied to sharpen the classification — none of it is
      required.
    - If review_handler is given and the classification's confidence
      needs review (validation.review.needs_review()), call it with the
      full classification context; a REJECTED outcome produces no card,
      APPROVED/CORRECTED continue with the (possibly edited) result.
    - Combine the final semantic result with the deterministic parsing
      of the raw fields into a structured Attack.
    - Convert the structured Attack into a MoveCard.

    template_name selects which classify_attack prompt template the
    initial classification runs against (see
    llm.semantic_classification.attacks.ATTACK_PROMPT_TEMPLATE_OPTIONS
    for the curated choices) — defaults to the baseline template,
    unchanged from before this parameter existed. Also forwarded to
    review_handler, so a reviewer sees which template actually produced
    the classification instead of always the default.

    No caching, deduplication, or persistence is performed here — every
    call re-invokes the LLM classifier and produces a MoveCard with a
    fresh random id.
    """
    if is_blank_attack(raw_attack):
        return None

    semantic_result = classify_attack(
        raw_attack=raw_attack,
        additional_description=additional_description,
        creature_description=creature_description,
        creature_subtype=creature_subtype,
        template_name=template_name,
    )

    if review_handler is not None and needs_review(confidence=semantic_result.confidence):
        semantic_context = SemanticContextInput(
            additional_description=additional_description,
            creature_description=creature_description,
            creature_subtype=creature_subtype,
        )
        review = review_handler(raw_attack, semantic_context, semantic_result, template_name)

        if review.status == ValidationStatus.REJECTED:
            return None

        semantic_result = review.result

    structured_attack = raw_to_structured_attack(raw_attack, semantic_result)

    return attack_converter(structured_attack)
