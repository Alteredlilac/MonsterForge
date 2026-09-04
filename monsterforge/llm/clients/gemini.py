"""
Gemini LLM Client

Simple client to interact with Google Gemini models through the
Google Gen AI SDK (google-genai).

This module provides a lightweight interface for text generation
used by the application, such as AI-assisted content generation
for game data, descriptions, and transformations.

Requires:
- GEMINI_API_KEY in environment variables

Configuration:
- Model name provided at initialization
- API key loaded from environment variables

Flow:
INIT → GENERATE → (OPTIONAL) SWITCH MODEL

Example:
    client = GeminiClient(llm_model="gemini-flash-lite-latest")

    description = client.generate_text(
        "Create a fantasy description for an undead creature"
    )

    client.change_llm_model("gemini-2.5-pro")
"""

from dotenv import load_dotenv
import os
from google import genai
from google.genai import errors, types
from monsterforge.config.llm_settings import (
    RETRY_ATTEMPTS,
    RETRY_INITIAL_DELAY_SECONDS,
    RETRY_MAX_DELAY_SECONDS,
)

load_dotenv()


class ModelUnavailableError(RuntimeError):
    """
    Raised when the configured model can't generate content for this
    API key/account (deprecated, region-restricted, tier-restricted...).

    Distinguished from other Gemini API errors (rate limits, invalid
    arguments...) so callers can react specifically — e.g. ask the user
    to pick a different model — instead of treating every failure the
    same way.
    """
    pass


class GeminiClient:
    def __init__(self, llm_model: str):
        """Build a Gemini client authenticated from GEMINI_API_KEY, with retry configured for transient API errors."""
        self.model_name = llm_model
        self._load_api_key()
        self._client = genai.Client(
            api_key=self._api_key,
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(
                    attempts=RETRY_ATTEMPTS,
                    initial_delay=RETRY_INITIAL_DELAY_SECONDS,
                    max_delay=RETRY_MAX_DELAY_SECONDS,
                )
            ),
        )

    def _load_api_key(self) -> None:
        """Read GEMINI_API_KEY from the environment, raising if it's missing."""
        self._api_key = os.getenv("GEMINI_API_KEY")

        if not self._api_key:
            raise ValueError("Missing GEMINI_API_KEY in environment")

    def change_llm_model(self, model_name: str) -> None:
        """Switch the model used by subsequent generate_text() calls."""
        # NOTE:
        # google-genai's Client is not bound to a single model the way
        # google-generativeai's GenerativeModel was — the model name is
        # passed per call to generate_content(). Switching models is
        # therefore just updating this attribute, no client/model object
        # to rebuild.
        self.model_name = model_name

    def generate_text(self, question: str) -> str:
        """
        Generate text from the configured model.

        Raises:
            ModelUnavailableError:
                If the configured model doesn't exist or is no longer
                available to this API key/account.
            RuntimeError:
                For any other Gemini API failure (rate limits, invalid
                arguments...).
        """
        try:
            response = self._client.models.generate_content(
                model=self.model_name, contents=question,
            )
            return getattr(response, "text", "")
        except errors.APIError as exc:
            # NOTE:
            # google-genai raises a single APIError for every API failure,
            # distinguished by .code rather than by exception subclass
            # (unlike the old SDK's separate NotFound/GoogleAPIError
            # hierarchy). Code 404 covers both a model that doesn't exist
            # at all and one that exists but is "no longer available to
            # new users" for this account/tier — a restriction
            # list_text_models() doesn't surface, so it can only be
            # detected here, at actual generation time.
            if exc.code == 404:
                raise ModelUnavailableError(
                    f"Model {self.model_name!r} is not available: {exc}"
                ) from exc
            raise RuntimeError(f"Gemini API error: {exc}") from exc

    def list_text_models(self) -> list[str]:
        """List model names that support text generation (generateContent)."""
        return [
            m.name
            for m in self._client.models.list()
            if "generateContent" in (m.supported_actions or [])
        ]
