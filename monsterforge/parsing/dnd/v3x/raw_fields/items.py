"""
Raw field representations for D&D 3.x item entries.

This module mirrors item entries as they appear in D&D 3.x sources,
preserving their original format instead of converting them into
structured domain types.

It represents the intermediate raw_fields layer described in
PIPELINE_ARCHITECTURE.md: extracted data is normalized into stable Python
structures here, while type casting and semantic interpretation happen
later during the structured_data conversion stage.

Empty category classes are intentionally kept to simplify later mapping
stages and preserve the original item classification.

Items with charges are represented using their maximum available charges,
as the current card-based game system does not model charge consumption.

Intelligent items, cursed items, and artifacts are represented as
wondrous items, with their specific behaviors preserved within the item
description.
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
    # additional_note serve per conservare note aggiuntive
    # presenti nella tabella e.g. 'A tower shield can instead grant you cover.'
    # 'Hand not free to cast spells.'

# =====================
# MAGIC ARMOR
# =====================
@dataclass(kw_only=True)
class MagicArmor(Armor):
    """
    Represents a magic armor or shield item entry extracted from a D&D 3.x source.
    """
    enhancement_bonus: str | None = None
    base_price_modifier: str | None = None
    # NOTE:
    # aura, caster level, required spells are not mapped
    # NOTE:
    # Magic armor with complex tables (e.g. 'Fortification')
    # are not fully mapped and are instead preserved in the description.

# =====================
# MAGIC WEAPON
# =====================
@dataclass(kw_only=True)
class MagicWeapon(Weapon):
    """
    Represents a magic weapon item entry extracted from a D&D 3.x source.
    """
    enhancement_bonus: str | None = None
    base_price_modifier: str | None = None
    # NOTE:
    # aura, caster level, required spells are not mapped
    # NOTE:
    # Magic weapon with complex tables (e.g. 'bane weapon', 'slaying arrow')
    # are not fully mapped and are instead preserved in the description.

# =====================
# HELPER
# =====================
@dataclass(kw_only=True)
class StoredSpell(Item):
    """
    Represents a spell stored or granted by an item entry.
    """
    spell_name: str
    added_description: str | None = None # e.g. "20" , "+2" 
    spell_charges: str | None = None # e.g. "(1 charge)"

# =====================
# POTION
# =====================
@dataclass(kw_only=True)
class Potion(Item):
    """
    Represents a potion or oil item entry extracted from a D&D 3.x source.
    """
    stored_spell: StoredSpell
    potion_type: str | None = None 
    # NOTE:
    # The source may classify entries as potion, oil, or potion or oil.
    # This field preserves the original item form designation.
    
# =====================
# RING
# =====================
@dataclass(kw_only=True)
class Ring(Item):
    """
    Represents a magic ring item entry extracted from a D&D 3.x source.
    """
    # NOTE:
    # aura, caster level, required spells are not mapped
    # NOTE:
    # rings with complex tables or descriptions (e.g. 'elemental command rings', 'ring of Shooting Stars')
    # are not fully mapped and are instead preserved in the description.
    pass

# =====================
# ROD
# =====================
@dataclass(kw_only=True)
class Rod(Item):
    """
    Represents a magic rod item entry extracted from a D&D 3.x source.
    """
    # NOTE:
    # aura, caster level, required spells are not mapped
    # NOTE:
    # rods with complex tables or descriptions (e.g. 'rod of wonder')
    # are not fully mapped and are instead preserved in the description.
    pass

# =====================
# SCROLL
# =====================
@dataclass(kw_only=True)
class Scroll(Item):
    """
    Represents a magic scroll item entry extracted from a D&D 3.x source.
    """
    stored_spell: StoredSpell
    is_arcane: bool | None = None
    is_divine: bool | None = None

# =====================
# MAGIC STAFF
# =====================
@dataclass(kw_only=True)
class MagicStaff(Item):
    """
    Represents a magic staff item entry extracted from a D&D 3.x source.
    """
    stored_spell: list[StoredSpell]
    additional_description: str | None = None
    # NOTE:
    # aura, caster level, required spells are not mapped

# =====================
# MAGIC WAND
# =====================
@dataclass(kw_only=True)
class MagicWand(Item):
    """
    Represents a magic wand item entry extracted from a D&D 3.x source.
    """
    stored_spell: StoredSpell

# =====================
# WONDROUS ITEM
# =====================
@dataclass(kw_only=True)
class WondrousItem(Item):
    """
    Represents a wondrous item entry extracted from a D&D 3.x source.
    """
    is_intelligent: bool = False
    is_cursed: bool = False
    is_artifact: bool = False
    # NOTE:
    # aura, caster level, required spells are not mapped
    # NOTE:
    # wondrous items with complex tables or descriptions (e.g. 'Apparatus of the Crab')
    # are not fully mapped and are instead preserved in the description
