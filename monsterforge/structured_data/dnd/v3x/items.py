"""
armi
armature
oggetti magici
simbionti
oggetti intelligenti
"""
from enum import Enum
from dataclasses import dataclass, field

@dataclass(kw_only=True)
class Item(str, Enum):
    ...