"""
Contiene le statistiche delle creature
"""
from dataclasses import dataclass, field
from .enums import (
    DiceType,
    UnitSystem, 
    MovementMode,  
    FlyManeuverability,
    )

# =====================
# Dadi vita
# =====================
@dataclass(kw_only=True)
class HitDice:
    num_hit_dice: int        # numero di dadi vita
    hit_dice_type: DiceType  # tipo di dado vita

# =====================
# Movimento
# =====================
@dataclass(kw_only=True)
class Movement:                # metodo di movimento
    movement_speed: int          # distanza percorsa
    unit_system: UnitSystem      # sistema di misura metrico o imperiale
    movement_type: MovementMode  # tipo di movimento
    maneuverability: FlyManeuverability | None = None # manovrabilità in volo

# =====================
# Classe armatura
# =====================
@dataclass(kw_only=True)
class ArmorClass:
    # Standard AC
    armor_class: int

    size_modifier: int = 0
    dexterity_modifier: int = 0
    natural_armor_bonus: int = 0
    armor_bonus: int = 0
    shield_bonus: int = 0
    deflection_bonus: int = 0
    miscellaneous_bonus: dict[str, int] = field(default_factory=dict)

    # Flat-footed AC 
    flat_footed_ac: int  

    # Touch AC
    touch_ac: int

# =====================
# spazio e portata della creatura
# =====================
@dataclass(kw_only=True)         
class Space:       # spazio
    space: int
    unit_system: UnitSystem      # sistema di misura metrico o imperiale


@dataclass(kw_only=True)
class Reach:       # portata
    reach: int
    unit_system: UnitSystem      # sistema di misura metrico o imperiale

# =====================
# CARATTERISTICHE
# =====================
@dataclass(kw_only=True)
class Abilities:       # oggetto che rappresenta le caratteristiche di una creatura
    # NOTE:
    # Some ability scores may be undefined ("-") in D&D 3.5 stat blocks.
    # Strength may be absent ("-") for creatures without a physical body (e.g. spectres). 
    # Dexterity may be absent ("-") for immobile creatures (e.g. certain plants or fungi).
    # Constitution is omitted for creatures without a living body (undead,
    # constructs), while Intelligence is omitted for mindless creatures.
    strength: int | None    # forza
    dexterity: int | None     # destrezza
    constitution: int | None # costituzione
    intelligence: int | None  # intelligenza
    wisdom: int        # saggezza
    charisma: int      # carisma

# =====================
# TIRI SALVEZZA
# =====================
@dataclass(kw_only=True)
class Saves:       # oggetto che rappresenta i tiri salvezza di una creatura
    fortitude_save: int  # tempra
    reflex_save: int     # riflessi
    will_save: int       # volontà
    