"""
Shared test fixtures for structured_data.dnd.v3x models.

Provides factory fixtures for the "building block" dataclasses reused
across many modules (Damage, Healing, EffectTarget, SavingThrow, ...),
so individual test files can build larger objects (Creature, Feat, Spell...)
without repeating boilerplate construction of their dependencies.

Each fixture returns a callable that allows overriding default values,
following the same pattern used in tests/domain/conftest.py.
"""
import pytest

from monsterforge.structured_data.dnd.v3x.enums import (
    DiceType, DamageType, SavingThrowType, Usage, Duration,
    AreaEffectShape, UnitSystem, TargetType, MovementMode,
    GrantedType,
)
from monsterforge.structured_data.dnd.v3x.dice_effects import (
    Dice, Damage, Healing, TimeExpression,
)
from monsterforge.structured_data.dnd.v3x.creature_stats import (
    HitDice, Movement, ArmorClass, Space, Reach, Abilities, Saves,
)
from monsterforge.structured_data.dnd.v3x.skills import Skills
from monsterforge.structured_data.dnd.v3x.effect_mechanics import (
    EffectRange, CriticalHit, SavingThrow, EffectDuration, EffectUsage,
    EffectArea, DamageOverTime, EffectTarget, EffectModifier, EffectGrant,
)
from monsterforge.structured_data.dnd.v3x.defenses import (
    DamageReduction, DamageResistance, Regeneration,
)


# =====================
# ENUM-BACKED BUILDING BLOCKS
# =====================
@pytest.fixture
def make_hit_dice():
    def _make(**overrides):
        defaults = dict(num_hit_dice=2, hit_dice_type=DiceType.D8)
        defaults.update(overrides)
        return HitDice(**defaults)
    return _make


@pytest.fixture
def make_movement():
    def _make(**overrides):
        defaults = dict(
            movement_speed=9, unit_system=UnitSystem.METRIC,
            movement_type=MovementMode.LAND,
        )
        defaults.update(overrides)
        return Movement(**defaults)
    return _make


@pytest.fixture
def make_armor_class():
    def _make(**overrides):
        defaults = dict(armor_class=14, flat_footed_ac=12, touch_ac=12)
        defaults.update(overrides)
        return ArmorClass(**defaults)
    return _make


@pytest.fixture
def make_space():
    def _make(**overrides):
        defaults = dict(space=1, unit_system=UnitSystem.METRIC)
        defaults.update(overrides)
        return Space(**defaults)
    return _make


@pytest.fixture
def make_reach():
    def _make(**overrides):
        defaults = dict(reach=1, unit_system=UnitSystem.METRIC)
        defaults.update(overrides)
        return Reach(**defaults)
    return _make


@pytest.fixture
def make_abilities():
    def _make(**overrides):
        defaults = dict(
            strength=13, dexterity=15, constitution=15,
            intelligence=2, wisdom=12, charisma=6,
        )
        defaults.update(overrides)
        return Abilities(**defaults)
    return _make


@pytest.fixture
def make_saves():
    def _make(**overrides):
        defaults = dict(fortitude_save=3, reflex_save=3, will_save=1)
        defaults.update(overrides)
        return Saves(**defaults)
    return _make


@pytest.fixture
def make_skills():
    """Factory fixture returning a function to create Skills test instances."""
    def _make(**overrides):
        return Skills(**overrides)
    return _make


# =====================
# DICE EFFECTS
# =====================
@pytest.fixture
def make_dice():
    def _make(**overrides):
        defaults = dict(dice_number=1, dice_type=DiceType.D6, modifier=None)
        defaults.update(overrides)
        return Dice(**defaults)
    return _make


@pytest.fixture
def make_damage():
    def _make(**overrides):
        defaults = dict(
            dice_number=1, dice_type=DiceType.D6,
            damage_type=DamageType.PHYSICAL,
        )
        defaults.update(overrides)
        return Damage(**defaults)
    return _make


@pytest.fixture
def make_healing():
    def _make(**overrides):
        defaults = dict(dice_number=1, dice_type=DiceType.D8)
        defaults.update(overrides)
        return Healing(**defaults)
    return _make


@pytest.fixture
def make_time_expression():
    def _make(**overrides):
        defaults = dict(unit=None, dice_number=1, dice_type=DiceType.D4)
        defaults.update(overrides)
        return TimeExpression(**defaults)
    return _make


# =====================
# EFFECT MECHANICS
# =====================
@pytest.fixture
def make_effect_range():
    def _make(**overrides):
        defaults = dict(effect_range=9, range_unit_system=UnitSystem.METRIC)
        defaults.update(overrides)
        return EffectRange(**defaults)
    return _make


@pytest.fixture
def make_critical_hit():
    def _make(**overrides):
        defaults = dict(critical_threat_min=20, critical_multiplier=2)
        defaults.update(overrides)
        return CriticalHit(**defaults)
    return _make


@pytest.fixture
def make_saving_throw():
    def _make(**overrides):
        defaults = dict(
            saving_throw_type=SavingThrowType.REFLEX,
            saving_throw_value=15,
        )
        defaults.update(overrides)
        return SavingThrow(**defaults)
    return _make


@pytest.fixture
def make_effect_duration():
    def _make(**overrides):
        defaults = dict(duration=Duration.INSTANT)
        defaults.update(overrides)
        return EffectDuration(**defaults)
    return _make


@pytest.fixture
def make_effect_usage():
    def _make(**overrides):
        defaults = dict(usage=Usage.UNLIMITED)
        defaults.update(overrides)
        return EffectUsage(**defaults)
    return _make


@pytest.fixture
def make_effect_area():
    def _make(**overrides):
        defaults = dict(
            area_size=6, area_unit_system=UnitSystem.METRIC,
            area_shape=AreaEffectShape.BURST,
        )
        defaults.update(overrides)
        return EffectArea(**defaults)
    return _make


@pytest.fixture
def make_damage_over_time(make_time_expression, make_damage):
    def _make(**overrides):
        defaults = dict(
            damage_frequency=make_time_expression(),
            damages=[make_damage()],
        )
        defaults.update(overrides)
        return DamageOverTime(**defaults)
    return _make


@pytest.fixture
def make_effect_target():
    def _make(**overrides):
        defaults = dict(target_type=TargetType.CREATURE)
        defaults.update(overrides)
        return EffectTarget(**defaults)
    return _make


@pytest.fixture
def make_effect_modifier():
    def _make(**overrides):
        from monsterforge.structured_data.dnd.v3x.enums import ModifierTarget
        defaults = dict(target=ModifierTarget.ABILITY_SCORE, modifier=2)
        defaults.update(overrides)
        return EffectModifier(**defaults)
    return _make


@pytest.fixture
def make_effect_grant():
    def _make(**overrides):
        defaults = dict(
            grant_type=GrantedType.CREATURE, amount=1,
            description="Grants something",
        )
        defaults.update(overrides)
        return EffectGrant(**defaults)
    return _make


# =====================
# DEFENSES
# =====================
@pytest.fixture
def make_damage_reduction():
    def _make(**overrides):
        defaults = dict(reduction_value=5, bypass_type="magic")
        defaults.update(overrides)
        return DamageReduction(**defaults)
    return _make


@pytest.fixture
def make_damage_resistance():
    def _make(**overrides):
        defaults = dict(damage_type=DamageType.FIRE, resistance_value=10)
        defaults.update(overrides)
        return DamageResistance(**defaults)
    return _make


@pytest.fixture
def make_regeneration():
    def _make(**overrides):
        defaults = dict(regeneration_value=5)
        defaults.update(overrides)
        return Regeneration(**defaults)
    return _make


# =====================
# CREATURE (full aggregate)
# =====================
@pytest.fixture
def make_creature(make_armor_class, make_space, make_reach, make_saves,
                   make_abilities, make_skills):
    """
    Factory for a minimal but complete Creature (a "Wolf"-like baseline),
    reused by tests in creatures.py, companions.py, and cleric_domains.py
    that need a valid Creature as a dependency rather than as the main
    subject under test.
    """
    def _make(**overrides):
        from monsterforge.structured_data.dnd.v3x.creatures import Creature
        from monsterforge.structured_data.dnd.v3x.enums import (
            CreatureType, Size, Alignment,
        )
        defaults = dict(
            name="Wolf", creature_type=CreatureType.ANIMAL, creature_size=Size.MEDIUM,
            description="A wild wolf", hit_points_total=23, hit_point_bonus=0,
            initiative=2, armor_class=make_armor_class(),
            base_attack=2, grapple=3,
            space=make_space(), reach=make_reach(),
            saves=make_saves(), abilities=make_abilities(),
            skills=make_skills(),
            challenge_rating="1", alignment=Alignment.NEUTRAL,
        )
        defaults.update(overrides)
        return Creature(**defaults)
    return _make
