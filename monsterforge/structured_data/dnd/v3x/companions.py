"""
Domain models for D&D 3.x companions and their level-based progression.

This module defines companions (e.g., familiars, animal companions,
special mounts) and the privileges they gain over time.
"""

from dataclasses import dataclass, field
from .enums import CompanionPrivilegeType
from .special_attacks import SpecialAttack
from .special_qualities import SpecialQuality
from .feats import Feat
from .attacks import Attack, FullAttack
from .items import Item
from .psionic_powers import Power
from .spells import Spell
from .creatures import CreatureModifier, Creature
import uuid


# =====================
# PRIVILEGES
# =====================
GrantedContent = (
    Attack | FullAttack | SpecialAttack | SpecialQuality | Feat |
    Item | Power | Spell | CreatureModifier
)
# NOTE:
# A privilege can grant heterogeneous content (attacks, feats, items, etc.),
# so a broad union type is used.
@dataclass(kw_only=True)
class CreaturePrivilege:
    """
    Represents a single privilege granted to a companion.
    """
    name : str
    granted_at_level: int 
    description: str
    privilege_type: CompanionPrivilegeType
    granted_privilege: GrantedContent


# =====================
# COMPANION
# =====================
@dataclass(kw_only=True)
class Companion:
    """
    Represents a D&D 3.x companion and its level-based progression
    (e.g., familiar, special mount, animal companion).
    """
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str   # esempio famiglio 
    description: str | None = None
    base_creature: Creature
    total_levels: int # numero di livelli totali della classe (esempio 5 , 10, 20)
    privileges: dict[int, list[CreaturePrivilege]] = field(default_factory=dict) # key = level, value = list of privileges granted at that level
