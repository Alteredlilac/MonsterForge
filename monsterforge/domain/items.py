"""
Defines the domain models for items.

This module contains the data structures used to represent item cards
within the game system. Item cards represent objects, equipment, and
possessions that can be associated with entities.

Each item card defines the information required to describe an item,
including its usage, effects, requirements, and modifiers.

This module introduces the ItemCard data structure used to represent
items within the game.
"""
# NOTE: unlike MoveCard (which represents a single atomic action), ItemCard
# composes multiple sub-effects (ItemMove, ItemDamage, ItemModifier...) because
# a single item can grant several simultaneous capabilities (e.g. an enchanted
# sword that deals damage, grants a bonus, and can parry).

from dataclasses import dataclass, field
from .cards import Card
from .enums import (
    ItemType,
    Size,
    Usage,
    TimeUnit,
    DamageType,
    AffectedAttribute,
    RequirementType,
    CreatureType
)
from .moves import MoveCard
import uuid

@dataclass(kw_only=True)
class ItemMove:
    move: MoveCard   # the move this item grants access to
    usage: Usage # how many times it can be used (unlimited, daily, limited, situational)
    usage_unit: TimeUnit | None = None # how often it recharges
    usage_value: int | None = None

@dataclass(kw_only=True)
class ItemDamage:
    damage_value: int | None = None
    damage_type: DamageType | None = None

@dataclass(kw_only=True)
class ItemModifier:
    bonus_value: int | None = None
    bonus_type: AffectedAttribute | None = None
    malus_value: int | None = None
    malus_type: AffectedAttribute | None = None

@dataclass(kw_only=True)
class ItemRequirement:
    requirement_type: RequirementType # item, stat, move, or creature
    required_card: uuid.UUID | None = None  # an item, move, or creature card
    required_attribute: AffectedAttribute | None = None
    minimum_attribute_value: int | None = None
    required_creature_type: CreatureType | None = None
    required_level: int | None = None

@dataclass(kw_only=True)
class ItemCard(Card):
    item_type: list[ItemType] = field(default_factory=list) # e.g. "WEAPON"
    item_size: Size
    price: int
    # Item Usage
    granted_moves: list[ItemMove] = field(default_factory=list)
    #Item data
    damages: list[ItemDamage] = field(default_factory=list)
    item_range: int | None = None # item's range, in meters
    is_melee: bool | None = None # usable in melee?
    # NOTE:
    # Two open modeling questions, not yet resolved: whether critical hit
    # should be considered for items, and whether ammunition should be
    # modeled at all — possibly as a tool, in which case it would become
    # a requirement rather than an item property.
    requirements: list[ItemRequirement] = field(default_factory=list)
    consumable: bool = False  # single-use
    charges: int | None = None # charges or limited uses
    # ItemModifier
    modifiers: list[ItemModifier] = field(default_factory=list)
   