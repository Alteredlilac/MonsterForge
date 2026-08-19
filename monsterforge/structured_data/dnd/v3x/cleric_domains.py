"""
Structured data models for D&D 3.x cleric domains.

Defines cleric domain data, including granted powers and domain spells.
"""

from dataclasses import dataclass, field
from .special_attacks import SpecialAttack
from .special_qualities import SpecialQuality
from .feats import Feat
from .attacks import Attack, FullAttack
from .items import Item
from .psionic_powers import Power
from .spells import Spell
from .creatures import CreatureModifier
from .companions import Companion
import uuid


# =====================
# CLERIC DOMAINS
# =====================
GrantedPower = (
    Attack | FullAttack | SpecialAttack | SpecialQuality | Feat | Companion |
    Item | Power | Spell | CreatureModifier
)
# NOTE:
# A granted power can grant heterogeneous content (attacks, feats, items, etc.),
# so a broad union type is used.

@dataclass(kw_only=True)
class ClericDomain:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str   # e.g. Fire Domain
    description: str | None = None
    
    # NOTE:
    # Associated deities are not mapped, as they are lore-specific
    # and not required by this domain model.
    granted_power: GrantedPower | None = None
    domain_spells: list[Spell] = field(default_factory=list)
