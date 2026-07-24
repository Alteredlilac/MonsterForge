"""
Tests for D&D 3.x magic item raw field models.

Covers:
- Magic item inheritance from mundane item structures
- Raw value preservation
- Stored spell representation
- Default values
- Empty category classes
"""

from monsterforge.parsing.dnd.v3x.raw_fields.items import (
    Item,
    Armor,
    Weapon,
)

from monsterforge.parsing.dnd.v3x.raw_fields.magic_items import (
    MagicArmor,
    MagicWeapon,
    StoredSpell,
    Potion,
    Ring,
    Rod,
    Scroll,
    MagicStaff,
    MagicWand,
    WondrousItem,
)


# =====================
# INHERITANCE
# =====================

def test_magic_armor_is_subclass_of_armor():
    assert issubclass(MagicArmor, Armor)


def test_magic_weapon_is_subclass_of_weapon():
    assert issubclass(MagicWeapon, Weapon)


def test_magic_items_are_subclass_of_item():
    assert issubclass(Potion, Item)
    assert issubclass(Scroll, Item)
    assert issubclass(MagicStaff, Item)
    assert issubclass(MagicWand, Item)
    assert issubclass(WondrousItem, Item)


# =====================
# STORED SPELL
# =====================

def test_stored_spell_preserves_raw_values():
    spell = StoredSpell(
        spell_name="Fireball",
        added_description="+3",
        spell_charges="(1 charge)",
    )

    assert spell.spell_name == "Fireball"
    assert spell.added_description == "+3"
    assert spell.spell_charges == "(1 charge)"


# =====================
# MAGIC ARMOR
# =====================

def test_magic_armor_preserves_raw_values():
    armor = MagicArmor(
        name="Armor of Resistance",
        armor_bonus="+5",
        enhancement_bonus="+2",
        base_price_modifier="+2000 gp",
    )

    assert armor.name == "Armor of Resistance"
    assert armor.armor_bonus == "+5"
    assert armor.enhancement_bonus == "+2"
    assert armor.base_price_modifier == "+2000 gp"


# =====================
# MAGIC WEAPON
# =====================

def test_magic_weapon_preserves_raw_values():
    weapon = MagicWeapon(
        name="Flaming Sword",
        damage="1d8",
        enhancement_bonus="+1",
        base_price_modifier="+8000 gp",
    )

    assert weapon.name == "Flaming Sword"
    assert weapon.damage == "1d8"
    assert weapon.enhancement_bonus == "+1"
    assert weapon.base_price_modifier == "+8000 gp"


# =====================
# POTION
# =====================

def test_potion_stores_granted_spell():
    spell = StoredSpell(
        spell_name="Cure Light Wounds"
    )

    potion = Potion(
        name="Potion of Healing",
        stored_spell=spell,
        potion_type="potion",
    )

    assert potion.stored_spell == spell
    assert potion.potion_type == "potion"


# =====================
# SCROLL
# =====================

def test_scroll_preserves_spell_and_type():
    spell = StoredSpell(
        spell_name="Magic Missile"
    )

    scroll = Scroll(
        name="Scroll of Magic Missile",
        stored_spell=spell,
        is_arcane=True,
    )

    assert scroll.stored_spell == spell
    assert scroll.is_arcane is True
    assert scroll.is_divine is None


# =====================
# MAGIC STAFF
# =====================

def test_magic_staff_stores_multiple_spells():
    spells = [
        StoredSpell(spell_name="Fireball"),
        StoredSpell(spell_name="Lightning Bolt"),
    ]

    staff = MagicStaff(
        name="Staff of Power",
        stored_spell=spells,
    )

    assert staff.stored_spell == spells
    assert len(staff.stored_spell) == 2


# =====================
# MAGIC WAND
# =====================

def test_magic_wand_stores_spell():
    spell = StoredSpell(
        spell_name="Magic Missile"
    )

    wand = MagicWand(
        name="Wand of Magic Missile",
        stored_spell=spell,
    )

    assert wand.stored_spell == spell


# =====================
# WONDROUS ITEM
# =====================

def test_wondrous_item_flags_default_to_false():
    item = WondrousItem(
        name="Bag of Holding"
    )

    assert item.is_intelligent is False
    assert item.is_cursed is False
    assert item.is_artifact is False


# =====================
# EMPTY CATEGORY ITEMS
# =====================

def test_ring_preserves_base_item_fields():
    ring = Ring(
        name="Ring of Protection",
        description="A magic protective ring",
    )

    assert ring.name == "Ring of Protection"
    assert ring.description == "A magic protective ring"


def test_rod_preserves_base_item_fields():
    rod = Rod(
        name="Rod of Wonder",
        description="A strange magical rod",
    )

    assert rod.name == "Rod of Wonder"
    assert rod.description == "A strange magical rod"
    