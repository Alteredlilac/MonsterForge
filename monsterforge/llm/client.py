"""
Provide the centralized LLM client configuration for MonsterForge.

This module exposes the application-level interface used to obtain the
configured LLM client without requiring callers to depend directly on a
specific provider implementation.

The client configuration is centralized here so that semantic classification
and other LLM-powered modules can request an LLM client without knowing which
provider or model is currently being used.

The current implementation uses the Gemini client with a default model
configuration.

The client layer is organized as follows:

llm/
├── client.py                 # centralized LLM client configuration
└── clients/
└── gemini.py             # Gemini-specific client implementation

Public API:

get_llm_client()
    Return the shared, configured LLM client used by the application.

set_llm_model(model_name)
    Switch the model used by the shared client for the rest of this
    process.

ModelUnavailableError
    Re-exported from clients.gemini so callers depending only on this
    module's abstraction can catch it without importing the
    provider-specific submodule directly.
"""
from .clients.gemini import GeminiClient, ModelUnavailableError

# NOTE:
# "-latest" alias models track the provider's current recommended model
# for that tier instead of a dated snapshot, so they are far less likely
# to be silently deprecated/removed than a pinned version like
# "gemini-1.5-flash" was. This does not eliminate the possibility of the
# default becoming unavailable — see ModelUnavailableError and
# entrypoints/_llm_model_selection.py for how that is still handled
# explicitly, without a silent fallback, when it happens anyway.
_DEFAULT_MODEL = "gemini-flash-lite-latest"

# NOTE:
# get_llm_client() returns a single shared instance (built lazily on
# first call), not a fresh GeminiClient every time. This is what lets
# set_llm_model() — called once by an interactive entry point when the
# default model isn't available (see entrypoints/_llm_model_selection.py)
# — take effect for every subsequent call, including ones buried deep in
# the classification pipeline (classify_attack -> _call_attack_classifier
# -> get_llm_client), without threading a model parameter through every
# function in between. The trade-off: this is shared mutable state.
# Tests that exercise real (non-mocked) LLM client code across multiple
# cases should be aware a prior case's set_llm_model() call persists.
_client: GeminiClient | None = None


def get_llm_client() -> GeminiClient:
    """
    Return the shared, configured LLM client used by the application.
    """
    global _client

    if _client is None:
        _client = GeminiClient(llm_model=_DEFAULT_MODEL)

    return _client


def set_llm_model(model_name: str) -> None:
    """
    Switch the model used by the shared client for the rest of this
    process, via GeminiClient.change_llm_model().
    """
    get_llm_client().change_llm_model(model_name)
