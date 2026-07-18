"""
armi
armature
oggetti magici
simbionti
oggetti intelligenti

- Oggetti
- costo
- attacco
- difesa
- magico 
- psionico
- bonus
- poteri / incantesimi 

"""
from enum import Enum
from dataclasses import dataclass, field

@dataclass(kw_only=True)
class Item(str, Enum):
    ...