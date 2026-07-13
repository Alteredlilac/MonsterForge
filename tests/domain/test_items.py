"""
Tests for item card models.

Covers:
- ItemCard creation and default values
- Support for multiple item types
- Sub-dataclass composition (damage, modifiers, requirements)
- Granted moves integration
- Automatic ID generation
"""
from monsterforge.domain.items import (
    ItemMove, ItemDamage, ItemModifier, ItemRequirement,
)
from monsterforge.domain.moves import MoveCard
from monsterforge.domain.enums import (
    ItemType, DamageType, AffectedAttribute, Usage, RequirementType,
    MoveType, MoveCategory, MoveMode, EffectType, Target, Resource, Duration,
)

# =====================
# ITEM CARD CREATION
# =====================
def test_item_card_minimal_creation(make_item):
    sword = make_item()
    assert sword.name == "Iron Sword"
    assert sword.item_type == []
    assert sword.consumable is False


def test_item_card_defaults_are_empty(make_item):
    item = make_item()
    assert item.damages == []
    assert item.modifiers == []
    assert item.requirements == []
    assert item.granted_moves == []
    assert item.item_type == []

# =====================
# TYPES
# =====================
def test_item_card_supports_multiple_types(make_item):
    """An item can have more than one functional role at once (e.g. weapon + defense)."""
    sword = make_item(item_type=[ItemType.WEAPON, ItemType.DEFENSE])
    assert set(sword.item_type) == {ItemType.WEAPON, ItemType.DEFENSE}
    assert ItemType.WEAPON in sword.item_type

# =====================
# SUB-DATACLASSES
# =====================
def test_item_card_accepts_damage_sub_dataclass(make_item):
    flaming_sword = make_item(
        damages=[ItemDamage(damage_value=3, damage_type=DamageType.FIRE)]
    )
    assert flaming_sword.damages[0].damage_type == DamageType.FIRE
    assert flaming_sword.damages[0].damage_value == 3


def test_item_card_with_modifier_sub_dataclass(make_item):
    ring = make_item(
        modifiers=[ItemModifier(bonus_value=2, bonus_type=AffectedAttribute.ATTACK)]
    )
    assert ring.modifiers[0].bonus_value == 2
    assert ring.modifiers[0].bonus_type == AffectedAttribute.ATTACK


def test_item_card_with_requirement_sub_dataclass(make_item):
    heavy_armor = make_item(
        requirements=[
            ItemRequirement(
                requirement_type=RequirementType.STAT,
                required_attribute=AffectedAttribute.DEFENSE,
                minimum_attribute_value=5,
            )
        ]
    )
    assert heavy_armor.requirements[0].requirement_type == RequirementType.STAT
    assert heavy_armor.requirements[0].minimum_attribute_value == 5

# =====================
# MOVES
# =====================
def test_item_card_can_grant_a_move(make_item):
    """An item can grant a usable MoveCard (e.g. a wand granting a spell-like attack)."""
    fireball_move = MoveCard(
        name="Fireball", description="Launches a fireball",
        move_type=MoveType.MAGICAL, category=MoveCategory.ATTACK, mode=MoveMode.ACTIVE,
        effect=EffectType.DAMAGE, target=Target.AREA, resource=Resource.MANA,
        duration=Duration.INSTANT, usage=Usage.LIMITED,
    )
    wand = make_item(
        granted_moves=[ItemMove(move=fireball_move, usage=Usage.LIMITED)]
    )
    assert wand.granted_moves[0].move is fireball_move

# =====================
# ID
# =====================
def test_item_card_auto_generates_unique_id(make_item):
    item1 = make_item()
    item2 = make_item()
    assert item1.id != item2.id
