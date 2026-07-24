"""
Tests for raw companion progression models.

Covers:
- Basic dataclass construction
- Nested structures (rows → table → companion)
- Default list values
- Raw string preservation (no interpretation)
"""

from monsterforge.parsing.dnd.v3x.raw_fields.companions import (
    CompanionPrivilege,
    ExtraTableEntry,
    CompanionProgressionRow,
    CompanionProgressionTable,
    Companion,
)


# =====================
# BASIC STRUCTURES
# =====================

def test_companion_privilege_creation():
    privilege = CompanionPrivilege(
        name="Link",
        description="Share spells with master"
    )

    assert privilege.name == "Link"


def test_extra_table_entry_creation():
    entry = ExtraTableEntry(
        name="Natural Armor",
        description="+2 bonus"
    )

    assert entry.description == "+2 bonus"


# =====================
# PROGRESSION ROW
# =====================

def test_progression_row_defaults():
    row = CompanionProgressionRow(
        owner_level="1–2"
    )

    # default lists must be empty and not shared
    assert row.special == []
    assert row.extra_table_entries == []


def test_progression_row_with_nested_data():
    privilege = CompanionPrivilege(
        name="Evasion",
        description="No damage on successful reflex save"
    )

    extra = ExtraTableEntry(
        name="Strength Bonus",
        description="+1"
    )

    row = CompanionProgressionRow(
        owner_level="3–5",
        special=[privilege],
        extra_table_entries=[extra],
    )

    assert row.special[0].name == "Evasion"
    assert row.extra_table_entries[0].name == "Strength Bonus"


# =====================
# TABLE STRUCTURE
# =====================

def test_progression_table_contains_rows():
    row1 = CompanionProgressionRow(owner_level="1–2")
    row2 = CompanionProgressionRow(owner_level="3–5")

    table = CompanionProgressionTable(rows=[row1, row2])

    assert len(table.rows) == 2
    assert table.rows[1].owner_level == "3–5"


# =====================
# COMPANION
# =====================

def test_companion_contains_progression_table():
    row = CompanionProgressionRow(owner_level="1–2")
    table = CompanionProgressionTable(rows=[row])

    companion = Companion(
        companion_type="Familiar",
        progression_table=table,
    )

    assert companion.companion_type == "Familiar"
    assert companion.progression_table.rows[0].owner_level == "1–2"


# =====================
# RAW DATA PRESERVATION
# =====================

def test_companion_fields_preserve_raw_strings():
    companion = Companion(
        companion_type="Animal Companion",
        hit_dice="as master",
        attacks="as master",
        progression_table=CompanionProgressionTable(rows=[]),
    )

    # Values are intentionally not interpreted or normalized
    assert companion.hit_dice == "as master"
    assert companion.attacks == "as master"
    