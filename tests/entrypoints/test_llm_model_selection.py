"""
Tests for the interactive LLM model selection/fallback helpers.

Covers:
- ensure_model_available(): no-op when the current model is listed,
  prompts and applies a choice when it isn't, re-prompts on invalid input
- call_llm_with_model_fallback(): success passthrough, retry-with-
  exclusion on ModelUnavailableError, and propagation once no models
  remain to retry with
"""
from unittest.mock import MagicMock, patch
import pytest
import monsterforge.llm.client as llm_client_module
from monsterforge.llm.client import ModelUnavailableError
from monsterforge.entrypoints._llm_model_selection import (
    ensure_model_available,
    call_llm_with_model_fallback,
)


@pytest.fixture
def make_mock_client():
    """
    Factory installing a MagicMock as the shared llm.client singleton.

    get_llm_client() (in both llm/client.py and, transitively, calls
    made from set_llm_model()) reads the module-level _client global
    directly, so setting it here — rather than patching get_llm_client
    itself — is what makes every code path see the same mock, including
    set_llm_model()'s own internal get_llm_client() call.
    """
    def _make(model_name, listed_models):
        client = MagicMock()
        client.model_name = model_name
        client.list_text_models.return_value = listed_models
        client.change_llm_model.side_effect = lambda name: setattr(client, "model_name", name)
        llm_client_module._client = client
        return client

    yield _make

    llm_client_module._client = None


# =====================
# ensure_model_available
# =====================
def test_ensure_model_available_is_a_noop_when_the_model_is_listed(make_mock_client):
    mock_client = make_mock_client(
        "gemini-flash-lite-latest",
        ["models/gemini-flash-lite-latest", "models/gemini-2.5-pro"],
    )

    ensure_model_available()

    mock_client.change_llm_model.assert_not_called()


def test_ensure_model_available_prompts_and_applies_a_choice_when_unavailable(make_mock_client):
    mock_client = make_mock_client(
        "gemini-1.5-flash",
        ["models/gemini-2.5-pro", "models/gemini-flash-lite-latest"],
    )

    with patch("builtins.input", side_effect=["2"]):
        ensure_model_available()

    assert mock_client.model_name == "gemini-flash-lite-latest"


def test_ensure_model_available_reprompts_on_invalid_choice(make_mock_client):
    mock_client = make_mock_client("gemini-1.5-flash", ["models/gemini-2.5-pro"])

    with patch("builtins.input", side_effect=["bogus", "0", "1"]):
        ensure_model_available()

    assert mock_client.model_name == "gemini-2.5-pro"


# =====================
# call_llm_with_model_fallback
# =====================
def test_call_llm_with_model_fallback_returns_action_result_on_success():
    assert call_llm_with_model_fallback(lambda: "ok") == "ok"


def test_call_llm_with_model_fallback_retries_with_a_different_model(make_mock_client):
    mock_client = make_mock_client(
        "gemini-2.5-flash",
        ["models/gemini-2.5-flash", "models/gemini-flash-lite-latest"],
    )
    attempts = []

    def action():
        attempts.append(mock_client.model_name)
        if mock_client.model_name == "gemini-2.5-flash":
            raise ModelUnavailableError("gemini-2.5-flash is not available")
        return "success"

    with patch("builtins.input", side_effect=["1"]):
        result = call_llm_with_model_fallback(action)

    assert result == "success"
    assert attempts == ["gemini-2.5-flash", "gemini-flash-lite-latest"]


def test_call_llm_with_model_fallback_excludes_the_failing_model_from_choices(make_mock_client):
    """After the first failure excludes gemini-2.5-flash, only one model
    remains, so exactly one prompt should fire before the second
    (still-failing) attempt runs out of models to try."""
    make_mock_client(
        "gemini-2.5-flash",
        ["models/gemini-2.5-flash", "models/gemini-flash-lite-latest"],
    )

    def action():
        raise ModelUnavailableError("always fails")

    with patch("builtins.input", side_effect=["1"]) as mock_input:
        with pytest.raises(ModelUnavailableError):
            call_llm_with_model_fallback(action)

    assert mock_input.call_count == 1


def test_call_llm_with_model_fallback_propagates_when_no_models_remain(make_mock_client):
    make_mock_client("gemini-2.5-flash", ["models/gemini-2.5-flash"])

    def action():
        raise ModelUnavailableError("always fails")

    with pytest.raises(ModelUnavailableError):
        call_llm_with_model_fallback(action)
