"""
Interpretation stat calculations for D&D 3.x transformation.

This module defines the rules used to convert D&D 3.x ability scores
and skill values into MonsterForge Interpretation stats.

Responsibilities:
- Resolve the D&D ability associated with each Interpretation stat.
- Group related D&D skills into Interpretation categories.
- Convert skill values into normalized contributions.
- Calculate deterministic Interpretation values from abilities and skills.

Rules:
- Ability modifiers are used as the base contribution instead of raw
  ability scores.
- Negative ability modifiers are normalized to 0.
- Skill contributions are calculated from the difference between the
  skill value and its associated ability modifier.
- When no skill contribution is available, the associated ability modifier
  is used as the default value.
- Ability scores below 10 force the associated Interpretation value to 0.
  This is an intentional simplification rule to avoid negative domain values.

Static mappings are defined in the rules package and consumed here.
This module applies transformation calculations but does not define
skill grouping or ability association tables.
"""
from typing import Mapping
from monsterforge.rules.dnd.v3x.interpretation_groups import SKILL_TO_INTERPRETATION_MAPPING, INTERPRETATION_TO_ABILITY_MAPPING
from monsterforge.structured_data.dnd.v3x.enums import SkillId, Ability
from monsterforge.domain.enums import Interpretation


# =====================
# HELPERS
# =====================
def ability_modifier(ability_value:int)-> int:
    """calcola il modificatore di una catatteristica"""
    return (ability_value - 10)//2


def calculate_skill_contribution(
    *,
    skill_value: int,
    ability_value: int
    ) -> int:
    """
    Calculate the normalized contribution of a D&D 3.x skill value.

    The contribution is derived from the associated ability modifier
    and the skill investment above the default ability contribution.
    """
    ability_contribution = max(ability_modifier(ability_value), 0)

    if skill_value == 0:
            return ability_contribution

    points = skill_value - ability_contribution - 3  
    # NOTE:
    # D&D 3.x skill values include ability modifier + 3 base skill points.
    # Remove them to keep only additional skill investment.

    return max(points, 0)

def calculate_interpretation_group_value(   
    *,
    skill_ids: list[SkillId],
    skills: Mapping[SkillId, int],
    ability_value: int   # Raw ability score value (e.g. 18), NOT the calculated ability modifier
    ) -> int:
    """
    Calculate the normalized value of an Interpretation skill group.

    The value is calculated as the average contribution of all assigned
    D&D skills. If no skill contribution exists, the associated ability
    modifier is used as the default value.
    """
    values = []

    for skill_id in skill_ids:
        if skill_id not in skills:
            continue

        val = calculate_skill_contribution(
            skill_value=skills[skill_id],
            ability_value=ability_value
        )

        if val > 0:
            values.append(val)

    if not values:
        return max(ability_modifier(ability_value), 0)  

    return sum(values) // len(values)
     
       
# =====================
# INTERPRETATION
# =====================
def calculate_interpretation(
    *,
    skills: Mapping[SkillId, int],
    abilities: Mapping[Ability, int],
    ) -> Mapping[Interpretation, int]:
    """
    Calculate MonsterForge Interpretation stats from D&D 3.x abilities
    and skills.

    Each Interpretation stat is associated with a primary D&D ability and
    a group of related skills. Skill contributions are averaged to produce
    the final deterministic value.

    Ability scores below 10 force the associated Interpretation value to 0
    according to the conversion rules.
    """
    result = {}

    for interpretation_str, ability_str in INTERPRETATION_TO_ABILITY_MAPPING.items():

        interpretation = Interpretation(interpretation_str)
        ability = Ability(ability_str) 

        ability_value = abilities[ability]  

        # NOTE: hard rule - Ability scores below 10 force the associated
        # interpretation value to 0. 
        # This is an intentional simplification rule to avoid negative domain values.
        if ability_value < 10:
            result[interpretation] = 0
            continue

        skill_ids = [
            SkillId(skill_name)
            for skill_name in SKILL_TO_INTERPRETATION_MAPPING[interpretation_str]
        ]

        result[interpretation] = calculate_interpretation_group_value(
            skill_ids=skill_ids,
            skills=skills,
            ability_value=ability_value
        )

    return result
