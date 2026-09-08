"""
Integrity tests for api_demo_seed_data.py.

Same reasoning as test_sample_attacks_web_seed.py: this dataset is
load-bearing for a real user-facing feature (the public API demo), so
a typo here (an invalid attack_type, a creature_subtype outside the
enum, a range_value with no unit) would silently break the deployed
demo rather than surface as an obvious error.
"""
from monsterforge.entrypoints.api_demo_seed_data import DEMO_SEED_ATTACKS
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_converter import ATTACK_TYPE_OPTIONS
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_effects_parser import get_attack_effects
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype, MoveType, UnitSystem

CASE_KEYS = {"name", "modifier", "attack_type", "attack_effect"}
CONTEXT_KEYS = {"additional_description", "creature_description", "creature_subtype"}
CLASSIFICATION_KEYS = {"description", "move_type", "range_value", "range_unit", "confidence", "rationale"}
VALID_MOVE_TYPES = {move_type.value for move_type in MoveType}
VALID_SUBTYPES = {subtype.value for subtype in CreatureSubtype}
VALID_UNITS = {unit.value for unit in UnitSystem}


def test_dataset_has_eight_cases():
    assert len(DEMO_SEED_ATTACKS) == 8


def test_every_entry_has_exactly_the_three_top_level_sections():
    for entry in DEMO_SEED_ATTACKS:
        assert set(entry.keys()) == {"case", "context", "classification"}


def test_every_case_has_exactly_the_raw_attack_fields_and_a_name():
    for entry in DEMO_SEED_ATTACKS:
        case = entry["case"]
        assert set(case.keys()) == CASE_KEYS
        assert case["name"], f"blank name in entry: {entry}"


def test_attack_type_is_always_a_known_vocabulary_value():
    for entry in DEMO_SEED_ATTACKS:
        assert entry["case"]["attack_type"] in ATTACK_TYPE_OPTIONS, entry["case"]["name"]


def test_every_context_has_exactly_the_expected_keys():
    for entry in DEMO_SEED_ATTACKS:
        assert set(entry["context"].keys()) == CONTEXT_KEYS, entry["case"]["name"]


def test_creature_subtype_is_a_real_enum_value_or_none():
    for entry in DEMO_SEED_ATTACKS:
        subtype = entry["context"]["creature_subtype"]
        assert subtype is None or subtype in VALID_SUBTYPES, entry["case"]["name"]


def test_every_classification_has_exactly_the_expected_keys():
    for entry in DEMO_SEED_ATTACKS:
        assert set(entry["classification"].keys()) == CLASSIFICATION_KEYS, entry["case"]["name"]


def test_move_type_is_a_real_enum_value():
    for entry in DEMO_SEED_ATTACKS:
        assert entry["classification"]["move_type"] in VALID_MOVE_TYPES, entry["case"]["name"]


def test_range_value_and_unit_are_given_together_or_both_absent():
    for entry in DEMO_SEED_ATTACKS:
        classification = entry["classification"]
        has_value = classification["range_value"] is not None
        has_unit = classification["range_unit"] is not None
        assert has_value == has_unit, entry["case"]["name"]
        if has_unit:
            assert classification["range_unit"] in VALID_UNITS, entry["case"]["name"]


def test_confidence_is_a_valid_probability():
    for entry in DEMO_SEED_ATTACKS:
        confidence = entry["classification"]["confidence"]
        assert 0.0 <= confidence <= 1.0, entry["case"]["name"]


def test_every_attack_effect_parses_without_error():
    """Same single highest-value check as test_sample_attacks_web_seed.py's
    own version: runs every case's attack_effect through the real
    deterministic parser, not a mock -- api/demo_seed.py relies on this
    succeeding for every entry at process startup."""
    for entry in DEMO_SEED_ATTACKS:
        raw_attack = RawAttack(**entry["case"])
        get_attack_effects(raw_attack)
