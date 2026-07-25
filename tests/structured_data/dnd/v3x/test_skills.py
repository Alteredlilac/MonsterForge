"""
Tests for the Skills model.

All fields default to None (or an empty dict for open-ended
specializations like Craft/Knowledge/Perform/Profession), so a Skills
instance can be constructed with no arguments at all.
"""


def test_skills_standard_fields_default_to_none(make_skills):
    skills = make_skills()
    assert skills.appraise is None
    assert skills.listen is None
    assert skills.spellcraft is None


def test_skills_open_ended_specializations_default_to_empty_dict(make_skills):
    """Craft, Knowledge, Perform, and Profession allow open specializations
    and are modeled as dicts rather than enums."""
    skills = make_skills()
    assert skills.craft == {}
    assert skills.knowledge == {}


def test_skills_can_set_specific_values(make_skills):
    skills = make_skills(listen=8, spot=6, hide=4)
    assert skills.listen == 8
    assert skills.spot == 6
    assert skills.hide == 4


def test_skills_craft_specialization_is_a_dict(make_skills):
    skills = make_skills(craft={"weaponsmithing": 5, "alchemy": 3})
    assert skills.craft["weaponsmithing"] == 5


def test_skills_3_0_only_fields_default_to_none():
    """
    The nine D&D 3.0-only fields (alchemy, innuendo, animal_empathy,
    read_lips, intuit_direction, scry, pick_pocket, stabilize_self,
    remote_view) now default to None, consistent with every other
    skill in this class — Skills() can be constructed with no arguments.
    """
    from monsterforge.structured_data.dnd.v3x.skills import Skills

    skills = Skills()
    assert skills.alchemy is None
    assert skills.innuendo is None
    assert skills.remote_view is None
