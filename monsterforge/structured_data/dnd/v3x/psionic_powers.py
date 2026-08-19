"""
Structured data models for D&D 3.x psionic powers and manifestation.

Defines psionic power effects, power level associations, manifestation
data, and creature psionic capabilities.
"""
from dataclasses import dataclass, field
from .enums import MagicType, PsionicDiscipline, CastingTime, SpellRangeType, ConditionType, DamageType
from .dice_effects import Damage, Healing, TimeExpression
from .effect_mechanics import EffectRange, SavingThrow, EffectDuration, EffectTarget, EffectArea, EffectModifier, EffectGrant
from .defenses import DamageReduction, DamageResistance, Regeneration
from .creature_stats import Movement


# =====================
# helper
# =====================
@dataclass(kw_only=True)
class ManifestingTimeValue:
    amount: int = 1
    unit: CastingTime

@dataclass(kw_only=True)
class PowerLevel:
    manifester_class: str
    level: int


# =====================
# Psionic Powers
# =====================
@dataclass(kw_only=True)
class Power:
    name: str
    # data
    discipline: PsionicDiscipline # 6 disciplines (e.g. telepathy, psychometabolism)
    # NOTE:
    # Power Subdisciplines are intentionally not mapped,
    # as they are not required by this domain model.
    level: list[PowerLevel] # required — must be provided
    # NOTE:
    # Power display (auditory, material, mental etc.) are intentionally
    # not mapped, as they are not required by this domain model.

    manifesting_time: ManifestingTimeValue  # standard action, full-round action, free action

    power_range: EffectRange | None = None # e.g. 30 meters

    range_type: SpellRangeType | None = None # touch, personal range, unlimited range

    damages: list[Damage] = field(default_factory=list)
    healing: list[Healing] = field(default_factory=list)
    # delayed effect?
    delayed_effect: bool = False
    delay_time: TimeExpression | None = None

    effect_description: str # brief description of the power
    long_description: str   # extended description of the power

    duration: EffectDuration = field(default_factory=EffectDuration)
    target: EffectTarget | None = None
    target_number: int | None = None
    area_effect: EffectArea | None = None

    # resistances and immunities
    damage_reduction: DamageReduction | None = None
    damage_resistances: list[DamageResistance] = field(default_factory=list)
    turn_resistance: int | None = None # resistance to turning undead, kept for symmetry with Spell

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
    # Saving throw DC is calculated as 10 + power level + the minimum
    # manifesting ability score.

    power_resistance: bool = True # whether power resistance applies

    power_points: int # power points required to manifest the power
    # NOTE:
    # Psionic power augmentation is intentionally not mapped,
    # as additional power point costs and scaling effects are not
    # required by this domain model.

    # NOTE:
    # XP costs, material components, and focus requirements are intentionally
    # not mapped, as they are not required by this domain model.

    applied_conditions: list[ConditionType] = field(default_factory=list)  # e.g. paralyzed, petrified


# =====================
# Psionic Manifester
# =====================
@dataclass(kw_only=True)
class Manifester:
    """Represents whether a creature has psionic manifestation capability."""
    # NOTE:
    # manifester_class is kept as a generic string to support classes from
    # different supplements and avoid limiting the model to a fixed set of values.
    manifester_class: str | None = None

@dataclass(kw_only=True)
class Psionics(Manifester):
    """Represents the psionic manifestation data of a creature."""
    manifester_level: int | None = None
    powers_known: list[Power] = field(default_factory=list)
    power_points: int | None = None

    @property
    def is_psionic(self) -> bool:
        """Indicates whether the creature has psionic manifestation ability."""
        return self.manifester_level is not None and self.manifester_level >= 1
        