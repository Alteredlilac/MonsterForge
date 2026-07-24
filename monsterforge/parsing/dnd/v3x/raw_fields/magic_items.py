"""
Raw field representations for D&D 3.x magic item entries.

This module defines magic items as they appear in D&D 3.x sources,
preserving their original format instead of converting them into
structured domain types.

It represents the intermediate raw_fields layer described in
PIPELINE_ARCHITECTURE.md: extracted data is normalized into stable
Python structures here, while type casting and semantic interpretation
are handled later during the structured_data conversion stage.

Magic item classes extend the base item structures defined in items.py,
ensuring a consistent data model across mundane, magic, and psionic
systems while keeping rule systems logically separated.

Empty category classes are intentionally preserved to simplify later
mapping stages and retain the original item classification.

Items with charges are represented using their maximum available charges,
as the current card-based game system does not model charge consumption.

Intelligent items, cursed items, and artifacts are represented as
wondrous items, with their specific behaviors preserved within the
item description.
"""
from dataclasses import dataclass
from .items import Item, Armor, Weapon

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
