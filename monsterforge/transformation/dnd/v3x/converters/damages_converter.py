"""
Convert D&D 3.x structured damage data into MonsterForge MoveEffect objects.

This module interprets structured damage definitions (dice, modifiers,
and ability drain) and resolves them into one or more domain-level
MoveEffect instances.

It handles multiple damage combinations, including:
- dice-based damage
- flat modifiers
- ability damage (energy drain)
- mixed damage types

The conversion process includes normalization, defaulting rules,
and domain-specific validation.

Notes:
- Default damage types are applied when missing
    - physical damage for standard damage
    - energy drain for ability damage
- Mixed damage types may produce multiple MoveEffect instances
- Invalid combinations raise a domain-specific error
"""
from monsterforge.domain.moves import MoveEffect
from monsterforge.structured_data.dnd.v3x.dice_effects import Damage
from monsterforge.structured_data.dnd.v3x.enums import DiceType, DamageType, Ability
from monsterforge.rules.dnd.v3x.enum_mapping import (DAMAGE_TYPE_MAPPING,
                                                     ABILITY_DAMAGE_MAPPING)
from monsterforge.transformation.dnd.v3x.calculations.general_rules import normalize_damage, normalize_drained_ability
from monsterforge.transformation.dnd.v3x.calculations.general_math import halve_value

# =====================
# HELPERS
# =====================
def dice_sum(num_of_dice: int, type_of_dice= DiceType):
    """
    Resolve the numeric value of a D&D 3.x dice damage component.

    Missing dice count values are treated as a single die, following
    the default behavior used during damage conversion.
    Values below one die are considered invalid.
    """
    if num_of_dice is None:
        num = 1
    elif num_of_dice <= 0:
        raise ValueError("num_of_dice must be >= 1")
    else:
        num = num_of_dice

    return normalize_damage(dice_type= type_of_dice, num_dice=num)


# =====================
# DAMAGE CATEGORY
# =====================
def damage_category(damage: Damage) -> str:
    """
    Classify a D&D 3.x damage definition into a resolver category.

    The returned key identifies which combination of damage components
    is present (dice, ability damage, modifiers, or none) and is used
    by the damage resolver dispatch table.
    """
    has_dice = damage.dice_type is not None
    has_drain = damage.affected_ability is not None
    has_modifier = damage.damage_bonus is not None

    if has_dice and has_drain and has_modifier:
        return "dice_drain_modifier"

    if has_dice and has_drain:
        return "dice_drain"

    if has_drain and has_modifier:
        return "drain_modifier"

    if has_dice and has_modifier:
        return "dice_modifier"

    if has_dice:
        return "dice"

    if has_drain:
        return "drain"

    if has_modifier:
        return "modifier"

    return "none"


# =====================
# RESOLVER FUNCTIONS
# =====================

def resolve_dice_drain_modifier(d: Damage)-> list[MoveEffect]:
    """
    Resolve damage definitions containing dice, ability damage,
    and a flat modifier.

    Depending on the damage type combination, this may produce one
    or multiple MoveEffect instances.

    Raises:
        InvalidDamageConfigurationError:
            if the damage definition cannot be resolved
    """
    num_of_dice = d.dice_number
    type_of_dice= d.dice_type
    dice_damages_type = d.damage_type or DamageType.ENERGY_DRAIN
    # drained ability 
    drained_ability = d.affected_ability
    # modifier
    damage_modifier= d.damage_bonus
    type_of_damage_modifier= d.damage_bonus_type or DamageType.ENERGY_DRAIN
    # NOTE:
    # If the damage type is not specified, it is considered
    # ENERGY_DRAIN for ability damage resolution.     

    dice_value = dice_sum(num_of_dice= num_of_dice, type_of_dice= type_of_dice)

    # Case 1: dice damage and modifier share the ENERGY_DRAIN type
    # e.g. 1d6 + 1 Dexterity damage
    if dice_damages_type == type_of_damage_modifier:
        # MoveEffect
        damage_type = dice_damages_type        
        effect_unit = ABILITY_DAMAGE_MAPPING[drained_ability]
        effect_value = normalize_drained_ability(dice_value + damage_modifier)

        return [MoveEffect(
            damage_type= DAMAGE_TYPE_MAPPING[damage_type],
            effect_unit= effect_unit,
            effect_value= effect_value)]
    
    # Case 2: dice-based ability damage combined with a different modifier damage type
    # e.g. 1d4 Strength damage +2 fire damage
    if dice_damages_type == DamageType.ENERGY_DRAIN:
        return [MoveEffect( 
                    damage_type= DAMAGE_TYPE_MAPPING[dice_damages_type],
                    effect_unit= effect_unit,
                    effect_value= normalize_drained_ability(dice_value)),
                MoveEffect(
                    damage_type= DAMAGE_TYPE_MAPPING[type_of_damage_modifier],
                    effect_value= damage_modifier)
                    ]

    # Case 3: modifier applies as ability damage and dice use a different damage type
    # e.g. 1d8 physical damage +2 Charisma damage
    if type_of_damage_modifier == DamageType.ENERGY_DRAIN:
        return [MoveEffect( 
                    damage_type= DAMAGE_TYPE_MAPPING[dice_damages_type],
                    effect_value= dice_value),
                MoveEffect(# risucchio su modifier caso 2
                    damage_type= DAMAGE_TYPE_MAPPING[type_of_damage_modifier],
                    effect_unit= effect_unit,
                    effect_value= halve_value(damage_modifier))
                    ]

    # Case 4: neither dice damage nor modifier damage resolves as ENERGY_DRAIN
    raise InvalidDamageConfigurationError(
    "Invalid damage configuration: at least one of dice damage type "
    "or modifier damage type must be ENERGY_DRAIN"
    )

def resolve_dice_drain(d: Damage)-> list[MoveEffect]:
    """
    Resolve dice-based ability damage into a MoveEffect.

    Missing damage types are interpreted as ENERGY_DRAIN.
    """
    num_of_dice = d.dice_number 
    type_of_dice= d.dice_type 
    dice_damages_type = d.damage_type or DamageType.ENERGY_DRAIN
    # drained ability 
    drained_ability = d.affected_ability 
    # NOTE:
    # If the damage type is not specified, it is considered
    # ENERGY_DRAIN for ability damage resolution. 
     
    dice_value = dice_sum(num_of_dice= num_of_dice, type_of_dice= type_of_dice)  

    # MoveEffect
    damage_type = dice_damages_type
    effect_unit = ABILITY_DAMAGE_MAPPING[drained_ability]
    effect_value = normalize_drained_ability(dice_value)

    return [MoveEffect(
        damage_type= damage_type,
        effect_unit= effect_unit,
        effect_value= effect_value)]

def resolve_drain_modifier(d: Damage)-> list[MoveEffect]:
    """
    Resolve flat ability damage caused by an energy drain effect.

    The modifier value is normalized according to MonsterForge rules.
    """ 
    drained_ability = d.affected_ability
    # modifier
    damage_modifier= d.damage_bonus 
    type_of_damage_modifier= d.damage_bonus_type or DamageType.ENERGY_DRAIN 
    # NOTE:
    # If the damage type is not specified, it is considered
    # ENERGY_DRAIN for ability damage resolution.   

    
    damage_type = DAMAGE_TYPE_MAPPING[type_of_damage_modifier]
    effect_unit = ABILITY_DAMAGE_MAPPING[drained_ability]
    effect_value = halve_value(damage_modifier)

    return [MoveEffect(
        damage_type= damage_type,
        effect_unit= effect_unit,
        effect_value= effect_value)]

def resolve_dice_modifier(d: Damage)-> list[MoveEffect]:
    """
    Resolve dice damage combined with a flat damage modifier.

    Produces a single MoveEffect when both components share the same
    damage type, otherwise returns separate effects.
    """
    # dice
    num_of_dice = d.dice_number       
    type_of_dice= d.dice_type  
    dice_damages_type = d.damage_type or DamageType.PHYSICAL
    # modifier
    damage_modifier= d.damage_bonus     
    type_of_damage_modifier= d.damage_bonus_type or DamageType.PHYSICAL
    # NOTE:
    # Missing damage type is interpreted as PHYSICAL damage.  

    dice_value = dice_sum(num_of_dice= num_of_dice, type_of_dice= type_of_dice)

    # Case 1: dice damage and modifier share the same damage type
    # e.g. 2d4+5 fire damage, 1d8+3 physical damage
    if dice_damages_type == type_of_damage_modifier:
        # MoveEffect
        damage_type = dice_damages_type        

        effect_value = dice_value + damage_modifier

        return [MoveEffect(
            damage_type= DAMAGE_TYPE_MAPPING[damage_type],
            effect_value= effect_value)]

    # Case 2: dice damage combined with a different modifier damage type
    # e.g. 1d4 bludgeoning damage +1 acid damage
    return [MoveEffect(
                damage_type= DAMAGE_TYPE_MAPPING[dice_damages_type],
                effect_value= dice_value),
            MoveEffect(
                damage_type= DAMAGE_TYPE_MAPPING[type_of_damage_modifier],
                effect_value= damage_modifier)
                ]

def resolve_dice(d: Damage)-> list[MoveEffect]:
    """
    Resolve a dice-only damage definition into a MoveEffect.

    Missing damage types default to PHYSICAL damage.
    """
    num_of_dice = d.dice_number
    type_of_dice= d.dice_type
    dice_damages_type = d.damage_type or DamageType.PHYSICAL 
    # NOTE:
    # Missing damage type is interpreted as PHYSICAL damage.   

    # MoveEffect
    damage_type = dice_damages_type

    effect_value = dice_sum(num_of_dice= num_of_dice, type_of_dice= type_of_dice)
    
    return [MoveEffect(
        damage_type= DAMAGE_TYPE_MAPPING[damage_type],
        effect_value= effect_value)]

def resolve_modifier(d: Damage)-> list[MoveEffect]:
    """
    Resolve a flat damage modifier into a MoveEffect.

    Missing damage types default to PHYSICAL damage.
    """   
    damage_modifier= d.damage_bonus 
    type_of_damage_modifier= d.damage_bonus_type or DamageType.PHYSICAL
    # NOTE:
    # Missing damage type is interpreted as PHYSICAL damage.

    # MoveEffect
    damage_type = type_of_damage_modifier
    effect_value = damage_modifier

    return [MoveEffect(
        damage_type= DAMAGE_TYPE_MAPPING[damage_type],
        effect_value= effect_value)]

def resolve_drain(d: Damage)-> None:
    """
    Reject invalid drain-only damage definitions.

    Ability damage requires either dice or a numeric value.
    """
    raise InvalidDamageConfigurationError(
            "Drain damage requires either dice or a numeric value")

def resolve_no_values(d: Damage)-> list[MoveEffect]:
    """
    Return an empty MoveEffect for damage definitions without values.
    """
    return [MoveEffect()]

# =====================
# DAMAGE RESOLVER
# =====================
DAMAGE_RESOLVERS = {
    "dice_drain_modifier": resolve_dice_drain_modifier,
    "dice_drain": resolve_dice_drain,
    "drain_modifier": resolve_drain_modifier,
    "dice_modifier": resolve_dice_modifier,
    "dice": resolve_dice,
    "modifier": resolve_modifier,
    "drain": resolve_drain,
    "none": resolve_no_values,
}

# =====================
# ERRORS
# =====================
class InvalidDamageConfigurationError(ValueError):
    pass
