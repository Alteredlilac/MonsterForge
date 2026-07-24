"""
Raw field representations for D&D 3.x psionic item entries.

This module mirrors psionic item entries as they appear in D&D 3.x sources,
preserving their original format instead of converting them into
structured domain types.

It represents the intermediate raw_fields layer described in
PIPELINE_ARCHITECTURE.md: extracted data is normalized into stable Python
structures here, while type casting and semantic interpretation happen
later during the structured_data conversion stage.

Psionic features not required by the current card-based game system,
such as power points and specific psionic activation rules, are intentionally
excluded or simplified during mapping.

Items with charges are represented using their maximum available charges,
as the current card-based game system does not model charge consumption.

Intelligent psionic items, cursed psionic items, and psionic artifacts
are represented as psionic universal items, with their specific behaviors
preserved within the item description.
"""
from dataclasses import dataclass
from .items import Item, Armor, Weapon

# =====================
# PSIONIC ARMOR
# =====================
@dataclass(kw_only=True)
class PsionicArmor(Armor):
    """
    Represents a psionic armor or shield item entry extracted from a D&D 3.x source.
    """
    enhancement_bonus: str | None = None
    base_price_modifier: str | None = None
    # NOTE:
    # aura, manifester level, required powers are not mapped
    # NOTE:
    # Psionic armor with complex tables or rule interactions
    # are not fully mapped and are instead preserved in the description.

# =====================
# PSIONIC WEAPON
# =====================
@dataclass(kw_only=True)
class PsionicWeapon(Weapon):
    """
    Represents a psionic weapon item entry extracted from a D&D 3.x source.
    """
    enhancement_bonus: str | None = None
    base_price_modifier: str | None = None
    # NOTE:
    # aura, manifester level, required powers are not mapped
    # NOTE:
    # Psionic weapon with complex tables (e.g. 'Psychic')
    # are not fully mapped and are instead preserved in the description.

# =====================
# COGNIZANCE CRYSTAL
# =====================
# NOTE:
# Cognizance crystals are intentionally excluded from the model, as they
# provide additional power points that are not used by the current
# card-based game system.

# =====================
# HELPER
# =====================
@dataclass(kw_only=True)
class StoredPower(Item):
    """
    Represents a psionic power stored or granted by an item entry.
    """
    power_name: str
    added_description: str | None = None # e.g. "20" , "+2" 
    power_charges: str | None = None # e.g. "(1 charge)"

# =====================
# DORJE
# =====================
@dataclass(kw_only=True)
class Dorje(Item):
    """
    Represents a dorje (psionic item) entry extracted from a D&D 3.x source.
    """
    stored_power: StoredPower

# =====================
# POWER STONE
# =====================
@dataclass(kw_only=True)
class PowerStone(Item):
    """
    Represents a psionic power stone item entry extracted from a D&D 3.x source.
    """
    stored_powers: list[StoredPower]
    manifester_class: str | None = None

# =====================
# PSICROWN
# =====================
@dataclass(kw_only=True)
class Psicrown(Item):
    """
    Represents a psicrown psionic item entry extracted from a D&D 3.x source.
    """
    stored_powers: list[StoredPower]
    additional_description: str | None = None
    # NOTE:
    # Psionic power points are not mapped, as they are not relevant for the
    # current card-based game system.
    # Psicrowns are represented using charges instead of power points, with
    # 50 charges as the default value.
    # NOTE:
    # aura, manifester level, required powers are not mapped

# =====================
# PSIONIC TATTOO
# =====================
@dataclass(kw_only=True)
class PsionicTattoo(Item):
    """
    Represents a psionic tattoo item entry extracted from a D&D 3.x source.
    """
    stored_power: StoredPower    
    
# =====================
# UNIVERSAL ITEM
# =====================
@dataclass(kw_only=True)
class PsionicUniversalItem(Item):
    """
    Represents a psionic universal item entry extracted from a D&D 3.x source.
    """
    is_intelligent: bool = False
    is_cursed: bool = False
    is_artifact: bool = False
    # NOTE:
    # aura, manifester level, required powers are not mapped
    # NOTE:
    # Psionic universal items with complex tables or descriptions
    # are not fully mapped and are instead preserved in the description.
