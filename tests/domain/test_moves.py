"""
Tests for move card models.

Covers:
- MoveCard creation and default values
- Optional fields and list defaults
- Damage and effect configuration
- Automatic ID generation
"""
from monsterforge.domain.enums import DamageType

# =====================
# MOVE CARD CREATION
# =====================
def test_move_card_minimal_creation(make_move):
    """A MoveCard can be created with only the required fields; optional fields default sensibly."""
    bite = make_move()
    assert bite.name == "Bite"
    assert bite.damage_type is None
    assert bite.effect_value is None

# =====================
# DEFAULTS
# =====================
def test_move_card_optional_lists_default_to_empty(make_move):
    bite = make_move()
    assert bite.entity_effect == []
    assert bite.cards_to_add == []
    assert bite.cards_to_remove == []

# =====================
# EFFECTS
# =====================
def test_move_card_with_damage_details(make_move):
    bite = make_move(damage_type=DamageType.PHYSICAL, effect_value=3)
    assert bite.damage_type == DamageType.PHYSICAL
    assert bite.effect_value == 3

# =====================
# ID
# =====================
def test_move_card_auto_generates_unique_id(make_move):
    bite1 = make_move()
    bite2 = make_move()
    assert bite1.id != bite2.id
