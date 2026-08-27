"""
Integrity tests for sample_attacks_web_seed.py.

Unlike sample_attacks.py/sample_attacks_with_context.py (which get no
dedicated tests of their own -- pure fixture data exercised implicitly
by whatever consumes them), this dataset is load-bearing for a real
user-facing feature: the live /convert form's Auto-fill button reads
these fields directly and posts them as-is. A typo here (an invalid
attack_type, a creature_subtype outside the enum, a ranged attack with
no way to resolve its range) would silently produce a broken auto-fill
click with no server-side error to catch it -- worth a real regression
test, not just a one-time manual check.
"""
from monsterforge.entrypoints.sample_attacks_web_seed import SAMPLE_ATTACKS_WEB_SEED
from monsterforge.parsing.dnd.v3x.raw_fields.attacks import Attack as RawAttack
from monsterforge.parsing.dnd.v3x.structured_conversions.attacks.attacks_effects_parser import get_attack_effects
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype

EXPECTED_KEYS = {
    "name", "modifier", "attack_type", "attack_effect", "range_value",
    "range_unit", "additional_description", "creature_description",
    "creature_subtype",
}
VALID_ATTACK_TYPES = {"melee", "melee touch", "ranged", "ranged touch"}
VALID_SUBTYPES = {subtype.value for subtype in CreatureSubtype} | {""}


def test_dataset_has_one_hundred_cases():
    assert len(SAMPLE_ATTACKS_WEB_SEED) == 100


def test_every_case_has_exactly_the_form_fields_and_a_name():
    """Keys must match the /convert form's field ids exactly -- the
    auto-fill JS sets document.getElementById(key).value for every key
    in the sample object, so an extra or misspelled key is silently
    ignored rather than causing a visible error."""
    for case in SAMPLE_ATTACKS_WEB_SEED:
        assert set(case.keys()) == EXPECTED_KEYS
        assert case["name"], f"blank name in case: {case}"


def test_attack_type_is_always_a_valid_dropdown_option():
    for case in SAMPLE_ATTACKS_WEB_SEED:
        assert case["attack_type"] in VALID_ATTACK_TYPES, case["name"]


def test_creature_subtype_is_a_real_enum_value_or_blank():
    for case in SAMPLE_ATTACKS_WEB_SEED:
        assert case["creature_subtype"] in VALID_SUBTYPES, case["name"]


def test_ranged_cases_can_always_resolve_a_range():
    """Matches /convert's own server-side rule: a ranged/ranged touch
    attack needs either an explicit range_value+range_unit or prose in
    additional_description -- otherwise the live form would reject its
    own auto-filled data with a 422."""
    for case in SAMPLE_ATTACKS_WEB_SEED:
        if case["attack_type"] not in ("ranged", "ranged touch"):
            continue
        has_structured_range = bool(case["range_value"]) and bool(case["range_unit"])
        has_prose_range = bool(case["additional_description"].strip())
        assert has_structured_range or has_prose_range, case["name"]


def test_non_ranged_cases_never_set_a_range():
    for case in SAMPLE_ATTACKS_WEB_SEED:
        if case["attack_type"] in ("ranged", "ranged touch"):
            continue
        assert case["range_value"] == "" and case["range_unit"] == "", case["name"]


def test_every_attack_effect_parses_without_error():
    """The single highest-value check here: runs every case's
    attack_effect through the real deterministic parser (not a mock),
    per this project's own 'verify by executing' discipline. A parser
    exception on auto-filled data would surface as a raw 500 on the
    live site, not a friendly error."""
    for case in SAMPLE_ATTACKS_WEB_SEED:
        raw_attack = RawAttack(
            name=case["name"],
            modifier=case["modifier"] or "+0",
            attack_type=case["attack_type"],
            attack_effect=case["attack_effect"],
        )
        get_attack_effects(raw_attack)
