"""
Provide internal helper functions for parsing D&D 3.x attack effects.

This module contains the internal parsing utilities used by the
attack-effects parser to normalize raw text, resolve known enum values, and
parse individual dice and damage expressions.

The helper functions include:

- normalizing whitespace and raw textual values
- resolving known DamageType values from textual damage types
- resolving known Ability values from ability names and abbreviations
- parsing dice expressions and their numeric modifiers
- parsing individual damage and effect components into structured Damage
  objects

These functions are implementation details of the attack-effects parser and
are not intended to be used directly as part of the public parsing API.
They rely on the regular-expression patterns and lookup mappings defined in
the corresponding attack-effects modules.
"""
from monsterforge.structured_data.dnd.v3x.dice_effects import Damage, DiceType
from monsterforge.structured_data.dnd.v3x.enums import Ability, DamageType
from .attacks_effects_lookups import DAMAGE_TYPE_MAP, ABILITY_MAP
from .attacks_effects_patterns import (DICE_PATTERN,
                                       CRITICAL_MULTIPLIER_PATTERN,
                                       CRITICAL_THRESHOLD_PATTERN,
                                       FIXED_TYPED_DAMAGE_PATTERN,
                                       TYPED_DICE_PATTERN,
                                       ABILITY_PATTERN)

# =====================
# ERRORS
# =====================
class InvalidDiceTypeError(ValueError):
    """Raised when a raw dice expression contains an unsupported dice type."""
    pass

# =====================
# NORMALIZE TEXT
# =====================
def _normalize_text(text: str) -> str:
    """Normalize whitespace and surrounding punctuation."""
    return " ".join(text.strip().split())


# =====================
# DAMAGE TYPE
# =====================
def _get_damage_type(text: str) -> DamageType | None:
    """Return a known DamageType for a normalized text value."""
    return DAMAGE_TYPE_MAP.get(text.lower().strip())

# =====================
# ABILITY
# =====================
def _get_ability(text: str) -> Ability | None:
    """
    Return the first known Ability mentioned in the text.
    """
    match = ABILITY_PATTERN.search(text)

    if not match:
        return None

    return ABILITY_MAP[match.group(1).lower()]

# =====================
# DICE EXPRESSION
# =====================
def _parse_dice_expression(
    expression: str,
) -> tuple[int, DiceType, int | None] | None:
    """
    Parse a dice expression such as:
        1d6
        2d8+4
        1d4-2

    Returns:
        (dice_number, dice_type, damage_bonus)
    """
    match = DICE_PATTERN.fullmatch(expression.strip())

    if not match:
        return None

    dice_number = int(match.group("number"))
    try:
        dice_type = DiceType(f"d{match.group('type')}")
    except ValueError as exc:
        raise InvalidDiceTypeError(
            f"Unsupported dice type: d{match.group('type')}"
        ) from exc

    bonus = match.group("bonus")
    damage_bonus = int(bonus) if bonus else None

    return dice_number, dice_type, damage_bonus

# =====================
# DAMAGE
# =====================

def _parse_damage_part(
    part: str,
    ) -> Damage | None:
    """
    Parse one damage/effect component.

    Rules:
    - A component is only considered damage if it expresses a quantity,
      via dice or a numeric bonus. A bare DamageType keyword with no
      dice/bonus of its own (e.g. "energy drain", "positive energy",
      "trip") never becomes a Damage, regardless of where it appears in
      the attack_effect text — it is left for the caller to treat as a
      special attack/effect instead.

    Args:
        part: Raw damage or effect component to parse.

    Returns:
        A structured Damage object if the component represents damage,
        otherwise None.

    Examples:
        2d6+4
        1d8 fire
        1 fire
        5
        1d6 Str
        1d4 Wisdom drain
    """
    part = _normalize_text(part)

    if not part:
        return None

    # NOTE:
    # Remove critical notation.
    # Example: 1d6+1/19-20 -> 1d6+1

    part = CRITICAL_THRESHOLD_PATTERN.sub("", part)
    part = CRITICAL_MULTIPLIER_PATTERN.sub("", part)
    part = _normalize_text(part)

    # NOTE:
    # Ability effect
    # Examples: 1d4 Wisdom drain, 1d6 Str

    ability = _get_ability(part)

    if ability:
        dice_match = DICE_PATTERN.search(part)

        if dice_match:
            parsed_dice = _parse_dice_expression(
                dice_match.group(0)
            )

            if parsed_dice:
                dice_number, dice_type, damage_bonus = parsed_dice

                return Damage(
                    dice_number=dice_number,
                    dice_type=dice_type,
                    damage_type=None,
                    affected_ability=ability,
                    damage_bonus=damage_bonus,
                )

        # NOTE: 
        # If an ability is mentioned but there is no dice
        # expression, it is not enough to create Damage.
        return None

    # NOTE:
    # Typed dice damage
    # Examples: 1d8 fire, 2d6 acid

    typed_dice_match = TYPED_DICE_PATTERN.fullmatch(part)

    if typed_dice_match:
        dice_expression = typed_dice_match.group("dice")
        damage_type_text = typed_dice_match.group("type").lower().strip()

        damage_type = _get_damage_type(damage_type_text)

        if damage_type:
            parsed_dice = _parse_dice_expression(dice_expression)

            if parsed_dice:
                dice_number, dice_type, damage_bonus = parsed_dice

                return Damage(
                    dice_number=dice_number,
                    dice_type=dice_type,
                    damage_type=damage_type,
                    damage_bonus=damage_bonus,
                )

    # NOTE:
    # Normal dice damage
    # Examples: 2d6+4, 1d4-2, 1d8

    parsed_dice = _parse_dice_expression(part)

    if parsed_dice:
        dice_number, dice_type, damage_bonus = parsed_dice

        return Damage(
            dice_number=dice_number,
            dice_type=dice_type,
            damage_type=DamageType.PHYSICAL,
            damage_bonus=damage_bonus,
        )

    # NOTE:
    # Fixed typed damage
    # Examples: 1 fire, 2 acid

    fixed_damage_match = FIXED_TYPED_DAMAGE_PATTERN.fullmatch(part)

    if fixed_damage_match:
        damage_number = int(fixed_damage_match.group("number"))
        damage_type_text = fixed_damage_match.group("type").lower().strip()

        damage_type = _get_damage_type(damage_type_text)

        if damage_type:
            return Damage(
                dice_number=None,
                dice_type=None,
                damage_type=damage_type,
                damage_bonus=damage_number,
            )

    # NOTE:
    # Bare fixed damage, no type
    # Examples: 5, 12
    # Defaults to PHYSICAL, mirroring the same default already applied
    # to untyped dice damage above — an explicit type is optional, not
    # required, for a bare numeric value to count as damage.

    if part.isdigit():
        return Damage(
            dice_number=None,
            dice_type=None,
            damage_type=DamageType.PHYSICAL,
            damage_bonus=int(part),
        )

    # NOTE:
    # A bare DamageType keyword with no dice/bonus (e.g. "positive
    # energy", "energy drain", "trip") never becomes a Damage on its
    # own — it carries no quantifiable value to compute. It is always
    # left for the caller to treat as a special attack/effect, whether
    # it is the entire attack_effect or a component after "plus".

    return None
