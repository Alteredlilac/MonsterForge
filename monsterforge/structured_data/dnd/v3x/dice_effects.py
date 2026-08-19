"""
Shared dice-based effect representations for D&D 3.x structured data.

Damage and Healing share a common dice-based structure (dice + bonus),
but represent opposite effects.

These models are reused across multiple systems, including attacks,
special attacks, spells, psionic powers, items, and feats.
"""
from dataclasses import dataclass
from .enums import DiceType, DamageType, Ability, TimeUnit

# =====================
# DICE
# =====================
@dataclass(kw_only=True)
class Dice:    
    dice_number: int | None = None        # e.g. 2 (for 2d4)
    dice_type: DiceType | None = None     # e.g. d4
    modifier: int | None = None           # e.g. +1


# =====================
# DAMAGE
# =====================
@dataclass(kw_only=True)
class Damage:
    dice_number : int | None = None
    dice_type: DiceType | None = None  # die type, e.g. d6, d8
    damage_type: DamageType | None = None # e.g. physical, fire
    affected_ability: Ability | None = None
    damage_bonus: int | None = None
    damage_bonus_type: DamageType | None = None # type of the bonus damage, e.g. physical, fire

# =====================
# HEALING
# =====================
@dataclass(kw_only=True)
class Healing:
    dice_number : int | None = None
    dice_type: DiceType | None = None  # die type, e.g. d6, d8
    affected_ability: Ability | None = None
    healing_bonus: int | None = None
    restores_full_amount: bool = False    # fully restores the value, e.g. HP or an ability score

# =====================
# TIME
# =====================
@dataclass(kw_only=True)
class TimeExpression:
    unit: TimeUnit | None = None          # rounds, minutes, hours, days, years
    dice_number: int | None = None        # e.g. 2 (for 2d4)
    dice_type: DiceType | None = None     # e.g. d4
    modifier: int | None = None           # e.g. +1