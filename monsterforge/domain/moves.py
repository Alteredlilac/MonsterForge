"""
Defines the domain models for moves.

This module contains the data structures used to represent move cards
within the game system. Move cards represent actions, abilities, and
techniques available to entities.

Each move card defines the information required to describe an action.

This module introduces the MoveCard data structure used to represent
actions within the game.
"""

from dataclasses import dataclass, field
from .cards import Card
from .enums import (
    MoveType,
    MoveCategory,
    MoveMode,
    EffectType,
    DamageType,
    AffectedAttribute,
    EntityEffect,
    Target,
    MoveRange,
    Resource,
    Duration,
    TimeUnit,
    Usage
    )


# MOVE EFFECT
@dataclass(kw_only=True)
class MoveEffect:
    """e.g. 2 fire, 4 Power"""
    damage_type: DamageType | None = None # e.g. "Fire"
    effect_unit : AffectedAttribute | None = None # which value it affects, e.g. Life, Armor
    effect_value: int | None = None  # numeric value of the effect (damage/healing)

# MOVE CARD
@dataclass(kw_only=True)
class MoveCard(Card):
    # Classification
    move_type: MoveType        # e.g. "Physical"
    category: MoveCategory     # e.g. "Attack"
    mode: MoveMode             # e.g. "Active"

    effect: EffectType         # e.g. "Damage", "Healing", "Bonus", "Malus"

    # NOTE:
    # Whether these three (move_effects, entity_effect, cards_to_add/remove)
    # should be aggregated into a single structure is an open question, not
    # yet resolved.
    move_effects: list[MoveEffect] = field(default_factory=list) # e.g. 5 physical damage, 2 fire

    entity_effect: list[EntityEffect] = field(default_factory=list) # effect on the entity itself (creature, move, item)
    cards_to_add: list[Card] = field(default_factory=list)  # cards to add, for an entity effect
    cards_to_remove: list[Card] = field(default_factory=list) # cards to remove, for an entity effect
    target: Target             # e.g. "Single"
    effect_radius: int | None = None  # in meters
    move_range: MoveRange | None = None
    range_value: int | None = None   # in meters
    resource: Resource         # e.g. "Stamina"
    resource_value: int = 1    # cost of using the move
    duration: Duration         # e.g. "Instant"
    duration_unit: TimeUnit | None = None # e.g. "Round", "Minutes"
    duration_value: int | None = None
    usage: Usage               # e.g. "Unlimited"
