"""
Tests for D&D 3.x psionic item raw field models.

Covers:
- Psionic item inheritance from mundane item structures
- Raw value preservation
- Stored power representation
- Psionic item spell/power containers
- Default values for universal items
"""

from monsterforge.parsing.dnd.v3x.raw_fields.items import (
    Item,
    Armor,
    Weapon,
)

from monsterforge.parsing.dnd.v3x.raw_fields.psionic_items import (
    PsionicArmor,
    PsionicWeapon,
    StoredPower,
    Dorje,
    PowerStone,
    Psicrown,
    PsionicTattoo,
    PsionicUniversalItem,
)


# =====================
# INHERITANCE
# =====================

def test_psionic_armor_is_subclass_of_armor():
    assert issubclass(PsionicArmor, Armor)


def test_psionic_weapon_is_subclass_of_weapon():
    assert issubclass(PsionicWeapon, Weapon)


def test_psionic_items_are_subclass_of_item():
    assert issubclass(Dorje, Item)
    assert issubclass(PowerStone, Item)
    assert issubclass(Psicrown, Item)
    assert issubclass(PsionicTattoo, Item)
    assert issubclass(PsionicUniversalItem, Item)


# =====================
# STORED POWER
# =====================

def test_stored_power_preserves_raw_values():
    power = StoredPower(
        power_name="Energy Ray",
        added_description="+2",
        power_charges="(1 charge)",
    )

    assert power.power_name == "Energy Ray"
    assert power.added_description == "+2"
    assert power.power_charges == "(1 charge)"


def test_stored_power_optional_fields_default_to_none():
    power = StoredPower(
        power_name="Mind Thrust",
    )

    assert power.added_description is None
    assert power.power_charges is None


# =====================
# PSIONIC ARMOR
# =====================

def test_psionic_armor_preserves_raw_values():
    armor = PsionicArmor(
        name="Mindarmor",
        armor_bonus="+4",
        enhancement_bonus="+2",
        base_price_modifier="+6000 gp",
    )

    assert armor.name == "Mindarmor"
    assert armor.armor_bonus == "+4"
    assert armor.enhancement_bonus == "+2"
    assert armor.base_price_modifier == "+6000 gp"


# =====================
# PSIONIC WEAPON
# =====================

def test_psionic_weapon_preserves_raw_values():
    weapon = PsionicWeapon(
        name="Psychic Longsword",
        damage="1d8",
        enhancement_bonus="+1",
        base_price_modifier="+8000 gp",
    )

    assert weapon.name == "Psychic Longsword"
    assert weapon.damage == "1d8"
    assert weapon.enhancement_bonus == "+1"
    assert weapon.base_price_modifier == "+8000 gp"


# =====================
# DORJE
# =====================

def test_dorje_stores_single_power():
    power = StoredPower(
        power_name="Energy Ray",
    )

    dorje = Dorje(
        name="Dorje of Energy Ray",
        stored_power=power,
    )

    assert dorje.stored_power == power
    assert dorje.stored_power.power_name == "Energy Ray"


# =====================
# POWER STONE
# =====================

def test_power_stone_stores_multiple_powers():
    powers = [
        StoredPower(power_name="Mind Thrust"),
        StoredPower(power_name="Energy Push"),
    ]

    stone = PowerStone(
        name="Power Stone",
        stored_powers=powers,
        manifester_class="Psion",
    )

    assert stone.stored_powers == powers
    assert len(stone.stored_powers) == 2
    assert stone.manifester_class == "Psion"


# =====================
# PSICROWN
# =====================

def test_psicrown_preserves_powers_without_power_points():
    powers = [
        StoredPower(power_name="Energy Burst"),
    ]

    crown = Psicrown(
        name="Psicrown of the Evoker",
        stored_powers=powers,
    )

    assert crown.stored_powers == powers
    assert crown.additional_description is None


# =====================
# PSIONIC TATTOO
# =====================

def test_psionic_tattoo_stores_single_power():
    power = StoredPower(
        power_name="Vigor",
    )

    tattoo = PsionicTattoo(
        name="Psionic Tattoo of Vigor",
        stored_power=power,
    )

    assert tattoo.stored_power == power


# =====================
# UNIVERSAL ITEM
# =====================

def test_psionic_universal_item_flags_default_to_false():
    item = PsionicUniversalItem(
        name="Third Eye",
    )

    assert item.is_intelligent is False
    assert item.is_cursed is False
    assert item.is_artifact is False
    