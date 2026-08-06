"""
Tests for Body/Spirit ability resolution and normalization.
"""
from monsterforge.transformation.dnd.v3x.calculations.body_spirit import (
    dnd_ability_from_body_stat, dnd_ability_from_spirit_stat,
    should_use_charisma_for_power, normalize_ability_stat,
)
from monsterforge.structured_data.dnd.v3x.enums import Ability, CreatureType
from monsterforge.domain.enums import BodyStat, SpiritStat


# =====================
# BODY STAT -> ABILITY
# =====================
def test_default_body_stat_mapping():
    assert dnd_ability_from_body_stat(
        body_stat=BodyStat.ATTACK,
        creature_type=CreatureType.ANIMAL) == Ability.STRENGTH
    assert dnd_ability_from_body_stat(
        body_stat=BodyStat.DEFENSE,
        creature_type=CreatureType.ANIMAL) == Ability.CONSTITUTION


def test_undead_uses_dexterity_for_defense():
    """Undead creatures use Dexterity instead of Constitution for
    Defense, since they typically lack a Constitution score."""
    result = dnd_ability_from_body_stat(
        body_stat=BodyStat.DEFENSE,
        creature_type=CreatureType.UNDEAD)
    assert result == Ability.DEXTERITY


def test_construct_uses_strength_for_defense():
    result = dnd_ability_from_body_stat(
        body_stat=BodyStat.DEFENSE,
        creature_type=CreatureType.CONSTRUCT)
    assert result == Ability.STRENGTH


def test_undead_attack_and_speed_unaffected_by_override():
    """The undead override changes Defense only; Attack/Speed stay
    on the default mapping."""
    attack = dnd_ability_from_body_stat(
        body_stat=BodyStat.ATTACK,
        creature_type=CreatureType.UNDEAD)
    assert attack == Ability.STRENGTH


# =====================
# SPIRIT STAT -> ABILITY
# =====================
def test_default_spirit_stat_mapping():
    assert dnd_ability_from_spirit_stat(
        spirit_stat=SpiritStat.POWER) == Ability.INTELLIGENCE
    assert dnd_ability_from_spirit_stat(
        spirit_stat=SpiritStat.FLOW) == Ability.CHARISMA


# =====================
# CHARISMA OVERRIDE RULE
# =====================
def test_charisma_replaces_intelligence_for_spellcasters():
    result = should_use_charisma_for_power(
        creature_intelligence=8, creature_charisma=16,
        is_spellcaster=True, is_psionic=False,
    )
    assert result is True


def test_charisma_override_requires_spellcaster_or_psionic():
    """A high Charisma alone is not enough — the creature must also
    be a spellcaster or psionic."""
    result = should_use_charisma_for_power(
        creature_intelligence=8, creature_charisma=16,
        is_spellcaster=False, is_psionic=False,
    )
    assert result is False


def test_charisma_override_requires_a_meaningful_gap():
    """Charisma must exceed Intelligence by more than 3 to trigger
    the override."""
    result = should_use_charisma_for_power(
        creature_intelligence=14, creature_charisma=16,
        is_spellcaster=True, is_psionic=False,
    )
    assert result is False


def test_charisma_override_applies_for_psionic_creatures_too():
    result = should_use_charisma_for_power(
        creature_intelligence=8, creature_charisma=16,
        is_spellcaster=False, is_psionic=True,
    )
    assert result is True


# =====================
# ABILITY NORMALIZATION
# =====================
def test_normalize_ability_stat_uses_dnd_modifier_formula():
    assert normalize_ability_stat(18) == 4
    assert normalize_ability_stat(12) == 1


def test_normalize_ability_stat_negative_modifier_clamped_to_zero():
    assert normalize_ability_stat(9) == 0
    assert normalize_ability_stat(3) == 0
    