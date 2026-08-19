"""
Convert D&D 3.x special attack effects into MonsterForge MoveCard objects.

Unlike attacks_converter.py, this is a deliberately shallow conversion:
special attacks (e.g. "trip" granted by a bite, "poison" following a
sting) are parsed by attacks_effects_parser.py with no semantic
classification at all — only a bare name and a placeholder
special_ability_type (see get_special_attacks() NOTE). A full semantic
classification of these (comparable to feats/special qualities) is out
of scope for now, the same way FullAttack is: this module exists to give
such references a valid, presentable MoveCard (used via
attacks_converter.py's cards_to_add), not to interpret their real
mechanical effect.
"""
from monsterforge.structured_data.dnd.v3x.special_attacks import SpecialAttack
from monsterforge.domain.moves import MoveCard
from monsterforge.domain.enums import (MoveCategory,
                                       MoveMode,
                                       EffectType,
                                       Target,
                                       Resource,
                                       Duration,
                                       Usage)
from monsterforge.rules.dnd.v3x.enum_mapping import SPECIAL_ABILITY_TYPE_TO_MOVE_TYPE_MAPPING


def special_attack_converter(
        special_attack: SpecialAttack,
        special_attack_image_uri: str | None = None) -> MoveCard:
    """
    Convert a D&D 3.x special attack reference into a shallow MoveCard.

    NOTE:
    Every field below except name/description/move_type is a
    deliberately approximate default, not a semantic classification:
    - category=ATTACK follows DESIGN.md's own precedent ("Attacco
      Poderoso", a talent modifying an attack, is classified as Attacco,
      not Speciale — Speciale is reserved for "other methods").
    - mode=ACTIVE: these are maneuvers granted alongside an attack
      (trip, push...), something the attacker actively does, not a
      reactive/always-on trait.
    - effect=ENTITY, used in a generic sense ("affects the creature in
      general"), since the actual mechanical effect is unknown without
      real classification.
    """
    return MoveCard(
        name=special_attack.name.title(),
        description=(special_attack.description
                     or f"Additional effect: {special_attack.name}."),
        image_uri=special_attack_image_uri,
        move_type=SPECIAL_ABILITY_TYPE_TO_MOVE_TYPE_MAPPING[special_attack.special_ability_type],
        category=MoveCategory.ATTACK,
        mode=MoveMode.ACTIVE,
        effect=EffectType.ENTITY,
        target=Target.SINGLE,
        resource=Resource.NONE,
        duration=Duration.INSTANT,
        usage=Usage.UNLIMITED,
    )
