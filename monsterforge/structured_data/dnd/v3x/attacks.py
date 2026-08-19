"""
Represents attack-related data for D&D 3.x creatures.

This module contains models for attacks, damage components, and full
attack sequences. It is designed to capture the information contained
in creature stat blocks while keeping the data suitable for later
conversion and transformation.
"""
from dataclasses import dataclass, field
from .effect_mechanics import CriticalHit, EffectRange
from .special_attacks import SpecialAttack
from .dice_effects import Damage
from .enums import MoveType

# =====================
# ATTACK
# =====================
@dataclass(kw_only=True)
class Attack:
    # Attack Data
    move_type: MoveType
    name: str
    description: str | None = None    
    attack_bonus: int | None = None    # to-hit roll bonus
    melee: bool = True      # True = melee, False = ranged
    touch: bool = False     # touch attack
    # Range
    attack_range: EffectRange | None = None
    # Damages
    damages: list[Damage] = field(default_factory=list)
    # Critical Hit
    critical_hit: CriticalHit | None = None 
    # Effects
    effects: list[SpecialAttack] = field(default_factory=list)
    

# =====================
# FULL ATTACK
# =====================    
@dataclass(kw_only=True)
class FullAttack:
    attacks: list[Attack] = field(default_factory=list)
