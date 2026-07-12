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
    armor: int     # armatura
    talisman: int  # talismano
    # Skills
    athletics: int  # atletica
    empathy: int    # empatia
    perception: int # percezione
    stealth: int    # furtività
    knowledge: int    # cultura
    crafting: int   # artigianato
    # Resources
    stamina: int  # fiato
    mana: int    # magia
    # Body
    attack: int    # attacco
    defense: int   # difesa
    speed: int     # velocità
    # Spirit
    power: int     # potere
    ward: int      # tangenza
    flow: int      # spin
       
       


@dataclass(kw_only=True)
class PlayerCard(CreatureCard):
    player_name: str
