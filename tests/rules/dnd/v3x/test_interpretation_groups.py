"""
Tests for interpretation_groups.py.

These are static rule mappings, so tests focus on structural integrity
rather than calculation logic.

The module defines the relationships between:
- D&D 3.x skills and MonsterForge interpretation groups
- interpretation groups and their reference ability scores

Tests verify:
- all interpretation groups have a reference ability
- the expected number of interpretation groups exists
- each D&D skill belongs to only one group
- mappings remain immutable
"""
from monsterforge.rules.dnd.v3x.interpretation_groups import (
    SKILL_TO_INTERPRETATION_MAPPING, INTERPRETATION_TO_ABILITY_MAPPING,
)


def test_all_interpretation_groups_have_a_reference_ability():
    """Every interpretation group must have a corresponding
    reference ability mapping, otherwise the transformation step
    would fail during lookup.
    """
    for group in SKILL_TO_INTERPRETATION_MAPPING:
        assert group in INTERPRETATION_TO_ABILITY_MAPPING


def test_six_interpretation_groups_exist():
    assert len(SKILL_TO_INTERPRETATION_MAPPING) == 6


def test_no_duplicate_skills_across_groups():
    """A D&D skill should belong to exactly one interpretation group,
    otherwise it would be double-counted or ambiguous during conversion."""
    all_skills = []
    for skills in SKILL_TO_INTERPRETATION_MAPPING.values():
        all_skills.extend(skills)
    assert len(all_skills) == len(set(all_skills))


def test_tables_are_immutable():
    """MappingProxyType should reject direct mutation attempts."""
    import pytest

    with pytest.raises(TypeError):
        SKILL_TO_INTERPRETATION_MAPPING["athletics"] = []
