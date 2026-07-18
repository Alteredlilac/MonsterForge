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
# Incantesimi
# =====================
@dataclass(kw_only=True)
class Spell:
    name: str 
    # data
    scuola: MagicSchool # 8 scuole +  universal
    # NOTE:
    # Spell subschools and descriptors are intentionally not mapped,
    # as they are not required by this domain model.
    level: list[SpellLevel] # va passata per forza
    # NOTE:
    # Spell components (verbal, somatic, material, etc.) are intentionally
    # not mapped, as they are not required by this domain model.

    casting_time: CastingTimeValue  #  standard action.  full-round action  free action 

    spell_range: EffectRange | None = None # 30 metri 

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
    turn_resistance: int | None = None # resistenza allo scacciare non morti 
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

    spell_resistance: bool = True # permette resistenza incantesimi? 

    # Material Component non mappato anche focus non mappato

    applied_conditions: list[ConditionType] = field(default_factory=list)  # condizioni applicate esempio paralizzato, pietrificato 
   

# =====================
# Spellcasting
# =====================

@dataclass(kw_only=True)
class Spellcaster:
    """Represents il fatto che una creatura sia una incatatore e se è arcano o divino"""
    # NOTE:
    # Spellcasting class is kept as a generic string to support classes from
    # different supplements and avoid limiting the model to a fixed set of values.
    spellcasting_class: str | None = None
    spellcasting_type: MagicType | None = None  # arcane, divine, etc.

@dataclass(kw_only=True)
class Spellcasting(Spellcaster):
    """Represents the spellcasting data of a creature."""
    caster_level: int | None = None  # livello incantatore
    spells_known: list[Spell] = field(default_factory=list)  # incantesimi conosciuti
    # incantesimi preparati non mappati
    # slot incantesimi non mappati vedi nota su classi personaggi

    @property
    def is_spellcaster(self) -> bool:
        """Indicates whether the creature has spellcasting ability."""
        return self.caster_level is not None and self.caster_level >= 1
    