"""
Tests for the ClericDomain model.
"""
from monsterforge.structured_data.dnd.v3x.cleric_domains import ClericDomain
from monsterforge.structured_data.dnd.v3x.spells import Spell, SpellLevel, CastingTimeValue
from monsterforge.structured_data.dnd.v3x.feats import Feat
from monsterforge.structured_data.dnd.v3x.enums import MagicSchool, CastingTime


def test_cleric_domain_minimal_creation():
    domain = ClericDomain(name="Fire Domain")
    assert domain.name == "Fire Domain"
    assert domain.granted_power is None
    assert domain.domain_spells == []


def test_cleric_domain_auto_generates_unique_id():
    d1 = ClericDomain(name="Fire Domain")
    d2 = ClericDomain(name="Fire Domain")
    assert d1.id != d2.id


def test_cleric_domain_can_grant_heterogeneous_content():
    """granted_power accepts any of the GrantedPower union members —
    here a Feat, but a Spell/Item/Companion etc. would work identically."""
    feat = Feat(name="Fire Resistance", description="x")
    domain = ClericDomain(name="Fire Domain", granted_power=feat)
    assert domain.granted_power is feat


def test_cleric_domain_with_domain_spells():
    fireball = Spell(
        name="Fireball", scuola=MagicSchool.EVOCATION,
        level=[SpellLevel(caster_class="cleric", level=3)],
        casting_time=CastingTimeValue(unit=CastingTime.STANDARD_ACTION),
        effect_description="x", long_description="x",
    )
    domain = ClericDomain(name="Fire Domain", domain_spells=[fireball])
    assert domain.domain_spells[0].name == "Fireball"
