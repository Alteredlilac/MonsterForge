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
# Poteri Psionici
# =====================
@dataclass(kw_only=True)
class Power:
    name: str 
    # data
    discipline: PsionicDiscipline # 6 discipline (telepatia, psicometabolismo)
    # NOTE:
    # Power Subdisciplines are intentionally not mapped,
    # as they are not required by this domain model.
    level: list[PowerLevel] # va passata per forza
    # NOTE:
    # Power display (auditory, material, mental etc.) are intentionally
    # not mapped, as they are not required by this domain model.

    manifesting_time: ManifestingTimeValue  #  standard action.  full-round action  free action 

    power_range: EffectRange | None = None # 30 metri 

    range_type: SpellRangeType | None = None # contatto, raggio personale, raggio illimitato
    
    # danni 
    damages: list[Damage] = field(default_factory=list)
    # cura 
    healing: list[Healing] = field(default_factory=list)
    # delayed effect?
    delayed_effect: bool = False
    delay_time: TimeExpression | None = None

    # descrizione
    effect_description: str # breve descizione dell'incantesimo
    long_description: str   # descrizione estesa dell'incantesimo

    duration: EffectDuration = field(default_factory=EffectDuration) 
    target: EffectTarget | None = None # brasaglio dell'effetto
    target_number: int | None = None  # numero di bersagli
    area_effect: EffectArea | None = None # area di effetto

    # resistenze e immunità
    # riduzione del danno
    damage_reduction: DamageReduction | None = None
    # resistenze 
    damage_resistances: list[DamageResistance] = field(default_factory=list) # elenco delle resistenze
    # resistenza scacciare
    turn_resistance: int | None = None # resistenza allo scacciare non morti , mantenuto per simmetria con Spell

    # immunità
    immunities: list[str] = field(default_factory=list) # per ora lasciato str per scelta enum troppo lungo / limitante
    
    # vulnerabilità 
    vulnerabilities: list[DamageType] = field(default_factory=list)
    
    # bonus / malus
    modifiers: list[EffectModifier] = field(default_factory=list)

    # percezioni 
    perception: str | None = None # descrizione della percezione (scurovisione)
    #  comunicazione
    communication: str | None = None # descrizione (Telepatia)
    
    # metodo di movimento (volare) 
    granted_movement: list[Movement] = field(default_factory=list) 

    # guarigione rapida / rigenerazione
    regeneration: Regeneration | None = None

    # guadagna carte?
    grants: list[EffectGrant] = field(default_factory=list) # esempio evoca 2d4 lupi 

    saving_throw: SavingThrow | None = None # None = nessun tiro salvezza
    # si calcola con 10+liv+ caratteristica minima di lancio

    power_resistance: bool = True # permette resistenza ai poteri? 

    power_points: int # i punti poteri necessari a lanciare il potere
    # NOTE:
    # Psionic power augmentation is intentionally not mapped,
    # as additional power point costs and scaling effects are not
    # required by this domain model.

    # NOTE:
    # XP costs, material components, and focus requirements are intentionally
    # not mapped, as they are not required by this domain model.

    applied_conditions: list[ConditionType] = field(default_factory=list)  # condizioni applicate esempio paralizzato, pietrificato 
   

# =====================
# Incantatore Psionico
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
    manifester_level: int | None = None # livello di manifestazione
    powers_known: list[Power] = field(default_factory=list) # poteri psionici
    power_points: int | None = None  # punti potere

    @property
    def is_psionic(self) -> bool:
        """Indicates whether the creature has psionic manifestation ability."""
        return self.manifester_level is not None and self.manifester_level >= 1
        