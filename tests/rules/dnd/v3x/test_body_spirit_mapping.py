"""
Tests for body_spirit_mapping.py.

These are static rule mappings, so tests focus on structural integrity
rather than calculation logic.

The module defines the relationships between D&D 3.x ability scores
and MonsterForge body/spirit attributes.

Tests verify:
- expected body attributes are mapped
- creature-type overrides modify only the intended attribute
- spirit attributes have the expected ability references
- mappings remain immutable
"""
import pytest
from monsterforge.rules.dnd.v3x.body_spirit_mapping import (
    BODY_STAT_MAPPING, UNDEAD_BODY_STAT_MAPPING,
    CONSTRUCT_BODY_STAT_MAPPING, SPIRIT_STAT_MAPPING,
)



def test_body_stat_mapping_has_expected_keys():
    expected = {"attack", "defense", "speed"}
    assert set(BODY_STAT_MAPPING.keys()) == expected


def test_undead_override_differs_only_in_defense():
    """The undead variant should override defense only, keeping
    attack/speed identical to the default mapping."""
    assert UNDEAD_BODY_STAT_MAPPING["attack"] == BODY_STAT_MAPPING["attack"]
    assert UNDEAD_BODY_STAT_MAPPING["speed"] == BODY_STAT_MAPPING["speed"]
    assert UNDEAD_BODY_STAT_MAPPING["defense"] != BODY_STAT_MAPPING["defense"]
    assert UNDEAD_BODY_STAT_MAPPING["defense"] == "dexterity"


def test_construct_override_differs_only_in_defense():
    """The construct variant should override defense only."""
    assert CONSTRUCT_BODY_STAT_MAPPING["attack"] == BODY_STAT_MAPPING["attack"]
    assert CONSTRUCT_BODY_STAT_MAPPING["speed"] == BODY_STAT_MAPPING["speed"]
    assert CONSTRUCT_BODY_STAT_MAPPING["defense"] != BODY_STAT_MAPPING["defense"]
    assert CONSTRUCT_BODY_STAT_MAPPING["defense"] == "strength"


def test_spirit_stat_mapping_has_expected_keys():
    expected = {"power", "ward", "flow"}
    assert set(SPIRIT_STAT_MAPPING.keys()) == expected


@pytest.mark.parametrize(
    "mapping",
    [
        BODY_STAT_MAPPING,
        UNDEAD_BODY_STAT_MAPPING,
        CONSTRUCT_BODY_STAT_MAPPING,
        SPIRIT_STAT_MAPPING,
    ],
)
def test_tables_are_immutable(mapping):
    with pytest.raises(TypeError):
        mapping["invalid"] = "value"
