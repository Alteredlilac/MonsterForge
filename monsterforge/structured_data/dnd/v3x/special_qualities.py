"""
Structured data model for D&D 3.x special qualities.

Defines active and passive creature abilities that are not
represented as attacks or spells, including defenses, resistances,
movement abilities, senses, communication, and granted
effects.
"""
# NOTE:
# Spell-based abilities are represented through spell models
# rather than special qualities.
# Magical and psionic powers that are inherent creature properties
# are stored as creature attributes instead of special qualities.
# Spell resistance and power resistance are also modeled separately
# as creature characteristics, not as special qualities.

from dataclasses import dataclass, field
from .dice_effects import Damage, Healing, TimeExpression
from .special_ability import SpecialAbility
from .creature_stats import Movement
from .effect_mechanics import (
    EffectRange,
    SavingThrow,
    EffectDuration,
    EffectTarget,
    EffectModifier,
    EffectGrant
    )
from .defenses import DamageReduction, DamageResistance, Regeneration
from .enums import DamageType, ConditionType

# =====================
# SPECIAL QUALITIES
# =====================
@dataclass(kw_only=True)
class SpecialQuality(SpecialAbility):
    # data
    # Activation
    always_active: bool = True  # whether the effect is always active
    requires_action: bool = False  # requires an action to be used?
    effect_range: EffectRange | None = None
    triggered_by_contact: bool = False
    saving_throw: SavingThrow | None = None
    damages: list[Damage] = field(default_factory=list)
    healing: list[Healing] = field(default_factory=list)
    # delayed effect?
    delayed_effect: bool = False
    delay_time: TimeExpression | None = None
    situational_usage: bool = False # e.g. only after 1 round of combat
    usage_condition: str | None = None
    effect_duration: EffectDuration | None = None
    # Target
    target: EffectTarget | None = None

    applied_conditions: list[ConditionType] = field(default_factory=list) # e.g. paralyzed, petrified

    # resistances and immunities
    damage_reduction: DamageReduction | None = None
    damage_resistances: list[DamageResistance] = field(default_factory=list)
    turn_resistance: int | None = None # resistance to turning undead

    # NOTE:
    # Left as list[str] for now rather than an enum — the set of possible
    # immunities is too large/limiting to enumerate cleanly.
    immunities: list[str] = field(default_factory=list)

    vulnerabilities: list[DamageType] = field(default_factory=list)

    # bonus / malus
    modifiers: list[EffectModifier] = field(default_factory=list)

    perception: str | None = None # e.g. darkvision
    communication: str | None = None # e.g. telepathy

    granted_movement: list[Movement] = field(default_factory=list) # e.g. granted flight

    regeneration: Regeneration | None = None # covers both fast healing and regeneration

    grants: list[EffectGrant] = field(default_factory=list) # creature, item, or effect
