"""
Tests for creature card models.

Covers:
- CreatureCard creation and default values
- Automatic ID generation
- Inheritance from Card
- PlayerCard specialization and inheritance
- Factory override behavior
"""

from monsterforge.domain.cards import Card
from monsterforge.domain.creatures import CreatureCard, PlayerCard
from monsterforge.domain.enums import CreatureType

# =====================
# INHERITANCE
# =====================
def test_creature_card_is_subclass_of_card():
    assert issubclass(CreatureCard, Card)


def test_player_card_is_subclass_of_creature_card():
    assert issubclass(PlayerCard, CreatureCard)

# =====================
# CREATURE CARD
# =====================
def test_creature_card_creation(make_creature):
    wolf = make_creature()
    assert wolf.name == "Wolf"
    assert wolf.creature_type == CreatureType.ANIMAL
    assert wolf.level == 1

def test_creature_card_current_life_defaults_to_none(make_creature):
    wolf = make_creature()
    assert wolf.current_life is None

def test_creature_card_auto_generates_unique_id(make_creature):
    wolf1 = make_creature()
    wolf2 = make_creature()
    assert wolf1.id != wolf2.id


def test_creature_card_override(make_creature):
    wolf = make_creature(name="Dire Wolf", level=5)
    assert wolf.name == "Dire Wolf"
    assert wolf.level == 5

# =====================
# PLAYER CARD
# =====================
def test_player_card_creation(make_player):
    hero = make_player()
    assert hero.player_name == "Lilak"
    assert hero.name == "Hero"
