"""
Shared mechanical components for D&D 3.x effect representations.

Defines reusable structures for range, critical hits, saving throws,
area effects, duration, usage/recharge, and damage over time.
These components are shared across attacks, special abilities, spells,
feats, special qualities, and psionic powers to avoid duplicated
effect-related fields.
"""
from dataclasses import dataclass, field
from .enums import (
    SavingThrowType,
    SavingThrowEffect,
    AreaEffectShape,
    Usage,
    UnitSystem,
    Duration,
    TargetType,
    CreatureType,
    CreatureSubtype,
    Ability,
    Alignment,
    RequirementOperator,
    )
from .dice_effects import TimeExpression, Damage

# =====================
# EFFECT RANGE
# =====================
@dataclass(kw_only=True)
class EffectRange:
    effect_range: int
    range_unit_system: UnitSystem


# =====================
# CRITICAL HIT 
# =====================
@dataclass(kw_only=True)
class CriticalHit:
    critical_threat_min: int | None = None  # minimum value of the critical threat range (e.g. 18 for 18-20)
    critical_multiplier: int | None = None  # critical multiplier (e.g. 2 for x2, 3 for x3) 

# =====================
# SAVING THROW 
# =====================
@dataclass(kw_only=True)
class SavingThrow:
    saving_throw_type: SavingThrowType
    saving_throw_value: int     # valore del tiro salvezza (es. CD 18)
    saving_throw_effect: SavingThrowEffect = SavingThrowEffect.NEGATES

# =====================
# DURATION
# =====================
@dataclass(kw_only=True)
class EffectDuration:
    duration: Duration = Duration.INSTANT # istantaneo di default 
    duration_time: TimeExpression | None = None # esempio 2d4+5 round

# =====================
# USAGE
# =====================
@dataclass(kw_only=True)
class EffectUsage:
    usage: Usage = Usage.UNLIMITED  # Utilizzo esempio("Illimitato", giornaliero, limitato, situazione)
    requires_recharge: bool = False
    recharge_time: TimeExpression | None = None # esempio 1d4 round
    uses_per_period: int | None = None # numero di utilizzi

# =====================
# AREA OF EFFECT
# =====================
@dataclass(kw_only=True)
class EffectArea:
    area_size: int                 # valore della misura dell'area (metri o piedi)
    area_unit_system: UnitSystem   # sistema di misura (metrico o imperiale)
    area_shape: AreaEffectShape    # forma dell'area di effetto

# =====================
# DAMAGE OVER TIME
# =====================
@dataclass(kw_only=True)
class DamageOverTime:  
    damage_frequency: TimeExpression
    damages: list[Damage] = field(default_factory=list)
    occurrences: int | None = None # quante volte si ripetono i danni?
    # damage_over_time_occurrences = None -> si ripetono continuamente, indefinitamente

# =====================
# TARGET
# =====================
@dataclass(kw_only=True)
class EffectTarget:
    target_type: TargetType  # creatura, oggetto, effetto, area, chiunque
    creature_type: CreatureType | None = None
    creature_subtype: CreatureSubtype | None = None
    target_description: str | None = None
    #requisiti
    required_level: int | None = None   # livello DV massimi richiesti
    required_level_operator: RequirementOperator | None = None # maggiore, minore

    required_ability_type: Ability | None = None # forza, destrezza ecc
    required_ability_value: int | None = None    # esempio intelligenza 10
    required_ability_operator: RequirementOperator | None = None # maggiore, minore

    target_alignment: list[Alignment] = field(default_factory=list)

# =====================
# BONUS
# =====================
@dataclass(kw_only=True)
class EffectModifier:
    # bonus derivanti dal tipo / sottotipo (esempio non morto)
    # bonus abilità 
    # bonus contro pietrificazione, disintegrazone, paralisi, sonno, veleno
    # bonus / malus # mettere se è situazionale / bersaglio 
    # eludere, eludere migliorato? 
    ...