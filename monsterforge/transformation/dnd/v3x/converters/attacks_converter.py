"""
Convert D&D 3.x structured attack data into MonsterForge MoveCard objects.

This module transforms fully structured D&D 3.x attack definitions into
domain-level MoveCard instances.

The conversion process includes:

- damage resolution through the damage resolver dispatch table
- resource assignment based on the structured move type
- range extraction and unit conversion
- conversion of special attack effects into additional cards
- mapping of structured attack attributes into the corresponding
  MoveCard fields

Semantic classification is not performed in this module. Fields such as
the move type and description are expected to have already been resolved
during the structured conversion / semantic classification stages and are
read directly from the structured Attack object.

The module also validates attack configurations that are inconsistent
with the expected D&D 3.x attack structure.

Design notes:

- Attacks without damage are treated as special attacks rather than standard
  attacks, e.g. the aranea's web attack and the stirge's attach attack.

- Attacks composed of multiple attacks are treated as multiple attacks and are
  handled by the full_attacks_converter module.

- The conversion is deterministic and does not perform LLM calls. Any semantic
  interpretation required to construct the structured Attack is completed
  before this module is invoked.
"""
# NOTE:
# TypedDict is used here instead of dataclass because these types represent
# temporary data exchanged between conversion helpers. They do not carry
# behavior, identity, or domain invariants, so a typed dictionary is sufficient.


from typing import TypedDict
from monsterforge.structured_data.dnd.v3x.attacks import Attack
from monsterforge.domain.cards import Card
from monsterforge.domain.moves import MoveCard, MoveEffect
from monsterforge.structured_data.dnd.v3x.enums import UnitSystem
from monsterforge.domain.enums import (MoveCategory,
                                       MoveMode,
                                       EffectType,
                                       EntityEffect,
                                       MoveType,
                                       Target,
                                       Duration,
                                       Usage,
                                       Resource,
                                       MoveRange,)
from monsterforge.transformation.dnd.v3x.calculations.general_math import feet_to_meters
from .damages_converter import damage_category, DAMAGE_RESOLVERS
from .special_attacks_converter import special_attack_converter


# =====================
# ERRORS
# =====================
class InvalidAttackConfigurationError(ValueError):
    pass


# =====================
# DAMAGES HELPER
# =====================
def extract_attack_damages(attack: Attack) -> list[MoveEffect]:
    """
    Convert all damage entries from a D&D 3.x attack into MoveEffect objects.

    Each damage entry is classified and resolved using the corresponding
    damage resolver. Multiple damage entries and multiple effects per entry
    are preserved in the resulting list.

    Returns:
        A list of MoveEffect objects representing all damage effects
        associated with the attack.
    """
    attack_effects = []

    for damage in attack.damages:
        resolver = DAMAGE_RESOLVERS[damage_category(damage)]
        attack_effects.extend(resolver(damage))

    return attack_effects

# =====================
# RESOURCE HELPER
# =====================
def attack_resource_type(move_type: MoveType) -> Resource:
    """
    Determine the resource associated with an attack type.

    Physical attacks use stamina, magical attacks use mana, and
    unsupported move types default to no resource.

    Args:
        move_type: The type of move being converted.

    Returns:
        The resource consumed by the move.
    """
    if move_type == MoveType.PHYSICAL:
        return Resource.STAMINA
    if move_type == MoveType.MAGICAL:
        return Resource.MANA

    return Resource.NONE

# =====================
# ATTACK RANGE HELPER
# =====================
class ExtractedAttackRange(TypedDict):
    range_value: int | None
    move_range: MoveRange | None

def extract_attack_range(attack:Attack) -> ExtractedAttackRange:
    """
    Extract the range information from a D&D 3.x attack.

    Melee attacks have no explicit range and return empty range values.
    Ranged attacks must define an attack range; metric values are preserved,
    while non-metric values are converted to meters.

    Raises:
        InvalidAttackConfigurationError:
            If a ranged attack does not define an attack range.

    Returns:
        A dictionary containing the move range type and range value.
    """
    if not attack.melee and attack.attack_range:
        move_range=  MoveRange.RANGED
        range_value= attack.attack_range.effect_range
        unit_system= attack.attack_range.range_unit_system 
        if unit_system == UnitSystem.METRIC:
            return {"range_value": range_value, "move_range": move_range} 
        
        return {"range_value": feet_to_meters(range_value), "move_range": move_range}

    if not attack.melee and not attack.attack_range:
            raise InvalidAttackConfigurationError(
                "Ranged attacks must define an attack_range")
    
    return {"range_value": None, "move_range": None}    


# =====================
# SPECIAL ATTACKS HELPER
# =====================
class SpecialAttackEffects(TypedDict, total=False):
    entity_effect: list[EntityEffect]
    cards_to_add: list[Card]

def extract_special_attacks(attack:Attack) -> SpecialAttackEffects:
    """
    Extract special attack effects from a D&D 3.x attack definition.

    Converts structured special effects into domain attributes:
    - entity effects indicating that the attack affects the creature's moves
    - cards generated from the special effect conversion

    For example, an attack such as a bite dealing 1d6+3 damage
    and granting a trip attack is converted into a normal attack
    card plus an additional special attack card representing the
    trip ability.

    Returns:
    A dictionary containing:
    - "entity_effect": always set to [EntityEffect.MOVES], indicating that
      the attack modifies or grants move-related effects
    - "cards_to_add": list of generated special attack cards

    Returns an empty dictionary if the attack has no special effects.
    """
    if attack.effects:
        return {"entity_effect": [EntityEffect.MOVES], 
                "cards_to_add": [special_attack_converter(effect) 
                                 for effect in attack.effects]}
    # NOTE:
    # EntityEffect.MOVES indicates that the effect modifies or grants
    # additional moves or move-related effects to the creature.

    return {}


# =====================
# DESCRIPTION 	 
# =====================
def augment_attack_description(
    description: str,
    touch: bool,
    ) -> str:
    """If Attack.touch is True, the MoveCard description should also state
    that this attack grants a +2 attack-roll bonus when used."""
    if touch:
        return f"{description} This attack grants a +2 attack-roll bonus when used."

    return description

# =====================
# ATTACK CONVERTER
# =====================
def attack_converter(
        attack: Attack,
        attack_image_uri: str | None = None) -> MoveCard:
    """
    Convert a D&D 3.x structured attack definition into a MoveCard.

    Resolves the attack's damage, range, resource type, and special
    effects using the corresponding conversion helpers.

    Args:
        attack: Structured D&D 3.x attack definition.
        attack_image_uri: Optional URI for the attack card image.

    Returns:
        A fully constructed MoveCard representing the attack.
    """

    return MoveCard(
        # Card class attributes
        name=  attack.name,
        description= augment_attack_description(
                    attack.description,
                    attack.touch,
                ),
        image_uri= attack_image_uri,

        # MoveCard attributes
        move_type= attack.move_type,   

        # default attributes
        category= MoveCategory.ATTACK,   
        mode= MoveMode.ACTIVE,            
        effect= EffectType.DAMAGE,        
        target= Target.SINGLE,             
        duration= Duration.INSTANT,         
        usage= Usage.UNLIMITED,              

        # derived attributes
        move_effects = extract_attack_damages(attack),   
        **extract_attack_range(attack),
        resource= attack_resource_type(attack.move_type),

        # bonus effects: 
        **extract_special_attacks(attack)        
        )
