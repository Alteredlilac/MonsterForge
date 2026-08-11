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
    Return the configured LLM client used by the application.

"""
from .clients.gemini import GeminiClient

_DEFAULT_MODEL = "gemini-1.5-flash"


def get_llm_client() -> GeminiClient:
    """
    Return the configured LLM client used by the application.
    """
    return GeminiClient(llm_model=_DEFAULT_MODEL)
