"""Converte special attacks in MoveCard"""
from monsterforge.structured_data.dnd.v3x.special_attacks import SpecialAttack
from monsterforge.domain.moves import MoveCard

def special_attack_converter(
        special_attack: SpecialAttack,
        special_attack_image_uri: str | None = None) -> MoveCard:
    ...