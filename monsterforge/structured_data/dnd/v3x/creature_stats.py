"""
Creature stat components: hit dice, movement, armor class, space/reach,
ability scores, and saving throws.
"""
from dataclasses import dataclass, field
from .enums import (
    DiceType,
    UnitSystem,
    MovementMode,
    FlyManeuverability,
    )

# =====================
# HIT DICE
# =====================
@dataclass(kw_only=True)
class HitDice:
    num_hit_dice: int
    hit_dice_type: DiceType

# =====================
# MOVEMENT
# =====================
@dataclass(kw_only=True)
class Movement:
    movement_speed: int
    unit_system: UnitSystem      # metric or imperial
    movement_type: MovementMode
    maneuverability: FlyManeuverability | None = None

# =====================
# ARMOR CLASS
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
# CREATURE SPACE AND REACH
# =====================
@dataclass(kw_only=True)
class Space:
    space: int
    unit_system: UnitSystem      # metric or imperial


@dataclass(kw_only=True)
class Reach:
    reach: int
    unit_system: UnitSystem      # metric or imperial

# =====================
# ABILITIES
# =====================
@dataclass(kw_only=True)
class Abilities:
    # NOTE:
    # Some ability scores may be undefined ("-") in D&D 3.5 stat blocks.
    # Strength may be absent ("-") for creatures without a physical body (e.g. spectres).
    # Dexterity may be absent ("-") for immobile creatures (e.g. certain plants or fungi).
    # Constitution is omitted for creatures without a living body (undead,
    # constructs), while Intelligence is omitted for mindless creatures.
    # Wisdom and Charisma are intentionally allowed to be undefined, as the
    # Abilities model is shared across multiple modules and must support
    # contexts beyond creature stat blocks.
    strength: int | None = None
    dexterity: int | None = None
    constitution: int | None = None
    intelligence: int | None = None
    wisdom: int | None = None
    charisma: int | None = None

# =====================
# SAVING THROWS
# =====================
@dataclass(kw_only=True)
class Saves:
    fortitude_save: int
    reflex_save: int
    will_save: int
