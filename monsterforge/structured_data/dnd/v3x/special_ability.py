"""
Structured data model for D&D 3.x special abilities.

Defines the base representation for extraordinary, supernatural,
and spell-like abilities shared by special attacks and special qualities.
"""
from dataclasses import dataclass, field
from .enums import SpecialAbilityType
import uuid


@dataclass(kw_only=True)
class SpecialAbility:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    #Data
    name: str
    description: str | None = None
    special_ability_type: SpecialAbilityType  