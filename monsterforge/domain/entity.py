"""
Defines the domain model for game entities.

An entity represents a complete game unit composed of multiple cards.
It represents any playable or interactable unit in the game
(e.g. monsters or player characters).

Instead of being modeled as a single card, each entity is a collection of:

- one or more creature cards defining its base characteristics;
- move cards representing available actions;
- item cards representing equipment and possessions.

This module introduces the Entity data structure, which acts as a
container for all cards that define a single in-game actor.
"""

from dataclasses import dataclass, field
from .creatures import CreatureCard
from .items import ItemCard
from .moves import MoveCard
import uuid



@dataclass(kw_only=True)
class Entity:
    # Internal data
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Cards
    # Multiple creature cards support shapeshifting/metamorphosis abilities.
    # Convention: index 0 is always the base/default form.
    creature_cards: list[CreatureCard] = field(default_factory=list)  
    move_cards: list[MoveCard] = field(default_factory=list)
    item_cards: list[ItemCard] = field(default_factory=list)
    # Description  
    entity_description: str | None = None

    @property
    def base_form(self):    # indice 0 = forma base
        return self.creature_cards[0]
