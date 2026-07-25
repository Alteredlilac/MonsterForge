"""
Tests for Power, Manifester, and Psionics — the psionic counterparts
to Spell/Spellcaster/Spellcasting.
"""
from monsterforge.structured_data.dnd.v3x.psionic_powers import (
    ManifestingTimeValue, PowerLevel, Power, Manifester, Psionics,
)
from monsterforge.structured_data.dnd.v3x.enums import PsionicDiscipline, CastingTime


def test_power_minimal_creation():
    power = Power(
        name="Mind Thrust", discipline=PsionicDiscipline.TELEPATHY,
        level=[PowerLevel(manifester_class="psion", level=2)],
        manifesting_time=ManifestingTimeValue(unit=CastingTime.STANDARD_ACTION),
        effect_description="x", long_description="x",
        power_points=3,
    )
    assert power.name == "Mind Thrust"
    assert power.discipline == PsionicDiscipline.TELEPATHY
    assert power.power_points == 3
    assert power.power_resistance is True  # default


def test_power_with_damage(make_damage):
    power = Power(
        name="Energy Ray", discipline=PsionicDiscipline.PSYCHOKINESIS,
        level=[PowerLevel(manifester_class="psion", level=1)],
        manifesting_time=ManifestingTimeValue(unit=CastingTime.STANDARD_ACTION),
        effect_description="x", long_description="x",
        power_points=1, damages=[make_damage()],
    )
    assert len(power.damages) == 1


def test_manifester_class_defaults_to_none():
    manifester = Manifester()
    assert manifester.manifester_class is None


def test_psionics_is_psionic_false_without_level():
    psionics = Psionics()
    assert psionics.is_psionic is False


def test_psionics_is_psionic_true_with_positive_level():
    psionics = Psionics(manifester_level=4)
    assert psionics.is_psionic is True


def test_psionics_inherits_manifester():
    psionics = Psionics(manifester_level=2, manifester_class="psion")
    assert isinstance(psionics, Manifester)
    assert psionics.manifester_class == "psion"


def test_psionics_with_known_powers():
    power = Power(
        name="Mind Thrust", discipline=PsionicDiscipline.TELEPATHY,
        level=[PowerLevel(manifester_class="psion", level=2)],
        manifesting_time=ManifestingTimeValue(unit=CastingTime.STANDARD_ACTION),
        effect_description="x", long_description="x", power_points=3,
    )
    psionics = Psionics(manifester_level=5, powers_known=[power])
    assert len(psionics.powers_known) == 1
    assert psionics.powers_known[0].name == "Mind Thrust"
