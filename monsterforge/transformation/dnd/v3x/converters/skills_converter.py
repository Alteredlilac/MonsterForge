"""
Skill conversion utilities for D&D 3.x transformation.

This module defines the conversion rules used to transform D&D 3.x
structured skill data into a flattened deterministic representation
used by the transformation layer.

Responsibilities:
- Remove missing skill values.
- Flatten specialized skills into their base skill category.
- Preserve meaningful specialization values when multiple entries exist.

Rules:
- Specialized skills (e.g. Craft, Knowledge, Perform, Profession)
  are represented by their highest specialization value.
- Output values are returned as a uniform skill mapping.

This module converts structured_data representations into a format
consumed by calculation functions.
It does not apply domain calculation rules.
"""
from dataclasses import fields
from monsterforge.structured_data.dnd.v3x.skills import Skills

# =====================
# FLATTEN SKILLS
# =====================
def flatten_skills(skills: Skills) -> dict[str, int]:
    """
    Flatten D&D 3.x skills into a uniform skill mapping.

    Rules:
    - Skills with no assigned value are ignored.
    - Specialized skills (e.g. Craft, Knowledge, Perform, Profession)
      are represented by their highest specialization value.
    - Output values are returned as a flat skill mapping.

    Examples:
        Knowledge:
            arcana = 12
            nature = 4
            religion = 6

        becomes:
            Knowledge = 12
    """
    result = {}

    for field in fields(skills):
        value = getattr(skills, field.name)

        if value is None:
            continue

        if isinstance(value, dict):
            if value:
                result[field.name] = max(value.values())

        else:
            result[field.name] = value

    return result

# NOTE:
# Specialized skills (e.g. Craft, Knowledge, Perform, Profession)
# are represented by multiple sub-values in D&D 3.x.
#
# During flattening, the highest specialization value is used as
# the representative value of the skill category.
#
# This avoids diluting meaningful expertise through averaging.
# A creature with high specialization in a specific field should retain
# that level of proficiency when converted into the target system,
# where these specializations are not modeled separately.
#
# Example:
# Knowledge:
#   arcana = 12
#   nature = 4
#   religion = 6
#
# becomes:
#   Knowledge = 12
