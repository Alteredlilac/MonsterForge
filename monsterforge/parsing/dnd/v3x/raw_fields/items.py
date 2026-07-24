"""
Raw field representations for D&D 3.x mundane item entries.

This module defines the base item structures and mundane equipment
as they appear in D&D 3.x sources, preserving their original format
instead of converting them into structured domain types.

It represents the intermediate raw_fields layer described in
PIPELINE_ARCHITECTURE.md: extracted data is normalized into stable
Python structures here, while type casting and semantic interpretation
are handled later during the structured_data conversion stage.

The classes defined in this module serve as the shared foundation for
all item types, including magic and psionic items, which are implemented
in dedicated modules (magic_items.py and psionic_items.py).

Only mundane item data is defined directly in this module. System-specific
items (e.g. magic or psionic) extend these base structures in their
respective modules to maintain separation between rule systems while
preserving a consistent data model.
"""
from dataclasses import dataclass, field

# =====================
# ITEM
# =====================
@dataclass(kw_only=True)
class Item:
    """
    Represents a generic item entry extracted from a D&D 3.x source.
    """
    name: str | None = None 
    # NOTE:
    # Some source entries do not provide an explicit item name
    # (e.g. potion or scroll categories).
    description: str | None = None
    price: str | None = None


# =====================
# WEAPON
# =====================
@dataclass(kw_only=True)
class Weapon(Item):
    """
    Represents a weapon item entry extracted from a D&D 3.x source.
    """
    damage: str | None = None
    damage_type: list[str]  = field(default_factory=list)
    # NOTE:
    # Only medium-size damage is mapped, as required by the
    # current card-based game system.

    # Critical 	
    critical: str | None = None
    # Range Increment
    range_increment: str | None = None
    # NOTE:
    # Weight is not mapped, as it is not relevant for the
    # current card-based game system.

    # Additional description
    nonlethal_damage: bool = False
    reach_weapon: bool = False
    double_weapon: bool = False
    
# =====================
# ARMOR
# =====================
@dataclass(kw_only=True)
class Armor(Item):
    """
    Represents an armor or shield item entry extracted from a D&D 3.x source.
    """
    armor_bonus: str | None = None
    maximum_dex_bonus: str | None = None
    armor_check_penalty: str | None = None
    arcane_spell_failure_chance: str | None = None
    max_speed : str | None = None    
    # NOTE:
    # Only medium-size movement speed values (30 ft. / 9m)
    # are mapped. Small-size variants (20 ft. / 6m) are not included.

    # NOTE:
    # Weight is not mapped, as it is not relevant for the
    # current card-based game system.

    additional_notes: str | None = None
    # NOTE:
    # additional_notes is used to preserve extra notes
    # presenti nella tabella e.g. 'A tower shield can instead grant you cover.'
    # 'Hand not free to cast spells.'
