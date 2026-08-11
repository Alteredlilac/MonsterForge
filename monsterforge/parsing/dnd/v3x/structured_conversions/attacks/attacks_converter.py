"""
Convert raw D&D 3.x attack fields into structured Attack objects.

This module performs the deterministic conversion from the raw attack
representation extracted from D&D 3.x sources into the typed
"structured_data" representation.

The conversion process includes:

- parsing the attack bonus and attack mode
- determining whether the attack is melee, ranged, or touch
- extracting weapon range information
- converting raw damage information into structured Damage objects
- extracting critical-hit information
- converting special attack effects into structured SpecialAttack objects
- incorporating semantic information produced by the LLM classifier

The semantic classification itself is performed by
"llm.semantic_classification". This module consumes its result and combines
it with the deterministically extracted attack data to construct a complete
structured Attack.
"""
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.structured_data.dnd.v3x.attacks import Attack as StructuredAttack
from monsterforge.structured_data.dnd.v3x.effect_mechanics import EffectRange
from monsterforge.llm.semantic_classification.attacks import classify_attack
from .attack_mappings import KNOWN_ATTACKS
from .attacks_effects_parser import get_attack_effects


# =====================
# ERRORS
# =====================
class InvalidAttackConfigurationError(ValueError):
    """Raised when a raw attack contains an invalid configuration."""
    pass

class UnknownAttackRange(ValueError):
    """Raised when an attack range cannot be resolved."""
    pass

# =====================
# GET MODIFIER
# =====================
def get_modifier(raw_attack: RawAttack) -> int | None:
    """
    Convert the raw attack modifier into an integer.

    Empty or missing modifiers are represented as ``None``.

    Args:
        raw_attack: Raw D&D 3.x attack definition.

    Returns:
        The numeric attack bonus, or ``None`` if no modifier is provided.

    Raises:
        InvalidAttackConfigurationError:
            If the modifier is present but cannot be converted to an integer.
    """
    if not raw_attack.modifier:
        return None

    try:
        return int(raw_attack.modifier)
    except ValueError as exc:
        raise InvalidAttackConfigurationError(
            f"Invalid attack modifier: {raw_attack.modifier!r}"
        ) from exc

# =====================
# MALEE OR RANGED
# =====================
def is_melee(raw_attack: RawAttack) -> bool:
    """Return whether a raw attack is melee rather than ranged."""
    if not raw_attack.attack_type:
        return False

    attack_type = raw_attack.attack_type.lower()

    return "melee" in attack_type and "ranged" not in attack_type

# =====================
# TOUCH ATTACK
# =====================
def is_touch(raw_attack: RawAttack) -> bool:
    """Determine whether a raw attack is a touch attack."""
    if not raw_attack.attack_type:
        return False

    return "touch" in raw_attack.attack_type.lower()

# =====================
# WEAPON RANGE
# =====================
def get_known_attack_range(
        raw_attack: RawAttack,
        semantic_range_result: EffectRange | None
        ) -> EffectRange | None:
    """
    Determine the range of a raw D&D 3.x attack.

    The semantic classification result takes precedence when a range
    has been identified. If no semantic range is available, the function
    falls back to the known attack mappings.

    Args:
        raw_attack: Raw D&D 3.x attack definition.
        semantic_range_result: Range identified by the semantic classifier,
            or ``None`` if no range was determined.

    Returns:
        The resolved attack range, or ``None`` if the attack has no range.

    Raises:
        UnknownAttackRange:
            If no semantic range is available and the attack name is not
            present in ``KNOWN_ATTACKS``.
    """
    if is_melee(raw_attack):
        return None

    if semantic_range_result is not None:
        return semantic_range_result

    weapon_name = raw_attack.name.lower()

    if weapon_name not in KNOWN_ATTACKS:
        raise UnknownAttackRange(
            f"Attack '{raw_attack.name}' is not mapped; manual input required."
        )

    properties = KNOWN_ATTACKS[weapon_name]
    return properties.range


# =====================
# RAW TO STRUCTURED
# =====================
def raw_to_structured_attack(raw_attack: RawAttack) -> StructuredAttack:
    """
    Convert a raw D&D 3.x attack into a structured Attack.

    The conversion combines deterministic parsing of the raw attack
    fields and attack effects with semantic information produced by
    the attack classifier.

    Args:
        raw_attack: Raw D&D 3.x attack definition.

    Returns:
        A fully structured Attack containing the parsed attack properties,
        damage information, critical-hit information, special attack
        effects, and semantic classification results.
    """
    semantic_result = classify_attack(raw_attack) # Call the LLM classifier 
    touch_attack = is_touch(raw_attack)
    attack_effects = get_attack_effects(raw_attack)


    return StructuredAttack(
        name = raw_attack.name,
        move_type = semantic_result.move_type,
        description= semantic_result.description,
        attack_bonus = get_modifier(raw_attack),
        melee = is_melee(raw_attack),
        touch = touch_attack,
        attack_range = get_known_attack_range(raw_attack, semantic_result.move_range), 
        damages = attack_effects.damages,
        critical_hit = attack_effects.critical_hit,  
        effects = attack_effects.special_attacks 
        )
