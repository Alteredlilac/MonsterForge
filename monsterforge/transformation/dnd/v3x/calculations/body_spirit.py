"""
Body and Spirit stat calculations for D&D 3.x transformation.

This module defines the rules used to resolve and normalize D&D 3.x
ability values into MonsterForge Body and Spirit stats.

Responsibilities:
- Resolve which D&D ability is associated with each Body or Spirit stat.
- Apply creature-specific exceptions (e.g. undead and constructs).
- Convert D&D ability scores into deterministic values used by
  MonsterForge Body and Spirit stats.

Rules:
- D&D ability modifiers are used as the source value for domain stats.
- Negative modifiers are treated as 0.
- Special creature rules may override default ability references.
- Charisma may replace Intelligence for Spirit Power for specific
  caster or psionic creatures.

Static mappings are defined in the rules package and consumed here.
This module applies transformation rules but does not define static
rule tables.
"""
from monsterforge.rules.dnd.v3x.body_spirit_mapping import (
    BODY_STAT_MAPPING,
    UNDEAD_BODY_STAT_MAPPING,
    CONSTRUCT_BODY_STAT_MAPPING,
    SPIRIT_STAT_MAPPING,
)
from monsterforge.structured_data.dnd.v3x.enums import Ability, CreatureType
from monsterforge.domain.enums import BodyStat, SpiritStat
from .general_math import floor_value


# =====================
# ABILITY FROM BODY STAT
# =====================
def dnd_ability_from_body_stat(*, body_stat: BodyStat, creature_type: CreatureType) -> Ability:
    """
    Resolve the D&D 3.x ability associated with a MonsterForge body stat.

    Applies creature-specific rules where some creature types use
    alternate ability references.

    Examples:
        BodyStat.ATTACK -> Ability.STRENGTH
        BodyStat.DEFENSE -> Ability.CONSTITUTION

    Undead and constructs use alternate rules for defense calculation.
    """  
    if creature_type == CreatureType.UNDEAD: 
       return Ability(UNDEAD_BODY_STAT_MAPPING[body_stat])

    if creature_type == CreatureType.CONSTRUCT:
       return Ability(CONSTRUCT_BODY_STAT_MAPPING[body_stat])
    
    return Ability(BODY_STAT_MAPPING[body_stat])

# NOTE:
# Incorporeal entities do not define Body Attack or Defense values.
# This special case is handled in the converter layer before calculation.


# =====================
# ABILITY FROM SPIRIT STAT
# =====================
def dnd_ability_from_spirit_stat(*, spirit_stat: SpiritStat) -> Ability:
    """
    Resolve the default D&D 3.x ability associated with a
    MonsterForge spirit stat.

    Examples:
        SpiritStat.POWER -> Ability.INTELLIGENCE
        SpiritStat.FLOW -> Ability.CHARISMA

    Special Spirit rules are handled by dedicated calculation functions.
    """
    return Ability(SPIRIT_STAT_MAPPING[spirit_stat])    


# =====================
# SPIRIT ALTERNATIVE RULES
# =====================
def should_use_charisma_for_power(
      *,
      creature_intelligence:int,
      creature_charisma:int,
      is_spellcaster:bool,
      is_psionic: bool ) -> bool:
    """
    Determine whether Charisma replaces Intelligence for Spirit Power.

    Rule:
    - Charisma replaces Intelligence when:
        - Charisma is greater than Intelligence by more than 3.
        - The creature is a spellcaster or psionic creature.

    Returns:
        True if the alternative rule applies, otherwise False.
    """
    return (
        creature_charisma > creature_intelligence + 3
        and (is_spellcaster or is_psionic)
    )

# NOTE:
# The converter layer (transformation/dnd/v3x/converters/)
# uses this rule to determine whether Spirit Power and Flow values
# should be swapped after the default Spirit calculation.


# =====================
# D&D ABILITY TO DOMAIN VALUE
# =====================
def normalize_ability_stat(dnd_ability_value: int)-> int:
    """
    Convert a D&D 3.x ability score into a normalized MonsterForge value.

    The normalized value is calculated using the D&D ability modifier
    formula and used as a deterministic domain feature.

    Rules:
    - Ability modifiers (not raw ability scores) are used as normalized values.
    - Negative results are treated as 0.

    Examples:
        18 -> 4
        12 -> 1
        9 -> 0
    """
    dnd_ability_modifier = floor_value((dnd_ability_value - 10) / 2)

    return max(0, dnd_ability_modifier)
