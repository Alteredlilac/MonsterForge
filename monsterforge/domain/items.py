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
    move: MoveCard   #mossa utilizzabile dall'oggetto
    usage: Usage # quante volte può essere utilizzata (illimitato, giornaliero, limitato, situazionale)
    usage_unit: TimeUnit | None = None # ogni quanto 
    usage_value: int | None = None  # valore di usage_unit

@dataclass(kw_only=True)
class ItemDamage:
    damage_value: int | None = None # dannni dell'oggeto 
    damage_type: DamageType | None = None  # tipo di danno

@dataclass(kw_only=True)
class ItemModifier:
    bonus_value: int | None = None # valore del bonus
    bonus_type: AffectedAttribute | None = None # tipo di bonus
    malus_value: int | None = None # valore del malus
    malus_type: AffectedAttribute | None = None # tipo di malus

@dataclass(kw_only=True)
class ItemRequirement:
    requirement_type: RequirementType #(oggetto, statistica, mossa, creatura)    
    required_card: uuid.UUID | None = None  # carta item o mossa o creatura
    required_attribute: AffectedAttribute | None = None # attributo richiesto
    minimum_attribute_value: int | None = None  # valore richiesto
    required_creature_type: CreatureType | None = None
    required_level: int | None = None

@dataclass(kw_only=True)
class ItemCard(Card):
    item_type: list[ItemType] = field(default_factory=list) # Tipo  esempio("WEAPON")
    item_size: Size     # taglia dell'oggetto
    price: int          # valore dell'oggetto
    # Item Usage
    granted_moves: list[ItemMove] = field(default_factory=list)
    #Item data
    damages: list[ItemDamage] = field(default_factory=list)
    item_range: int | None = None # portata dell'oggetto = gittata in metri
    is_melee: bool | None = None # utilizzabile in mischia? 
    # il critico non viene considerato ? 
    # munizioni non viene considerato ? o è tool? in quel caso requisito
    requirements: list[ItemRequirement] = field(default_factory=list) # requisiti di utilizzo
    consumable: bool = False  # monouso 
    charges: int | None = None # cariche od usi limitati
    # ItemModifier
    modifiers: list[ItemModifier] = field(default_factory=list)
   