"""
Round-tripping an AttackSemanticResult through a hidden form field.

This web app keeps no server-side session: a classification result has
to survive from one POST/GET to the next (/convert -> /review,
/review/edit -> /review, a library reopen -> /review) as a hidden form
field's value rather than something held in memory between requests.
These two functions are the only place that (de)serialization happens.
"""
import json

from monsterforge.llm.semantic_classification.attacks import AttackSemanticResult, semantic_result_to_dict
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import MoveType, UnitSystem


def semantic_result_to_json(result: AttackSemanticResult) -> str:
    """Serialize an AttackSemanticResult for a hidden form field, to
    survive the round trip from POST /convert to POST /review — there's
    no server-side session to hold onto it instead."""
    return json.dumps(semantic_result_to_dict(result))


def semantic_result_from_json(text: str) -> AttackSemanticResult:
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
