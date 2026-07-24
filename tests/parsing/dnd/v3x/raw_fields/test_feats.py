"""
Tests for raw feat models.

Covers:
- Basic dataclass construction
- Optional field defaults
- Raw string preservation
"""

from monsterforge.parsing.dnd.v3x.raw_fields.feats import Feat


# =====================
# FEAT
# =====================

def test_feat_creation():
    feat = Feat(
        name="Power Attack",
        feat_type="General",
        prerequisite="Str 13",
        benefit="You can choose to take a penalty on melee attack rolls.",
    )

    assert feat.name == "Power Attack"
    assert feat.feat_type == "General"


def test_feat_optional_fields_default_to_none():
    feat = Feat(
        name="Dodge",
        feat_type="General",
    )

    assert feat.description is None
    assert feat.prerequisite is None
    assert feat.benefit is None
    assert feat.normal is None
    assert feat.special is None


def test_feat_preserves_raw_sections():
    feat = Feat(
        name="Improved Familiar",
        feat_type="General",
        prerequisite="Ability to acquire a new familiar",
        benefit="You can choose a familiar from the special list.",
        special="The familiar must meet additional requirements.",
    )

    # Sections are intentionally preserved as source text
    assert feat.prerequisite == "Ability to acquire a new familiar"
    assert feat.benefit == "You can choose a familiar from the special list."
    assert feat.special == "The familiar must meet additional requirements."
    