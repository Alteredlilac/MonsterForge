"""
Represents attack-related data for D&D 3.x creatures.

This module contains models for attacks, damage components, and full
attack sequences. It is designed to capture the information contained
in creature stat blocks while keeping the data suitable for later
conversion and transformation.
"""
from dataclasses import dataclass, field
from .enums import HitDiceType, DamageType, UnitSystem, Ability
from .special_attacks import SpecialAttack

@dataclass(kw_only=True)
class Damage:
    dice_number : int | None = None       # numero di dadi
    dice_type: HitDiceType | None = None  # tipo di dado d6 , d8 eccetera
    damage_type: DamageType | None = None # tipo di danni (normali, fuoco)
    affected_ability: Ability | None = None
    damage_bonus: int | None = None       # bonus ai danni
    damage_bonus_type: DamageType | None = None # tipo di danni bonus (normali, fuoco)


@dataclass(kw_only=True)
class Attack:
    # Attack Data
    name: str
    description: str | None = None    
    attack_bonus: int | None = None    #tiro per colpire
    melee: bool = True      #mischia / distanza
    touch: bool = False     # attacco di contatto
    # Range
    attack_range: int | None = None   # Gittata in metri / portata
    range_unit_system: UnitSystem | None = None
    # Damages
    damages: list[Damage] = field(default_factory=list) # elenco dei danni dell'attacco
    # Critical Hit
    critical_threat_min: int | None = None  # minimum value of the critical threat range (e.g. 18 for 18-20)
    critical_multiplier: int | None = None  # critical multiplier (e.g. 2 for x2, 3 for x3)    
    # Effects
    effects: list[SpecialAttack] = field(default_factory=list)   
    
    
@dataclass(kw_only=True)
class FullAttack:
    attacks: list[Attack] = field(default_factory=list)
