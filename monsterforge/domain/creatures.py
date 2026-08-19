"""
Defines the domain models for creatures and player characters.

This module contains the data structures used to represent creature cards
within the game system. CreatureCard is the base model shared by all
creatures, while PlayerCard extends it with additional information for
player-controlled characters.
"""

from dataclasses import dataclass
from .enums import CreatureType,Size
from .cards import Card


@dataclass(kw_only=True)
class CreatureCard(Card):
    # Creature data
    level: int
    creature_type: CreatureType 
    creature_size: Size     
    # Life
    total_life: int
    current_life: int | None = None
    # Protection
    armor: int
    talisman: int
    # Skills
    athletics: int
    empathy: int
    perception: int
    stealth: int
    knowledge: int
    crafting: int
    # Resources
    stamina: int
    mana: int
    # Body
    attack: int
    defense: int
    speed: int
    # Spirit
    power: int
    ward: int
    flow: int
       
       


@dataclass(kw_only=True)
class PlayerCard(CreatureCard):
    player_name: str
