"""
Defines the domain model for cards.

This module contains the base data structure shared by all card types
within the game system. Cards represent the individual components that
can be combined to define complete game entities.

The Card class provides the common attributes shared by all cards,
while specialized card types extend it with their own specific data.

This module introduces the Card data structure used as the foundation
for all card models within the game.
"""

from dataclasses import dataclass, field
import uuid

@dataclass(kw_only=True)
class Card:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Description
    name: str
    description: str
    # Artwork
    image_uri: str | None = None # card artwork
