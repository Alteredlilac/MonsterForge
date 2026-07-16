"""
talenti 
Feat
"""
from enum import Enum
from dataclasses import dataclass, field

@dataclass(kw_only=True)
class Feat(str, Enum):
    ...