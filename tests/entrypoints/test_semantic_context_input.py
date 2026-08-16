"""
Tests for the shared semantic-context collection helpers.

Covers:
- prompt_for_creature_subtype(): valid, blank, and invalid-then-valid input
- resolve_relevant_creature_subtype(): only "incorporeal" survives
  reduction, everything else collapses to None
- prompt_for_semantic_context(): wires the three fields together into a
  SemanticContextInput
"""
from unittest.mock import patch
from monsterforge.structured_data.dnd.v3x.enums import CreatureSubtype
from monsterforge.entrypoints._semantic_context_input import (
    prompt_for_creature_subtype,
    prompt_for_multiple_creature_subtypes,
    resolve_relevant_creature_subtype,
    prompt_for_semantic_context,
    SemanticContextInput,
)


# =====================
# prompt_for_creature_subtype
# =====================
def test_prompt_for_creature_subtype_accepts_a_valid_value():
    with patch("builtins.input", side_effect=["incorporeal"]):
        assert prompt_for_creature_subtype() == CreatureSubtype.INCORPOREAL


def test_prompt_for_creature_subtype_blank_returns_none():
    with patch("builtins.input", side_effect=[""]):
        assert prompt_for_creature_subtype() is None


def test_prompt_for_creature_subtype_reprompts_on_invalid_value():
    with patch("builtins.input", side_effect=["bogus", "fire"]):
        assert prompt_for_creature_subtype() == CreatureSubtype.FIRE


# =====================
# prompt_for_multiple_creature_subtypes
# =====================
def test_prompt_for_multiple_creature_subtypes_collects_until_blank():
    with patch("builtins.input", side_effect=["fire", "incorporeal", ""]):
        result = prompt_for_multiple_creature_subtypes()

    assert result == [CreatureSubtype.FIRE, CreatureSubtype.INCORPOREAL]


def test_prompt_for_multiple_creature_subtypes_empty_on_immediate_blank():
    with patch("builtins.input", side_effect=[""]):
        assert prompt_for_multiple_creature_subtypes() == []


# =====================
# resolve_relevant_creature_subtype
# =====================
def test_resolve_relevant_creature_subtype_finds_incorporeal():
    result = resolve_relevant_creature_subtype([CreatureSubtype.FIRE, CreatureSubtype.INCORPOREAL])
    assert result == CreatureSubtype.INCORPOREAL


def test_resolve_relevant_creature_subtype_none_when_absent():
    result = resolve_relevant_creature_subtype([CreatureSubtype.FIRE, CreatureSubtype.EVIL])
    assert result is None


def test_resolve_relevant_creature_subtype_none_when_empty():
    assert resolve_relevant_creature_subtype([]) is None


# =====================
# prompt_for_semantic_context
# =====================
def test_prompt_for_semantic_context_collects_all_fields():
    with patch(
        "builtins.input",
        side_effect=["Extra flavor text.", "A shambling horror.", "incorporeal", ""],
    ):
        result = prompt_for_semantic_context()

    assert result == SemanticContextInput(
        additional_description="Extra flavor text.",
        creature_description="A shambling horror.",
        creature_subtype=CreatureSubtype.INCORPOREAL,
    )


def test_prompt_for_semantic_context_all_blank_is_all_none():
    with patch("builtins.input", side_effect=["", "", ""]):
        result = prompt_for_semantic_context()

    assert result == SemanticContextInput(
        additional_description=None,
        creature_description=None,
        creature_subtype=None,
    )
