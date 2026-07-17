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
    EffectModifier
    )
from .defenses import DamageReduction, DamageResistance, Regeneration
from .enums import DamageType, GrantedType

# =====================
# SPECIAL QUALITIES
# =====================
@dataclass(kw_only=True)
class SpecialQuality(SpecialAbility):
    # data
    # Activation
    always_active: bool = True  # l'effetto è sempre attivo?
    requires_action: bool = False  # requires an action to be used?
    # raggio di azione
    effect_range: EffectRange | None = None 
    triggered_by_contact: bool = False   # attivato dal contatto
    # TS
    saving_throw: SavingThrow | None = None
    # danni 
    damages: list[Damage] = field(default_factory=list)
    # cura 
    healing: list[Healing] = field(default_factory=list)
    # delayed effect?
    delayed_effect: bool = False
    delay_time: TimeExpression | None = None
    # utilizzo situazionale(dopo 1 round di combattimento esempio)
    situational_usage: bool = False
    usage_condition: str | None = None
    #durata
    effect_duration: EffectDuration | None = None
    # Target
    target: EffectTarget | None = None # brasaglio dell'effetto
    
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
    grants: list[GrantedType] = field(default_factory=list) # creatura, oggetto, effetto 
