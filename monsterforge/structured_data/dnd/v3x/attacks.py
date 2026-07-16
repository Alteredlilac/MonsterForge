"""
attacchi
"""
from enum import Enum
from dataclasses import dataclass, field

@dataclass(kw_only=True)
class Attack(str, Enum):
    ...
    
@dataclass(kw_only=True)
class FullAttack(str, Enum):
    # valutare se farla o se fare lista di attacchi -> creatures 
    list[Attack] = field(default_factory=list)
