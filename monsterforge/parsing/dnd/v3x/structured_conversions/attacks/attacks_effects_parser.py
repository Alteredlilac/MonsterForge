"""
Parse raw D&D 3.x attack-effect fields into structured effect objects.

This module performs the deterministic parsing of the raw "attack_effect"
field extracted from D&D 3.x sources into the typed "structured_data"
representation.

The parsing process includes:

- extracting damage components and their associated damage types
- identifying ability damage or drain effects
- extracting critical-threat ranges and critical multipliers
- identifying special attack or effect names
- converting special attack names into structured SpecialAttack objects
- combining all parsed effects into a ParsedAttackEffects result

The parsing is intentionally deterministic and does not perform semantic
classification of unknown special attacks. Special attack resolution and
semantic classification can be incorporated separately once the corresponding
structured special attacks and classification mechanisms are available.
"""
import re
from dataclasses import dataclass
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.structured_data.dnd.v3x.special_attacks import SpecialAttack
from monsterforge.structured_data.dnd.v3x.enums import SpecialAbilityType
from monsterforge.structured_data.dnd.v3x.dice_effects import Damage
from monsterforge.structured_data.dnd.v3x.effect_mechanics import CriticalHit
from .attacks_effects_patterns import (CRITICAL_MULTIPLIER_PATTERN,
                                       CRITICAL_THRESHOLD_PATTERN)
from .attacks_effects_helpers import _normalize_text, _parse_damage_part


# =====================
# PARSED RESULT
# =====================
@dataclass
class ParsedAttackEffects:
    damages: list[Damage]
    critical_hit: CriticalHit | None
    special_attacks: list[SpecialAttack]


# =====================
# CRITICAL HIT
# =====================
def get_critical(raw_attack: RawAttack) -> CriticalHit | None:
    """
    Parse critical-hit information.

    Examples:
        1d6+4/19-20
        1d8/×3
        4d8+17/18-20/×3
    """
    text = raw_attack.attack_effect

    if not text:
        return None

    threshold_match = CRITICAL_THRESHOLD_PATTERN.search(text)
    multiplier_match = CRITICAL_MULTIPLIER_PATTERN.search(text)

    if not threshold_match and not multiplier_match:
        return None

    return CriticalHit(
        critical_threat_min=(
            int(threshold_match.group("threshold"))
            if threshold_match
            else None
        ),
        critical_multiplier=(
            int(multiplier_match.group("multiplier"))
            if multiplier_match
            else None
        ),
    )


# =====================
# DAMAGE
# =====================
def get_damages(raw_attack: RawAttack) -> list[Damage]:
    """
    Parse all damage components from an attack effect.

    Examples:

        2d6+4 -> one physical Damage

        1d6+1 plus 1 fire
            -> physical Damage
            -> 1 fixed fire damage

        1d8 fire plus combustion
            -> one fire Damage

        2d6+4 plus 2d6 acid
            -> physical Damage
            -> acid Damage

        1d6 plus energy drain
            -> one physical Damage

        1d4 Wisdom drain
            -> one Damage affecting Wisdom
    """
    text = raw_attack.attack_effect

    if not text:
        return []

    text = _normalize_text(text)

    # NOTE:
    # Split only on the explicit D&D separator "plus".
    parts = re.split(r"\s+plus\s+", text, flags=re.IGNORECASE)

    damages: list[Damage] = []

    for index, part in enumerate(parts):
        damage = _parse_damage_part(
            part,
            allow_standalone_damage_type=(index == 0),
        )

        if damage is not None:
            damages.append(damage)

    return damages


# =====================
# SPECIAL ATTACK NAMES
# =====================
def _get_special_attacks_names(raw_attack: RawAttack) -> list[str]:
    """
    Extract special attack/effect names from attack_effect.

    Examples:
        1d6+8 plus slime -> ["slime"]
        1d6 plus poison -> ["poison"]
        1d3+2 plus corporeal instability -> ["corporeal instability"]
        paralysis -> ["paralysis"]
        1d8 fire plus combustion -> ["combustion"]
        1d6 plus energy drain -> []
        because "energy drain" is represented by DamageType.
    """
    text = raw_attack.attack_effect

    if not text:
        return []

    text = _normalize_text(text)

    parts = re.split(r"\s+plus\s+", text, flags=re.IGNORECASE)

    special_attacks: list[str] = []

    # NOTE:
    # Everything after "plus" can be either:
    #   - damage
    #   - typed damage
    #   - a special attack/effect
    # _parse_damage_part() decide whether it is a
    # structured Damage. If not, it is a special attack.

    if len(parts) > 1:
        for part in parts[1:]:
            part = _normalize_text(part)

            if not part:
                continue

            damage = _parse_damage_part(part)

            if damage is None:
                special_attacks.append(part)

        return special_attacks

    # NOTE:
    # No "plus": e.g "paralysis" , "rust"
    # should become special attacks.
    # But: "2d6+4", "1d4 Wisdom drain", "1d8 fire"
    # are already structured data.

    if _parse_damage_part(text) is not None:
        return []

    return [text]

def get_special_attacks(raw_attack: RawAttack) -> list[SpecialAttack]:
    """Convert special attack names into SpecialAttack objects."""
    special_attack_names = _get_special_attacks_names(raw_attack)

    return [
        SpecialAttack(
            name=special_attack_name,
            special_ability_type=SpecialAbilityType.EXTRAORDINARY,
            # EXTRAORDINARY usato solo come placeholder perchè obbligatorio passala
        )
        for special_attack_name in special_attack_names
    ]

    
# TODO:
# Update get_special_attacks so that, once special attacks are available,
# it resolves them from the special-attacks database or retrieves them
# from the semantic classifier.

# =====================
# ATTACK EFFECTS
# =====================
def get_attack_effects(raw_attack: RawAttack) -> ParsedAttackEffects:
    """
    Parse all structured effects contained in attack_effect.
    """
    return ParsedAttackEffects(
        damages=get_damages(raw_attack),
        critical_hit=get_critical(raw_attack),
        special_attacks=get_special_attacks(raw_attack),
    )
