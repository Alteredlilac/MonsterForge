"""
Tests for the Gemini LLM client wrapper.

Covers:
- generate_text() translates NotFound (raised by the underlying SDK
  both when a model doesn't exist and when it's "no longer available to
  new users" for this account/tier) into the project-specific
  ModelUnavailableError, keeping it distinguishable from other
  GoogleAPIError failures that callers should not treat the same way.
"""
from unittest.mock import MagicMock, patch
import pytest
from google.api_core.exceptions import NotFound, InvalidArgument
from monsterforge.llm.clients.gemini import GeminiClient, ModelUnavailableError


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    with patch("monsterforge.llm.clients.gemini.genai.configure"), \
         patch("monsterforge.llm.clients.gemini.genai.GenerativeModel"):
        return GeminiClient(llm_model="gemini-flash-lite-latest")


def test_generate_text_returns_response_text_on_success(client):
    response = MagicMock()
    response.text = "hello"
    client.model.generate_content.return_value = response

    assert client.generate_text("prompt") == "hello"


def test_generate_text_raises_model_unavailable_error_on_not_found(client):
    client.model.generate_content.side_effect = NotFound("model not found")

    with pytest.raises(ModelUnavailableError):
        client.generate_text("prompt")


def test_generate_text_raises_plain_runtime_error_on_other_api_errors(client):
    """Other GoogleAPIError failures (rate limits, invalid arguments...)
    must not be mistaken for a model-availability problem."""
    client.model.generate_content.side_effect = InvalidArgument("bad request")

    with pytest.raises(RuntimeError) as exc_info:
        client.generate_text("prompt")

    assert not isinstance(exc_info.value, ModelUnavailableError)


def test_missing_api_key_raises_value_error(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValueError):
        GeminiClient(llm_model="gemini-flash-lite-latest")
