"""
Tests for entity domain models.

Covers:
- Entity creation and default values
- Automatic ID generation
- Base form selection from creature cards
- Creature form validation
"""
from monsterforge.domain.entity import Entity
from monsterforge.domain.enums import CreatureType

# =====================
# ENTITY CREATION
# =====================
def test_entity_minimal_creation(make_creature):
    entity = Entity(creature_cards=[make_creature("Wolf")])
    assert entity.entity_description is None
    assert entity.move_cards == []
    assert entity.item_cards == []

# =====================
# ID
# =====================
def test_entity_auto_generates_unique_id(make_creature):
    entity1 = Entity(creature_cards=[make_creature("Wolf")])
    entity2 = Entity(creature_cards=[make_creature("Wolf")])
    assert entity1.id != entity2.id

# =====================
# BASE FORM
# =====================
def test_entity_base_form_is_first_creature_card(make_creature):
    """base_form always returns the creature card at index 0, per the shapeshifting convention."""
    human_form = make_creature("Human", creature_type=CreatureType.HUMANOID)
    wolf_form = make_creature("Wolf")
    entity = Entity(creature_cards=[human_form, wolf_form])
    assert entity.base_form is human_form
    assert entity.base_form is not wolf_form

def test_entity_base_form_is_none_without_any_creature():
    """An Entity with no creature_cards has no base form — base_form
    returns None rather than raising, matching what domain_to_json.py
    already relies on when serializing such an Entity."""
    entity = Entity()
    assert entity.base_form is None
