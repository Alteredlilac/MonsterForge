"""
Tests for CreaturePrivilege and Companion.
"""
from monsterforge.structured_data.dnd.v3x.companions import CreaturePrivilege, Companion
from monsterforge.structured_data.dnd.v3x.feats import Feat
from monsterforge.structured_data.dnd.v3x.enums import CompanionPrivilegeType


def test_creature_privilege_minimal_creation():
    feat = Feat(name="Alertness", description="x")
    privilege = CreaturePrivilege(
        name="Alertness", granted_at_level=1, description="x",
        privilege_type=CompanionPrivilegeType.FEAT,
        granted_privilege=feat,
    )
    assert privilege.name == "Alertness"
    assert privilege.privilege_type == CompanionPrivilegeType.FEAT
    assert privilege.granted_privilege is feat


def test_companion_minimal_creation(make_creature):
    base = make_creature()
    familiar = Companion(name="Raven", base_creature=base, total_levels=20)
    assert familiar.name == "Raven"
    assert familiar.base_creature is base
    assert familiar.privileges == {}


def test_companion_auto_generates_unique_id(make_creature):
    base = make_creature()
    c1 = Companion(name="Raven", base_creature=base, total_levels=20)
    c2 = Companion(name="Raven", base_creature=base, total_levels=20)
    assert c1.id != c2.id


def test_companion_privileges_are_keyed_by_level(make_creature):
    base = make_creature()
    feat = Feat(name="Alertness", description="x")
    privilege = CreaturePrivilege(
        name="Alertness", granted_at_level=1, description="x",
        privilege_type=CompanionPrivilegeType.FEAT, granted_privilege=feat,
    )
    familiar = Companion(
        name="Raven", base_creature=base, total_levels=20,
        privileges={1: [privilege]},
    )
    assert familiar.privileges[1][0].name == "Alertness"
