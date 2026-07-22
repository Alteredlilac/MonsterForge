"""
Raw field representations for D&D 3.x companion progression tables.

This module mirrors companion entries and progression tables as they appear
in D&D 3.x sources, keeping values in their source format rather than
converting them into structured domain types.

It represents the intermediate raw_fields layer described in
PIPELINE_ARCHITECTURE.md: extracted data is normalized into stable Python
structures here, while type casting and semantic interpretation happen
later during the structured_data conversion stage.

Companion data is intentionally modeled separately from creature data, as
companions such as familiars, animal companions, special mounts, and
psicrystals have progression rules tied to an owner's level rather than
independent creature stat blocks.

Only fields relevant to the current card-based game system are represented.
Additional rulebook data may be omitted when it describes progression rules
or mechanics that are not required by the target system.
"""
from dataclasses import dataclass, field

# =====================
# COMPANION PRIVILEGE
# =====================
@dataclass(kw_only=True)
class CompanionPrivilege:
    """
    Represents an entry from the "Special" column of a companion
    progression table.
    """
    name: str
    description: str

# =====================
# EXTRA TABLE ENTRY
# =====================
@dataclass(kw_only=True)
class ExtraTableEntry:
    """
    Represents an additional table entry that cannot be mapped
    to a predefined field.
    """
    # NOTE:
    # Each companion type may have different table columns that cannot be
    # predefined in a generic model.
    name: str
    description: str

# =====================
# PROGRESSION ROW
# =====================
@dataclass(kw_only=True)
class CompanionProgressionRow:
    """
    Represents a single row from a companion progression table.
    """
    # Generic Data
    owner_level: str 
    # Extra table entries for uncommon columns
    extra_table_entries: list[ExtraTableEntry] = field(default_factory=list) 

    special: list[CompanionPrivilege] = field(default_factory=list)
     
# =====================
# PROGRESSION TABLE
# =====================
@dataclass(kw_only=True)
class CompanionProgressionTable:
    """
    Represents a companion progression table extracted from a D&D 3.x source.
    """
    rows: list[CompanionProgressionRow]

# =====================
# COMPANION
# =====================
@dataclass(kw_only=True)
class Companion:
    """
    Represents a companion entry extracted from a D&D 3.x source.

    Companions are entities whose progression may depend on the level
    of the associated character, such as familiars, animal companions,
    special mounts, or psicrystals.
    """
    companion_type: str # esempio famiglio, psicocristallo
    description: str | None = None

    # Basics
    hit_dice: str | None = None
    hit_points: str | None = None
    attacks: str | None = None
    saving_throws: str | None = None
    abilities: str | None = None
    skills: str | None = None
    # NOTE:
    # These fields contain progression descriptions rather than resolved values.
    # They are kept as strings because companion rules may depend on the owner
    # or other contextual conditions.

    # Special Abilities
    progression_table: CompanionProgressionTable
