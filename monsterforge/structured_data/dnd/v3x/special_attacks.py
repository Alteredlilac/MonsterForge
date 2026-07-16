"""
Structured data model for D&D 3.x special attacks.

Defines attack-based special abilities with damage, saving throws,
duration, usage, area effects, and damage over time representations.
"""
# NOTE:
# Spell-based attacks are represented through spell models instead
# of special attacks.

from dataclasses import dataclass, field
from .enums import (
    UnitSystem,
    SavingThrowType,
    Usage,
    Duration,
    AreaEffectShape,
    SavingThrowEffect     
    )
from .dice_effects import Damage, TimeExpression
from .special_ability import SpecialAbility

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
    attack_range: int | None = None   # Gittata in metri / portata
    range_unit_system: UnitSystem | None = None

    # Damages
    damages: list[Damage] = field(default_factory=list) # elenco dei danni dell'attacco
    # Critical Hit
    critical_threat_min: int | None = None  # minimum value of the critical threat range (e.g. 18 for 18-20)
    critical_multiplier: int | None = None  # critical multiplier (e.g. 2 for x2, 3 for x3)    
    
    # Saving Throw -> tiro salvezza
    saving_throw_type: SavingThrowType | None = None 
    saving_throw_value: int | None = None # valore del tiro salvezza (es. CD 18)
    saving_throw_effect: SavingThrowEffect | None = None
    
    #durata
    duration: Duration = Duration.INSTANT # istantaneo di default 
    duration_time: TimeExpression | None = None

    #utilizzi
    usage: Usage = Usage.UNLIMITED  # Utilizzo esempio("Illimitato", giornaliero, limitato, situazione)
    requires_recharge: bool = False
    recharge_time: TimeExpression | None = None
    uses_per_period: int | None = None # numero di utilizzi
    
    # Area of Effect
    area_size: int | None = None                 # valore della misura dell'area (metri o piedi)
    area_unit_system: UnitSystem | None = None   # sistema di misura (metrico o imperiale)
    area_shape: AreaEffectShape | None = None    # forma dell'area di effetto

    # Damage over Time
    damage_over_time: bool = False               # infligge danni prolungati?
    damage_frequency: TimeExpression | None = None
    damage_over_time_damages: list[Damage] = field(default_factory=list)
