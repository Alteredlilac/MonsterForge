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



@dataclass(kw_only=True)
class MoveCard(Card):
    # Classification
    move_type: MoveType        # Tipo  esempio("Fisico")
    category: MoveCategory     # Categoria esempio("Attacco")
    mode: MoveMode             # Modalita esempio("Attivo")
    effect: EffectType         # esempio("Danno", "Cura", "Bonus", "Malus")
    damage_type: DamageType  | None = None # Tipo di Danno esempio("Fuoco")
    effect_unit : AffectedAttribute | None = None # Quale valore influenza (esempio Vita, Armatura)
    effect_value: int | None = None  # Valore numerico dell'effetto (danno/cura)
    entity_effect: list[EntityEffect] = field(default_factory=list) # Effetto sull'entità (creatura, mossa, oggetto)
    cards_to_add: list[Card] = field(default_factory=list)  # Carte da aggiungere in caso di entity effect
    cards_to_remove: list[Card] = field(default_factory=list) # Carte da togliere in caso di entity effect
    target: Target             # Bersaglio esempio("Singolo")
    effect_radius: int | None = None  # Area in metri 
    move_range: MoveRange | None = None# Gittata
    range_value: int | None = None   # Gittata in metri 
    resource: Resource         # Risorsa esempio("Fiato")
    duration: Duration         # Durata esempio("Istantaneo")
    duration_unit: TimeUnit | None = None # Unità di misura della durata esempio("Round", "Minuti")
    duration_value: int | None = None # Valore numerico della duration_unit dell'effetto 
    usage: Usage               # Utilizzo esempio("Illimitato")
