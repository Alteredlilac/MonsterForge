"""
Tests for raw item field models.

Covers:
- Item base model creation
- Weapon and Armor inheritance
- Default values
- Raw value preservation
- Independent mutable defaults
"""

from monsterforge.parsing.dnd.v3x.raw_fields.items import (
    Item,
    Weapon,
    Armor,
)


# =====================
# INHERITANCE
# =====================

def test_weapon_is_subclass_of_item():
    assert issubclass(Weapon, Item)


def test_armor_is_subclass_of_item():
    assert issubclass(Armor, Item)


# =====================
# ITEM
# =====================

def test_item_creation():
    item = Item(
        name="Backpack",
        description="A simple leather backpack",
        price="2 gp",
    )

    assert item.name == "Backpack"
    assert item.description == "A simple leather backpack"
    assert item.price == "2 gp"


def test_item_defaults_to_none():
    item = Item()

    assert item.name is None
    assert item.description is None
    assert item.price is None


# =====================
# WEAPON
# =====================

def test_weapon_preserves_raw_values():
    weapon = Weapon(
        name="Longsword",
        damage="1d8",
        damage_type=["slashing"],
        critical="19-20/x2",
        range_increment=None,
    )

    assert weapon.name == "Longsword"
    assert weapon.damage == "1d8"
    assert weapon.damage_type == ["slashing"]
    assert weapon.critical == "19-20/x2"


def test_weapon_default_flags():
    weapon = Weapon()

    assert weapon.nonlethal_damage is False
    assert weapon.reach_weapon is False
    assert weapon.double_weapon is False


def test_weapon_damage_type_has_independent_default_list():
    weapon_a = Weapon()
    weapon_b = Weapon()

    weapon_a.damage_type.append("slashing")

    assert weapon_b.damage_type == []


# =====================
# ARMOR
# =====================

def test_armor_preserves_raw_values():
    armor = Armor(
        name="Tower Shield",
        armor_bonus="+4",
        maximum_dex_bonus="2",
        armor_check_penalty="-10",
        arcane_spell_failure_chance="50%",
        max_speed="30 ft.",
    )

    assert armor.name == "Tower Shield"
    assert armor.armor_bonus == "+4"
    assert armor.maximum_dex_bonus == "2"
    assert armor.armor_check_penalty == "-10"
    assert armor.arcane_spell_failure_chance == "50%"
    assert armor.max_speed == "30 ft."


def test_armor_additional_notes_preserve_raw_text():
    armor = Armor(
        additional_notes="A tower shield can instead grant you cover."
    )

    assert armor.additional_notes == (
        "A tower shield can instead grant you cover."
    )
    