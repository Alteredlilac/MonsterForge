"""
Tests for Spell, Spellcaster, and Spellcasting.
"""
from monsterforge.structured_data.dnd.v3x.spells import (
    CastingTimeValue, SpellLevel, Spell, Spellcaster, Spellcasting,
)
from monsterforge.structured_data.dnd.v3x.enums import (
    MagicSchool, CastingTime, MagicType,
)


def test_casting_time_value_defaults_to_one():
    ctv = CastingTimeValue(unit=CastingTime.STANDARD_ACTION)
    assert ctv.amount == 1


def test_spell_level_creation():
    level = SpellLevel(caster_class="wizard", level=3)
    assert level.caster_class == "wizard"
    assert level.level == 3


def test_spell_minimal_creation():
    fireball = Spell(
        name="Fireball", school=MagicSchool.EVOCATION,
        level=[SpellLevel(caster_class="wizard", level=3)],
        casting_time=CastingTimeValue(unit=CastingTime.STANDARD_ACTION),
        effect_description="A burst of fire",
        long_description="A burst of fire deals damage in an area.",
    )
    assert fireball.name == "Fireball"
    assert fireball.school == MagicSchool.EVOCATION
    assert fireball.spell_resistance is True  # default


def test_spell_supports_multiclass_levels():
    """The same spell can appear at different levels for different
    caster classes (e.g. Cure Light Wounds: Clr 1, Pal 1)."""
    spell = Spell(
        name="Cure Light Wounds", school=MagicSchool.CONJURATION,
        level=[
            SpellLevel(caster_class="cleric", level=1),
            SpellLevel(caster_class="paladin", level=1),
        ],
        casting_time=CastingTimeValue(unit=CastingTime.STANDARD_ACTION),
        effect_description="x", long_description="x",
    )
    assert len(spell.level) == 2


def test_spell_with_damage_and_healing(make_damage, make_healing):
    spell = Spell(
        name="Chaos Bolt", school=MagicSchool.EVOCATION,
        level=[SpellLevel(caster_class="sorcerer", level=1)],
        casting_time=CastingTimeValue(unit=CastingTime.STANDARD_ACTION),
        effect_description="x", long_description="x",
        damages=[make_damage()], healing=[make_healing()],
    )
    assert len(spell.damages) == 1
    assert len(spell.healing) == 1


def test_spellcaster_fields_are_optional():
    caster = Spellcaster()
    assert caster.spellcasting_class is None
    assert caster.spellcasting_type is None


def test_spellcaster_with_type():
    caster = Spellcaster(spellcasting_type=MagicType.ARCANE)
    assert caster.spellcasting_type == MagicType.ARCANE


def test_spellcasting_is_spellcaster_false_when_no_caster_level():
    casting = Spellcasting()
    assert casting.is_spellcaster is False


def test_spellcasting_is_spellcaster_true_with_positive_level():
    casting = Spellcasting(caster_level=5)
    assert casting.is_spellcaster is True


def test_spellcasting_is_spellcaster_false_at_level_zero():
    casting = Spellcasting(caster_level=0)
    assert casting.is_spellcaster is False


def test_spellcasting_inherits_spellcaster():
    casting = Spellcasting(caster_level=3, spellcasting_type=MagicType.DIVINE)
    assert isinstance(casting, Spellcaster)
    assert casting.spellcasting_type == MagicType.DIVINE
