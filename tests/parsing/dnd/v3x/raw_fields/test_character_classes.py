"""
Tests for raw character class progression models.

Covers:
- Basic dataclass construction
- Nested structures (rows → table → class)
- Default values for optional and list fields
- Preservation of table structure (None spell slots)
"""

from monsterforge.parsing.dnd.v3x.raw_fields.character_classes import (
    CharacterPrivilege,
    SpellSlots,
    ExtraTableEntry,
    CharacterProgressionRow,
    CharacterProgressionTable,
    CharacterClass,
)


# =====================
# BASIC STRUCTURES
# =====================

def test_character_privilege_creation():
    privilege = CharacterPrivilege(
        name="Rage",
        description="Grants bonus to strength"
    )

    assert privilege.name == "Rage"


def test_extra_table_entry_creation():
    entry = ExtraTableEntry(
        name="Bonus Spells",
        description="Additional spells per day"
    )

    assert entry.name == "Bonus Spells"


# =====================
# SPELL SLOTS
# =====================

def test_spell_slots_preserve_none_values():
    # Missing spell levels must default to None to preserve table alignment
    slots = SpellSlots(level_0="3")

    assert slots.level_1 is None
    assert slots.level_8 is None


# =====================
# PROGRESSION ROW
# =====================

def test_progression_row_creation_with_defaults():
    row = CharacterProgressionRow(
        level="1",
        base_attack_bonus="+0",
        fort_save="+2",
        ref_save="+0",
        will_save="+0",
    )

    # default lists must be empty (not shared)
    assert row.special == []
    assert row.extra_table_entries == []


def test_progression_row_with_nested_data():
    privilege = CharacterPrivilege(
        name="Sneak Attack",
        description="+1d6 damage"
    )

    extra = ExtraTableEntry(
        name="Bonus",
        description="+1 to initiative"
    )

    row = CharacterProgressionRow(
        level="1",
        base_attack_bonus="+0",
        fort_save="+0",
        ref_save="+2",
        will_save="+0",
        special=[privilege],
        extra_table_entries=[extra],
    )

    assert row.special[0].name == "Sneak Attack"
    assert row.extra_table_entries[0].name == "Bonus"


# =====================
# TABLE STRUCTURE
# =====================

def test_progression_table_contains_rows():
    row1 = CharacterProgressionRow(
        level="1",
        base_attack_bonus="+0",
        fort_save="+2",
        ref_save="+0",
        will_save="+0",
    )

    row2 = CharacterProgressionRow(
        level="2",
        base_attack_bonus="+1",
        fort_save="+3",
        ref_save="+0",
        will_save="+0",
    )

    table = CharacterProgressionTable(rows=[row1, row2])

    assert len(table.rows) == 2
    assert table.rows[1].level == "2"


# =====================
# CHARACTER CLASS
# =====================

def test_character_class_contains_progression_table():
    row = CharacterProgressionRow(
        level="1",
        base_attack_bonus="+0",
        fort_save="+2",
        ref_save="+0",
        will_save="+0",
    )

    table = CharacterProgressionTable(rows=[row])

    char_class = CharacterClass(
        name="Barbarian",
        hit_die="d12",
        progression_table=table,
    )

    assert char_class.name == "Barbarian"
    assert char_class.progression_table.rows[0].level == "1"
