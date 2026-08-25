"""
Tests for the shared prompt-template-choice CLI helper.

Covers: blank input keeps the default, a valid number selects the
matching template, and an invalid entry re-prompts rather than crashing
or silently falling back.
"""
from unittest.mock import patch
from monsterforge.llm.semantic_classification.attacks import ATTACK_PROMPT_TEMPLATE_OPTIONS
from monsterforge.entrypoints._template_selection_input import prompt_for_template_choice


def test_prompt_for_template_choice_blank_returns_the_default():
    with patch("builtins.input", side_effect=[""]):
        assert prompt_for_template_choice() == ATTACK_PROMPT_TEMPLATE_OPTIONS[0].path


def test_prompt_for_template_choice_accepts_a_valid_number():
    with patch("builtins.input", side_effect=["3"]):
        assert prompt_for_template_choice() == ATTACK_PROMPT_TEMPLATE_OPTIONS[2].path


def test_prompt_for_template_choice_reprompts_on_out_of_range_number():
    with patch("builtins.input", side_effect=["99", "2"]):
        assert prompt_for_template_choice() == ATTACK_PROMPT_TEMPLATE_OPTIONS[1].path


def test_prompt_for_template_choice_reprompts_on_non_numeric_input():
    with patch("builtins.input", side_effect=["bogus", "1"]):
        assert prompt_for_template_choice() == ATTACK_PROMPT_TEMPLATE_OPTIONS[0].path


def test_prompt_for_template_choice_blank_keeps_the_given_current_template():
    """Unlike the no-argument case (blank -> option 1), a rerun passes
    its already-in-use template as `current` — blank input should keep
    that, not silently reset to the default."""
    current = ATTACK_PROMPT_TEMPLATE_OPTIONS[2].path

    with patch("builtins.input", side_effect=[""]):
        assert prompt_for_template_choice(current=current) == current
