"""
attacchi speciali

SpecialAttacks
"""
from enum import Enum
from dataclasses import dataclass, field

@dataclass(kw_only=True)
class SpecialAttack(str, Enum):
    ...