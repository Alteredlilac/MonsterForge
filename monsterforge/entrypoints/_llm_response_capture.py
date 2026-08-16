"""
Shared helper for calling classify_attack() while also capturing the
raw LLM response text it normally discards.

Used by every script that collects real (non-mocked) LLM data for
review — currently collect_real_classifications.py and
collect_real_pipeline_conversions.py, which capture different things
downstream of classification but share this exact same need.
"""
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.llm.client import get_llm_client
from monsterforge.llm.semantic_classification.attacks import (
    classify_attack,
    AttackSemanticResult,
)


def classify_with_raw_response(
        raw_attack: RawAttack) -> tuple[AttackSemanticResult, str | None]:
    """
    Call classify_attack() while also capturing the raw LLM response
    text alongside the parsed AttackSemanticResult it returns.

    classify_attack() only returns the parsed result and discards the
    raw response internally. Reaching into its private helpers
    (_call_attack_classifier, _parse_attack_result) to get both would
    couple callers to internals not meant to be used outside that
    module. Instead, GeminiClient.generate_text() — an already-public
    seam — is temporarily wrapped for the duration of this one call,
    then restored, regardless of outcome.

    Returns:
        (AttackSemanticResult, raw_response_text)
    """
    client = get_llm_client()
    original_generate_text = client.generate_text
    captured: dict[str, str] = {}

    def capturing_generate_text(question: str) -> str:
        text = original_generate_text(question)
        captured["value"] = text
        return text

    client.generate_text = capturing_generate_text
    try:
        result = classify_attack(raw_attack=raw_attack)
    finally:
        client.generate_text = original_generate_text

    return result, captured.get("value")
