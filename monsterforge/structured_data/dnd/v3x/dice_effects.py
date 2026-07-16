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
# DAMAGE
# =====================
@dataclass(kw_only=True)
class Damage:
    dice_number : int | None = None       # numero di dadi
    dice_type: DiceType | None = None  # tipo di dado d6 , d8 eccetera
    damage_type: DamageType | None = None # tipo di danni (normali, fuoco)
    affected_ability: Ability | None = None
    damage_bonus: int | None = None       # bonus ai danni
    damage_bonus_type: DamageType | None = None # tipo di danni bonus (normali, fuoco)

# =====================
# HEALING
# =====================
@dataclass(kw_only=True)
class Healing:
    dice_number : int | None = None       # numero di dadi
    dice_type: DiceType | None = None  # tipo di dado d6 , d8 eccetera
    affected_ability: Ability | None = None
    healing_bonus: int | None = None      # bonus alla cura
    restores_full_amount: bool = False    # ripristina completamente il valore (es. HP o caratteristica)

# =====================
# TIME
# =====================
@dataclass(kw_only=True)
class TimeExpression:
    unit: TimeUnit | None = None          # round, minuti, ore, giorni, anni
    dice_number: int | None = None        # es: 2 (per 2d4)
    dice_type: DiceType | None = None     # es: d4
    modifier: int | None = None           # es: +1