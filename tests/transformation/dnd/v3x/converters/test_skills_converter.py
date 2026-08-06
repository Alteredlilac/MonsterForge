"""
Tests for flatten_skills: converts structured_data Skills into a flat
dict suitable for the interpretation calculation.
"""
from monsterforge.transformation.dnd.v3x.converters.skills_converter import flatten_skills
from monsterforge.structured_data.dnd.v3x.skills import Skills


def test_flatten_skills_excludes_unset_fields():
    """Fields left at their None default are not included in the output."""
    skills = Skills(listen=8)
    result = flatten_skills(skills)
    assert "spot" not in result
    assert result["listen"] == 8


def test_flatten_skills_excludes_empty_specialization_dicts():
    """An empty Craft/Knowledge/etc. dict (no specializations set)
    contributes no key at all."""
    skills = Skills(craft={})
    result = flatten_skills(skills)
    assert "craft" not in result


def test_flatten_skills_uses_highest_specialization_value():
    """Knowledge (arcana=12, nature=4) flattens to 12 — the highest
    specialization, not an average, to avoid diluting expertise."""
    skills = Skills(knowledge={"arcana": 12, "nature": 4, "religion": 6})
    result = flatten_skills(skills)
    assert result["knowledge"] == 12


def test_flatten_skills_combines_simple_and_specialized_fields():
    skills = Skills(listen=8, spot=6, knowledge={"arcana": 12, "nature": 4})
    result = flatten_skills(skills)
    assert result == {"listen": 8, "spot": 6, "knowledge": 12}


def test_flatten_skills_on_empty_skills_returns_empty_dict():
    skills = Skills()
    result = flatten_skills(skills)
    assert result == {}
    