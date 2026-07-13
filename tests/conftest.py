"""
Shared test fixtures for domain models.

Provides factory fixtures to create test instances of core entities:
- Card
- CreatureCard and PlayerCard
- ItemCard
- MoveCard

Each fixture returns a callable that allows overriding default values
to easily customize test objects.
"""
import pytest
from monsterforge.domain.cards import Card
from monsterforge.domain.creatures import CreatureCard, PlayerCard
from monsterforge.domain.enums import CreatureType, Size
from monsterforge.domain.items import ItemCard
from monsterforge.domain.moves import MoveCard
from monsterforge.domain.enums import (
    MoveType, MoveCategory, MoveMode, EffectType,
    Target, Resource, Duration, Usage
)

# =====================
# GENERIC CARD
# =====================
@pytest.fixture
def make_card():
    """Factory fixture returning a function to create Card test instances."""
    def _make_card(**overrides):
        defaults = {
            "name" : "Test Card",
            "description" : "A test card"
            }
        
        defaults.update(overrides)

        return Card(**defaults)
    
    return _make_card

# =====================
# CREATURE CARD
# =====================
@pytest.fixture
def make_creature():
    """Factory fixture returning a function to create CreatureCard test instances."""
    def _make_creature(name="Wolf", **overrides):
        defaults = {
        "name": name,
        "description": "A wild wolf",
        "level": 1,
        "total_life": 23,
        "armor": 2,
        "talisman": 0,
        "athletics": 2,
        "empathy": 0,
        "perception": 2,
        "stealth": 2,
        "knowledge": 0,
        "crafting": 0,
        "stamina": 1,
        "mana": 0,
        "attack": 1,
        "defense": 2,
        "speed": 2,
        "power": 0,
        "ward": 1,
        "flow": 0,
        "creature_type": CreatureType.ANIMAL,
        "creature_size": Size.MEDIUM,
    }

        defaults.update(overrides)

        return CreatureCard(**defaults)

    return _make_creature

# =====================
# PLAYER CARD
# =====================
@pytest.fixture
def make_player():
    """Factory fixture returning a function to create PlayerCard test instances."""
    def _make_player(**overrides):
        defaults = {
            "name": "Hero",
            "description": "A brave adventurer",
            "level": 1,
            "creature_type": CreatureType.HUMANOID,
            "creature_size": Size.MEDIUM,
            "total_life": 30,
            "armor": 3,
            "talisman": 1,
            "athletics": 1,
            "empathy": 1,
            "perception": 1,
            "stealth": 1,
            "knowledge": 1,
            "crafting": 1,
            "stamina": 2,
            "mana": 1,
            "attack": 2,
            "defense": 2,
            "speed": 2,
            "power": 1,
            "ward": 1,
            "flow": 1,
            "player_name": "Lilak",
        }

        defaults.update(overrides)

        return PlayerCard(**defaults)

    return _make_player

# =====================
# ITEM CARD
# =====================
@pytest.fixture
def make_item():
    """Factory fixture returning a function to create ItemCard test instances."""
    def _make_item(**overrides):
        defaults = {
            "name": "Iron Sword",
            "description": "A simple iron sword",
            "item_size": Size.MEDIUM,
            "price": 10,
        }

        defaults.update(overrides)

        return ItemCard(**defaults)
    
    return _make_item

# =====================
# MOVE CARD
# =====================
@pytest.fixture
def make_move():
    """Factory fixture returning a function to create MoveCard test instances."""
    def _make_move(**overrides):
        defaults = {
            "name": "Bite",
            "description": "A natural bite attack",
            "move_type": MoveType.PHYSICAL,
            "category": MoveCategory.ATTACK,
            "mode": MoveMode.ACTIVE,
            "effect": EffectType.DAMAGE,
            "target": Target.SINGLE,
            "resource": Resource.STAMINA,
            "duration": Duration.INSTANT,
            "usage": Usage.UNLIMITED,
        }

        defaults.update(overrides)

        return MoveCard(**defaults)
    
    return _make_move
