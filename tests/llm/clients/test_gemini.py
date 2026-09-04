"""
Tests for the Gemini LLM client wrapper.

Covers:
- generate_text() translates an APIError with code 404 (raised by the
  underlying SDK both when a model doesn't exist and when it's "no
  longer available to new users" for this account/tier) into the
  project-specific ModelUnavailableError, keeping it distinguishable
  from other APIError codes that callers should not treat the same way.
"""
from unittest.mock import MagicMock, patch
import pytest
from google.genai import errors
from monsterforge.llm.clients.gemini import GeminiClient, ModelUnavailableError


def _api_error(code: int, message: str) -> errors.APIError:
    return errors.APIError(code, {"error": {"code": code, "message": message}})


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    with patch("monsterforge.llm.clients.gemini.genai.Client") as mock_client_cls:
        instance = GeminiClient(llm_model="gemini-flash-lite-latest")
        instance._client = mock_client_cls.return_value
        return instance


def test_generate_text_returns_response_text_on_success(client):
    response = MagicMock()
    response.text = "hello"
    client._client.models.generate_content.return_value = response

    assert client.generate_text("prompt") == "hello"


def test_generate_text_raises_model_unavailable_error_on_not_found(client):
    client._client.models.generate_content.side_effect = _api_error(404, "model not found")

    with pytest.raises(ModelUnavailableError):
        client.generate_text("prompt")


def test_generate_text_raises_plain_runtime_error_on_other_api_errors(client):
    """Other APIError codes (rate limits, invalid arguments...) must not
    be mistaken for a model-availability problem."""
    client._client.models.generate_content.side_effect = _api_error(400, "bad request")

    with pytest.raises(RuntimeError) as exc_info:
        client.generate_text("prompt")

    assert not isinstance(exc_info.value, ModelUnavailableError)


def test_missing_api_key_raises_value_error(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValueError):
        GeminiClient(llm_model="gemini-flash-lite-latest")


def test_change_llm_model_updates_model_name_without_rebuilding_client(client):
    """Unlike the old SDK, the model name is passed per call, not bound
    to a client/model object — switching models is just an attribute
    update, and the underlying client instance must stay the same."""
    original_client = client._client

    client.change_llm_model("gemini-2.5-pro")

    assert client.model_name == "gemini-2.5-pro"
    assert client._client is original_client


def test_list_text_models_filters_by_generate_content_support(client):
    supported = MagicMock(name="supported")
    supported.name = "models/gemini-flash-lite-latest"
    supported.supported_actions = ["generateContent", "countTokens"]

    unsupported = MagicMock(name="unsupported")
    unsupported.name = "models/embedding-001"
    unsupported.supported_actions = ["embedContent"]

    client._client.models.list.return_value = [supported, unsupported]

    assert client.list_text_models() == ["models/gemini-flash-lite-latest"]
