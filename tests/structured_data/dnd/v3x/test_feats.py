"""
Tests for the Feat model and its requirement helpers.
"""
from monsterforge.structured_data.dnd.v3x.feats import Feat, FeatRequirement, SaveRequirement
from monsterforge.structured_data.dnd.v3x.enums import FeatCategory, SavingThrowType


def test_feat_minimal_creation():
    feat = Feat(name="Power Attack", description="Trade accuracy for damage")
    assert feat.name == "Power Attack"
    assert feat.categories == []
    assert feat.requirements == []


def test_feat_can_belong_to_multiple_categories():
    """A feat can grant a bonus AND an attack at once (e.g. some
    combat feats), so categories is a list, not a single value."""
    feat = Feat(
        name="Improved Trip", description="x",
        categories=[FeatCategory.GRANTS_BONUS, FeatCategory.GRANTS_ATTACK],
    )
    assert FeatCategory.GRANTS_BONUS in feat.categories
    assert FeatCategory.GRANTS_ATTACK in feat.categories


def test_feat_with_granted_modifiers(make_effect_modifier):
    feat = Feat(
        name="Weapon Focus", description="x",
        granted_modifiers=[make_effect_modifier()],
    )
    assert len(feat.granted_modifiers) == 1


def test_feat_metamagic_fields_default_to_none():
    feat = Feat(name="Empower Spell", description="x")
    assert feat.metamagic_effect is None
    assert feat.metamagic_level_adjustment is None


def test_save_requirement_creation():
    req = SaveRequirement(save_type=SavingThrowType.FORTITUDE, minimum_value=4)
    assert req.save_type == SavingThrowType.FORTITUDE
    assert req.minimum_value == 4


def test_feat_requirement_minimal_creation():
    req = FeatRequirement(description="Str 13")
    assert req.description == "Str 13"
    assert req.spellcasting is False
    assert req.psionics is False


def test_feat_requirement_with_multiple_saving_throws():
    """A single feat requirement can reference multiple save
    thresholds (e.g. 'Fort +4 and Ref +2')."""
    req = FeatRequirement(
        description="x",
        saving_throw=[
            SaveRequirement(save_type=SavingThrowType.FORTITUDE, minimum_value=4),
            SaveRequirement(save_type=SavingThrowType.REFLEX, minimum_value=2),
        ],
    )
    assert len(req.saving_throw) == 2


def test_feat_requirement_class_and_level():
    req = FeatRequirement(
        description="x", required_character_class="Fighter", minimum_level=6,
    )
    assert req.required_character_class == "Fighter"
    assert req.minimum_level == 6


def test_feat_with_requirements_and_grants(make_effect_grant):
    feat = Feat(
        name="Leadership", description="x",
        requirements=[FeatRequirement(description="Character level 6")],
        grants=[make_effect_grant()],
    )
    assert len(feat.requirements) == 1
    assert len(feat.grants) == 1
