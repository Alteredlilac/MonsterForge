"""
Tests for card base model.

Covers:
- Card creation and default values
- Automatic ID generation
- Optional image URI handling
- Override of optional fields
"""
# No imports required

# =====================
# CARD CREATION
# =====================
def test_card_creation(make_card):
    card = make_card()
    assert card.name == "Test Card"
    assert card.description == "A test card"

# =====================
# ID
# =====================
def test_card_auto_generates_unique_id(make_card):
    card1 = make_card()
    card2 = make_card()
    assert card1.id != card2.id

# =====================
# OPTIONAL FIELDS
# =====================
def test_card_image_uri_defaults_to_none(make_card):
    card = make_card()
    assert card.image_uri is None


def test_card_image_uri_can_be_set(make_card):
    card = make_card(image_uri="https://example.com/wolf.png")
    assert card.image_uri == "https://example.com/wolf.png"
