"""
Structured data models for D&D 3.x spells and spellcasting.

Defines spell effects, spell level associations, casting data,
and creature spellcasting capabilities.
"""
from dataclasses import dataclass, field
from .enums import MagicType, MagicSchool, CastingTime, SpellRangeType, ConditionType, DamageType
from .dice_effects import Damage, Healing, TimeExpression
from .effect_mechanics import EffectRange, SavingThrow, EffectDuration, EffectTarget, EffectArea, EffectModifier, EffectGrant
from .defenses import DamageReduction, DamageResistance, Regeneration
from .creature_stats import Movement


# =====================
# helper
# =====================
@dataclass(kw_only=True)
class CastingTimeValue:
    amount: int = 1
    unit: CastingTime

@dataclass(kw_only=True)
class SpellLevel:
    caster_class: str
    level: int


# =====================
# Spells
# =====================
@dataclass(kw_only=True)
class Spell:
    name: str
    # data
    school: MagicSchool # 8 schools + universal
    # NOTE:
    # Spell subschools and descriptors are intentionally not mapped,
    # as they are not required by this domain model.
    level: list[SpellLevel] # required — must be provided
    # NOTE:
    # Spell components (verbal, somatic, material, etc.) are intentionally
    # not mapped, as they are not required by this domain model.

    casting_time: CastingTimeValue  # standard action, full-round action, free action

    spell_range: EffectRange | None = None # e.g. 30 meters

    range_type: SpellRangeType | None = None # touch, personal range, unlimited range

    damages: list[Damage] = field(default_factory=list)
    healing: list[Healing] = field(default_factory=list)
    # delayed effect?
    delayed_effect: bool = False
    delay_time: TimeExpression | None = None

    effect_description: str # brief description of the spell
    long_description: str   # extended description of the spell

    duration: EffectDuration = field(default_factory=EffectDuration)
    target: EffectTarget | None = None
    target_number: int | None = None
    area_effect: EffectArea | None = None

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

    grants: list[EffectGrant] = field(default_factory=list) # e.g. summons 2d4 wolves

    saving_throw: SavingThrow | None = None # None = no saving throw
    # NOTE:
    # Saving throw DC is calculated as 10 + spell level + the minimum
    # casting ability score.

    spell_resistance: bool = True # whether spell resistance applies

    # NOTE:
    # Material components and focus requirements are intentionally not mapped.

    applied_conditions: list[ConditionType] = field(default_factory=list)  # e.g. paralyzed, petrified


# =====================
# Spellcasting
# =====================

@dataclass(kw_only=True)
class Spellcaster:
    """Represents whether a creature is a spellcaster, and if so whether
    it casts arcane or divine spells."""
    # NOTE:
    # Spellcasting class is kept as a generic string to support classes from
    # different supplements and avoid limiting the model to a fixed set of values.
    spellcasting_class: str | None = None
    spellcasting_type: MagicType | None = None  # arcane, divine, etc.

@dataclass(kw_only=True)
class Spellcasting(Spellcaster):
    """Represents the spellcasting data of a creature."""
    caster_level: int | None = None
    spells_known: list[Spell] = field(default_factory=list)
    # NOTE:
    # Prepared spells and spell slots are intentionally not mapped — see
    # the note on character classes for the related scoping decision.

    @property
    def is_spellcaster(self) -> bool:
        """Indicates whether the creature has spellcasting ability."""
        return self.caster_level is not None and self.caster_level >= 1
    