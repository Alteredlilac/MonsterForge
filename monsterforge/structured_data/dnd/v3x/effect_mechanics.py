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
    DiceType, 
    ModifierTarget,
    ModifierConditionType,
    GrantedType
    )
from .dice_effects import TimeExpression, Damage, Dice
from .creature_stats import ArmorClass, Abilities, Saves
from .skills import Skills

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
    saving_throw_value: int     # e.g. DC 18
    saving_throw_effect: SavingThrowEffect = SavingThrowEffect.NEGATES

# =====================
# DURATION
# =====================
@dataclass(kw_only=True)
class EffectDuration:
    duration: Duration = Duration.INSTANT
    duration_time: TimeExpression | None = None # e.g. 2d4+5 rounds

# =====================
# USAGE
# =====================
@dataclass(kw_only=True)
class EffectUsage:
    usage: Usage = Usage.UNLIMITED  # e.g. unlimited, daily, limited, situational
    requires_recharge: bool = False
    recharge_time: TimeExpression | None = None # e.g. 1d4 rounds
    uses_per_period: int | None = None

# =====================
# AREA OF EFFECT
# =====================
@dataclass(kw_only=True)
class EffectArea:
    area_size: int                 # in meters or feet
    area_unit_system: UnitSystem   # metric or imperial
    area_shape: AreaEffectShape

# =====================
# DAMAGE OVER TIME
# =====================
@dataclass(kw_only=True)
class DamageOverTime:  
    damage_frequency: TimeExpression
    damages: list[Damage] = field(default_factory=list)
    occurrences: int | None = None # how many times the damage repeats
    # occurrences = None -> repeats continuously, indefinitely

# =====================
# TARGET
# =====================
@dataclass(kw_only=True)
class EffectTarget:
    target_type: TargetType  # creature, item, effect, area, anyone
    creature_type: CreatureType | None = None
    creature_subtype: CreatureSubtype | None = None
    target_description: str | None = None
    # requirements
    required_level: int | None = None   # maximum required HD level
    required_level_operator: RequirementOperator | None = None # greater than, less than

    required_ability_type: Ability | None = None # e.g. strength, dexterity
    required_ability_value: int | None = None    # e.g. intelligence 10
    required_ability_operator: RequirementOperator | None = None # greater than, less than

    target_alignment: list[Alignment] = field(default_factory=list)

# =====================
# EFFECT MODIFIER
# =====================
@dataclass(kw_only=True)
class EffectModifier:
    # Amount
    dice_number: int | None = None        # e.g. 2 (for 2d4)
    dice_type: DiceType | None = None     # e.g. d4
    modifier: int | None = None           # e.g. +1

    # Modified subject
    target: ModifierTarget # e.g. ability score, damage, to-hit roll

    # Target specification
    skill_to_apply: Skills | None = None
    armor_class_to_apply: ArmorClass | None = None
    ability_to_apply: Abilities | None = None # e.g. strength
    save_to_apply: Saves | None = None    # e.g. Fortitude

    # Modifier against
    against_type: ModifierConditionType | None = None # effect, creature, item
    against_description: str | None = None
    # e.g. petrification, disintegration, paralysis, sleep, poison

# =====================
# EFFECT GRANT
# =====================
@dataclass(kw_only=True)
class EffectGrant:
    """Represents content granted by an effect."""
    grant_type: GrantedType
    amount: Dice | int = 1
    usage: EffectUsage = field(default_factory=EffectUsage)
    description: str