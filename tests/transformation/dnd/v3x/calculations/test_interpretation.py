"""
Tests for Interpretation stat calculation: ability modifiers, skill
contributions, group averaging, and the full calculate_interpretation
pipeline.
"""
from monsterforge.transformation.dnd.v3x.calculations.interpretation import (
    ability_modifier, calculate_skill_contribution,
    calculate_interpretation_group_value, calculate_interpretation,
)
from monsterforge.structured_data.dnd.v3x.enums import SkillId, Ability
from monsterforge.domain.enums import Interpretation


# =====================
# ABILITY MODIFIER
# =====================
def test_ability_modifier_matches_dnd_formula():
    assert ability_modifier(15) == 2
    assert ability_modifier(10) == 0
    assert ability_modifier(8) == -1


# =====================
# SKILL CONTRIBUTION
# =====================
def test_skill_contribution_uses_ability_modifier_when_untrained():
    """A skill value of 0 (no ranks) contributes the ability modifier
    itself, per design.md."""
    result = calculate_skill_contribution(skill_value=0, ability_value=15)
    assert result == 2  # ability_modifier(15)


def test_skill_contribution_extracts_ranks_from_trained_skill():
    """D&D skill values bundle ability modifier + 3 base points; this
    strips them to isolate actual rank investment."""
    result = calculate_skill_contribution(skill_value=10, ability_value=15)
    assert result == 5  # 10 - 2 (mod) - 3 (base)


def test_skill_contribution_never_negative():
    result = calculate_skill_contribution(skill_value=1, ability_value=15)
    assert result == 0


# =====================
# GROUP VALUE (averaging)
# =====================
def test_interpretation_group_falls_back_to_ability_modifier_with_no_skills():
    result = calculate_interpretation_group_value(
        skill_ids=[SkillId.LISTEN, SkillId.SPOT], skills={}, ability_value=14,
    )
    assert result == 2  # ability_modifier(14)


def test_interpretation_group_averages_multiple_skill_contributions():
    """Two skills with contributions 5 and 7 average to 6."""
    skills = {SkillId.LISTEN: 9, SkillId.SPOT: 11}  # ability_value=12 -> mod=1
    result = calculate_interpretation_group_value(
        skill_ids=[SkillId.LISTEN, SkillId.SPOT], skills=skills, ability_value=12,
    )
    # LISTEN: 9 - 1 - 3 = 5; SPOT: 11 - 1 - 3 = 7; avg = 6
    assert result == 6


def test_interpretation_group_excludes_zero_contributions_from_average():
    """Per design.md, only non-zero contributions are averaged. An
    untrained skill (value=0) whose associated ability modifier is
    itself 0 contributes exactly 0 and is excluded — only the trained
    skill counts toward the average."""
    skills = {SkillId.LISTEN: 0, SkillId.SPOT: 13}  # ability_value=10 -> mod=0
    result = calculate_interpretation_group_value(
        skill_ids=[SkillId.LISTEN, SkillId.SPOT], skills=skills, ability_value=10,
    )
    # LISTEN untrained, mod=0 -> contributes 0 -> excluded
    # SPOT: 13 - 0 - 3 = 10 -> included, and is the only value averaged
    assert result == 10


# =====================
# FULL PIPELINE
# =====================
def test_calculate_interpretation_returns_all_six_categories():
    abilities = {
        Ability.STRENGTH: 13, Ability.DEXTERITY: 15, Ability.CONSTITUTION: 15,
        Ability.INTELLIGENCE: 2, Ability.WISDOM: 12, Ability.CHARISMA: 6,
    }
    result = calculate_interpretation(skills={}, abilities=abilities)
    assert len(result) == 6
    assert Interpretation.PERCEPTION in result


def test_calculate_interpretation_forces_zero_below_ability_10():
    """An ability score below 10 forces the associated Interpretation
    value to 0, regardless of any skill investment."""
    abilities = {
        Ability.STRENGTH: 13, Ability.DEXTERITY: 15, Ability.CONSTITUTION: 15,
        Ability.INTELLIGENCE: 2, Ability.WISDOM: 12, Ability.CHARISMA: 6,
    }
    result = calculate_interpretation(skills={}, abilities=abilities)
    # Charisma 6 -> Empathy forced to 0; Intelligence 2 -> Knowledge/Crafting forced to 0
    assert result[Interpretation.EMPATHY] == 0
    assert result[Interpretation.KNOWLEDGE] == 0
    