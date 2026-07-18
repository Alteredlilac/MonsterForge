"""
Structured data model for D&D 3.x special attacks.

Defines attack-based special abilities with damage, saving throws,
duration, usage, area effects, and damage over time representations.
"""
# NOTE:
# Spell-based attacks are represented through spell models instead
# of special attacks.

from dataclasses import dataclass, field
from .dice_effects import Damage
from .special_ability import SpecialAbility
from .effect_mechanics import (
    EffectRange,
    CriticalHit,
    SavingThrow,
    EffectDuration,
    EffectUsage,
    EffectArea,
    DamageOverTime,
    EffectTarget
    )
from .enums import ConditionType

# =====================
# SPECIAL ATTACK
# =====================
@dataclass(kw_only=True)
class SpecialAttack(SpecialAbility):
    # Attack properties
    # NOTE:
    # Boolean fields are used instead of an enum list to improve
    # model querying and make property checks more straightforward.
    melee: bool = True        # melee or ranged attack
    touch: bool = False       # touch attack
    ray: bool = False         # ray attack
    gaze: bool = False        # gaze attack
    area_effect: bool = False # area attack (affects an area)

    # Range
    attack_range: EffectRange | None = None   # Gittata / portata 
    # Damages
    damages: list[Damage] = field(default_factory=list) # elenco dei danni dell'attacco
    # Critical Hit
    critical_hit: CriticalHit | None = None     
    # Saving Throw -> tiro salvezza
    saving_throw: SavingThrow | None = None     
    # Duration 
    duration: EffectDuration = field(default_factory=EffectDuration)
    #utilizzi
    usage: EffectUsage = field(default_factory=EffectUsage)    
    # Area of Effect
    area_of_effect: EffectArea | None = None 
    # Damage over Time
    damage_over_time: DamageOverTime | None = None 
    # Target
    target: EffectTarget  # brasaglio dell'effetto
    applied_conditions: list[ConditionType] = field(default_factory=list) # condizioni applicate esempio paralizzato, pietrificato  
    
