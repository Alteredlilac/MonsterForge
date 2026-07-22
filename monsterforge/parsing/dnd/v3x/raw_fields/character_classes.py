"""
Raw field representations for D&D 3.x character class progression tables.

Unlike structured_data.dnd.v3x.character_classes (which represents a class
already interpreted into typed progression tiers — ProgressionRate,
SaveProgression, etc.), this module mirrors the class progression table
almost verbatim as it appears in the rulebook: one row per level, values 
still as source-formatted strings rather than cast numeric/enum/domain types.

This is the intermediate "raw fields" step described in
PIPELINE_ARCHITECTURE.md: it exists to decouple regex/HTML extraction from
interpretation, allow multiple sources to converge on the same shape
before any casting happens, and let simple classes skip semantic
classification entirely when no free-text content is present.

Kept out of scope intentionally: spells known (not needed by the
card-based game system), class skills, alignment restrictions, and
weapon/armor proficiency (not represented in the target card system).
"""
from dataclasses import dataclass, field

# =====================
# CHARACTER PRIVILEGE
# =====================
@dataclass(kw_only=True)
class CharacterPrivilege:
    """
    Represents an entry from the "Special" column of a character class
    progression table.
    """
    name: str
    description: str

# =====================
# SPELL SLOTS
# =====================
@dataclass(kw_only=True)
class SpellSlots:
    """
    Represents the spell slots columns of a character class progression table.

    Empty levels are represented as None rather than being removed, preserving
    the original table structure for later processing.
    """
    level_0: str | None = None
    level_1: str | None = None
    level_2: str | None = None
    level_3: str | None = None
    level_4: str | None = None
    level_5: str | None = None
    level_6: str | None = None
    level_7: str | None = None
    level_8: str | None = None
    level_9: str | None = None
    description: str | None = None
    # NOTE:
    # Description is used for special progression cases, such as
    # "+1 level of existing arcane spellcasting class".

# =====================
# EXTRA TABLE ENTRY
# =====================
@dataclass(kw_only=True)
class ExtraTableEntry:
    """Represents additional columns or entries in a progression table
    that cannot be mapped to a predefined field.
    """
    # NOTE:
    # Used for edge cases where a class grants non-standard bonuses or
    # abilities. Kept flexible due to the large variety of supplements.
    # Example from the core manuals:
    # Dragon Disciple bonus spells.
    name: str
    description: str

# =====================
# PROGRESSION ROW
# =====================
@dataclass(kw_only=True)
class CharacterProgressionRow:
    """
    Represents a single row from a character class progression table.
    """
    # Generic Data
    level: str
    base_attack_bonus: str
    fort_save: str
    ref_save: str
    will_save: str
    special: list[CharacterPrivilege] = field(default_factory=list)
    
    # Spellcasting Data
    spells_per_day: SpellSlots = field(default_factory=SpellSlots)
    # NOTE:
    # Spells Known are not included, as they are not needed
    # for the card-based game system.

    # Unarmed Combat Data
    flurry_of_blows_attack_bonus: str | None = None
    unarmed_damage: str | None = None
    # NOTE:
    # Only medium-size values are mapped, as the card-based game system
    # does not require size-based progression variants.
    armor_class_bonus: str | None = None
    unarmored_speed_bonus: str | None = None

    # Extra table entries for uncommon columns 
    extra_table_entries: list[ExtraTableEntry] = field(default_factory=list)
    
    # Psionics    
    maximum_power_level_known: str | None = None
    powers_known: str | None = None 
    # NOTE:
    # Powers Known is used only for classes with progression entries such as
    # "+1 level of existing manifesting class", where a maximum power level
    # value cannot be directly extracted.
    # It is kept as a fallback for these ambiguous cases.
    # NOTE:
    # Power Points per Day are not included, as they are not needed
    # for the card-based game system.


# =====================
# PROGRESSION TABLE
# =====================
@dataclass(kw_only=True)
class CharacterProgressionTable:
    """
    Represents a character class progression table extracted from a D&D 3.x source.
    """
    rows: list[CharacterProgressionRow]

# =====================
# CHARACTER CLASS
# =====================
@dataclass(kw_only=True)
class CharacterClass:
    """
    Represents a raw character class entry extracted
    from a D&D 3.x source.
    """
    name: str    
    hit_die: str
    # NOTE:
    # alignment, class skills, "Weapon and Armor Proficiency"
    # are intentionally not mapped, as they are not required
    # by the card-based game system.
    progression_table: CharacterProgressionTable
