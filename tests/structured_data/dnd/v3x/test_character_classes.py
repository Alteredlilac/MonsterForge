"""
Tests for ClassPrivilege, CharacterClass, and PrestigeClass.
"""
from monsterforge.structured_data.dnd.v3x.character_classes import (
    ClassPrivilege, CharacterClass, PrestigeClass,
)
from monsterforge.structured_data.dnd.v3x.feats import Feat, SaveRequirement
from monsterforge.structured_data.dnd.v3x.enums import (
    ClassPrivilegeType, DiceType, SaveProgression, CreatureType, SavingThrowType,
)


def _make_class(cls=CharacterClass, **overrides):
    defaults = dict(
        name="Rogue", description="A skilled scoundrel", hit_die=DiceType.D6,
        total_levels=20, fortitude_save=SaveProgression.POOR,
        reflex_save=SaveProgression.GOOD, will_save=SaveProgression.POOR,
    )
    defaults.update(overrides)
    return cls(**defaults)


def test_character_class_minimal_creation():
    rogue = _make_class()
    assert rogue.name == "Rogue"
    assert rogue.reflex_save == SaveProgression.GOOD
    assert rogue.privileges == {}


def test_character_class_auto_generates_unique_id():
    c1 = _make_class()
    c2 = _make_class()
    assert c1.id != c2.id


def test_character_class_base_attack_bonus_optional():
    rogue = _make_class()
    assert rogue.base_attack_bonus is None


def test_spellcasting_progression_none_without_max_spell_level():
    fighter = _make_class(name="Fighter")
    assert fighter.spellcasting_progression is None


def test_spellcasting_progression_low_for_level_4_or_less():
    cls = _make_class(max_spell_level=4)
    assert cls.spellcasting_progression.value == "low"


def test_spellcasting_progression_medium_for_level_5_to_7():
    cls = _make_class(max_spell_level=6)
    assert cls.spellcasting_progression.value == "medium"


def test_spellcasting_progression_high_for_level_8_or_9():
    cls = _make_class(max_spell_level=9)
    assert cls.spellcasting_progression.value == "high"


def test_class_privilege_can_grant_heterogeneous_content():
    feat = Feat(name="Sneak Attack", description="x")
    privilege = ClassPrivilege(
        name="Sneak Attack", granted_at_level=1, description="x",
        privilege_type=ClassPrivilegeType.FEAT, granted_privilege=feat,
    )
    assert privilege.granted_privilege is feat


def test_character_class_with_privileges_by_level():
    feat = Feat(name="Evasion", description="x")
    privilege = ClassPrivilege(
        name="Evasion", granted_at_level=2, description="x",
        privilege_type=ClassPrivilegeType.FEAT, granted_privilege=feat,
    )
    rogue = _make_class(privileges={2: [privilege]})
    assert rogue.privileges[2][0].name == "Evasion"


def test_prestige_class_inherits_character_class():
    assassin = _make_class(cls=PrestigeClass, name="Assassin", total_levels=10)
    assert isinstance(assassin, CharacterClass)
    assert assassin.name == "Assassin"


def test_prestige_class_requirements_default_to_empty():
    assassin = _make_class(cls=PrestigeClass, name="Assassin", total_levels=10)
    assert assassin.required_feats == []
    assert assassin.required_alignment == []
    assert assassin.required_abilities is None


def test_prestige_class_with_save_requirements():
    """required_saves models per-save-type minimums (e.g. only Fort +4),
    not a full Saves triple — a prestige class need not require all
    three saves at once."""
    assassin = _make_class(
        cls=PrestigeClass, name="Assassin", total_levels=10,
        required_saves=[
            SaveRequirement(save_type=SavingThrowType.FORTITUDE, minimum_value=4),
        ],
    )
    assert len(assassin.required_saves) == 1
    assert assassin.required_saves[0].minimum_value == 4


def test_prestige_class_with_creature_type_requirement():
    fiend_blooded = _make_class(
        cls=PrestigeClass, name="Fiend-Blooded", total_levels=10,
        required_creature_type=CreatureType.HUMANOID,
    )
    assert fiend_blooded.required_creature_type == CreatureType.HUMANOID
