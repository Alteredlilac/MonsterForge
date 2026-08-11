"""
Classificatore semantico per Attacks
"""
from dataclasses import dataclass
from typing import TypedDict
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.domain.enums import MoveType
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.structured_data.dnd.v3x.enums import UnitSystem


@dataclass
class AttackSemanticResult():
    description: str
    move_type: MoveType
    move_range: EffectRange | None 
    # confidence: float

# NOTE:
# AttackSemanticResult non è semplicemente "dati che mancano a StructuredAttack".
# È il risultato tecnico della fase LLM, che contiene sia dati utili al dominio
# sia metadati necessari alla pipeline.

# =====================
# DESCRIPTION
# =====================
# Fake semantic classifier used only as a stub
def attack_description(raw_attack: RawAttack) -> str:
    """
    Generate the attack description.

    Design note:
        This is currently a stub for a future semantic classifier.

        The initial description template is expected to follow this structure:
            "{adjective based on damage [e.g. 'powerful', 'sudden']}"
            Attack.name | if an effect is present | that {effect description}

        The final wording and generation logic will be refined when the
        semantic classifier is implemented.

        If Attack.touch is True, the MoveCard description should also state
        that this attack grants a +2 attack-roll bonus when used.
    """
    return ""

# =====================
# ATTACK TYPE
# =====================
# Fake semantic classifier used only as a stub
def attack_type(raw_attack: RawAttack) -> MoveType:
    """
    Classify the attack as physical or magical.

    Design note:
        This is currently a stub for a future semantic classifier.
        The final implementation will determine the MoveType of the attack
        from its structured D&D 3.x properties and semantic characteristics.
    """
    ...

# =====================
# ATTACK RANGE
# =====================
# Fake semantic classifier used only as a stub
def attack_range(raw_attack: RawAttack) -> EffectRange | None:
    """
    Determine the range of a raw D&D 3.x attack.

    Design note:
        This is currently a stub for a future semantic classifier.
        The final implementation will determine the attack range using
        known attack mappings and, when necessary, semantic classification.

    Args:
        raw_attack: Raw D&D 3.x attack definition.

    Returns:
        The attack range, or ``None`` if non è possibile determinare semanticamente il range
    """
    ...

# =====================
# FAKE LLM - CLASSIFY ATTACK
# =====================
def classify_attack(raw_attack: RawAttack) -> AttackSemanticResult:
    return AttackSemanticResult(
        description=attack_description(raw_attack),
        move_type=attack_type(raw_attack),
    )
