"""
Tests for Item, MagicItem, and IntelligentItem.
"""
from monsterforge.structured_data.dnd.v3x.items import Item, MagicItem, IntelligentItem
from monsterforge.structured_data.dnd.v3x.enums import (
    ItemType, ItemPowerType, IntelligentItemType,
)


def test_item_minimal_creation():
    sword = Item(item_type=ItemType.WEAPON)
    assert sword.item_type == ItemType.WEAPON
    assert sword.name is None
    assert sword.is_consumable is False


def test_item_with_damage_and_range(make_damage, make_effect_range):
    bow = Item(
        item_type=ItemType.WEAPON, melee=False,
        attack_range=make_effect_range(effect_range=18),
        damages=[make_damage()],
    )
    assert bow.melee is False
    assert bow.attack_range.effect_range == 18


def test_item_with_damage_reduction(make_damage_reduction):
    armor = Item(
        item_type=ItemType.ARMOR,
        damage_reduction=make_damage_reduction(reduction_value=5),
    )
    assert armor.damage_reduction.reduction_value == 5


def test_magic_item_healing_effects_defaults_to_empty_list():
    wand = MagicItem(item_type=ItemType.TOOL, magic_type=ItemPowerType.MAGICAL)
    assert wand.healing_effects == []


def test_magic_item_minimal_creation():
    wand = MagicItem(
        item_type=ItemType.TOOL, magic_type=ItemPowerType.MAGICAL,
    )
    assert wand.magic_type == ItemPowerType.MAGICAL
    assert wand.is_artifact is False
    assert wand.is_cursed is False


def test_magic_item_can_be_psionic():
    dorje = MagicItem(
        item_type=ItemType.TOOL, magic_type=ItemPowerType.PSIONIC,
    )
    assert dorje.magic_type == ItemPowerType.PSIONIC


def test_magic_item_with_grants(make_effect_grant):
    staff = MagicItem(
        item_type=ItemType.TOOL, magic_type=ItemPowerType.MAGICAL,
        grants=[make_effect_grant()],
    )
    assert len(staff.grants) == 1


def test_intelligent_item_creation():
    sword = IntelligentItem(
        item_type=ItemType.WEAPON, magic_type=ItemPowerType.MAGICAL,
        intelligent_type=IntelligentItemType.INTELLIGENT,
        intelligence=14, wisdom=12, charisma=16,
    )
    assert sword.intelligent_type == IntelligentItemType.INTELLIGENT
    assert sword.intelligence == 14


def test_intelligent_item_is_a_magic_item():
    symbiont = IntelligentItem(
        item_type=ItemType.WEAPON, magic_type=ItemPowerType.PSIONIC,
        intelligent_type=IntelligentItemType.SYMBIOTIC,
        intelligence=10, wisdom=10, charisma=10,
    )
    assert isinstance(symbiont, MagicItem)
