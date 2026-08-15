"""
Shared interactive helpers ensuring the LLM client is configured with a
model that actually works, for entry points that call the LLM (directly
or via the classification pipeline).

Model availability changes independently of this codebase (models get
deprecated/removed on the provider side), and is checked in two layers:

- ensure_model_available(): a pre-flight check against
  GeminiClient.list_text_models(), run once before an entry point does
  anything else.
- call_llm_with_model_fallback(): a reactive fallback for models that
  list_text_models() reports as supporting generateContent but are
  still rejected once actually invoked (e.g. "no longer available to
  new users" — an account-tier restriction the listing doesn't surface).

Neither layer ever falls back to an arbitrary model automatically: which
model is used can affect semantic classification results, so switching
away from the configured default is always an explicit, visible choice
made by the user.
"""
from typing import Callable, TypeVar
from monsterforge.llm.client import get_llm_client, set_llm_model, ModelUnavailableError

T = TypeVar("T")


def _prompt_for_model_choice(available: list[str]) -> str:
    """Print the available models and prompt for a choice by number,
    re-prompting on invalid input."""
    print("Available models:")
    for index, name in enumerate(available, start=1):
        print(f"  {index}. {name}")

    while True:
        choice = input(f"Choose a model [1-{len(available)}]: ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(available):
            return available[int(choice) - 1]

        print("Invalid choice, try again.")


def ensure_model_available() -> None:
    """
    Make sure the shared LLM client's current model is available; if
    not, list the models that are and ask the user to pick one.

    Model names from list_text_models() are prefixed with "models/"
    (e.g. "models/gemini-2.5-flash"), while GeminiClient.model_name is
    not — the prefix is stripped before comparing.
    """
    client = get_llm_client()
    available = [name.removeprefix("models/") for name in client.list_text_models()]

    if client.model_name in available:
        return

    print(f"Model {client.model_name!r} is not available for this API key/version.")
    set_llm_model(_prompt_for_model_choice(available))


def call_llm_with_model_fallback(action: Callable[[], T]) -> T:
    """
    Call action() (expected to eventually invoke the shared LLM client),
    retrying with a freshly user-picked model whenever the current one
    raises ModelUnavailableError — the reactive counterpart to
    ensure_model_available(), for models that looked available in
    list_text_models() but are rejected at actual generation time.

    Rules:
    - On ModelUnavailableError, the failing model is excluded from the
      choices offered next, so it can't be picked again.
    - If no models remain to retry with, the original error propagates.

    Args:
        action: A zero-argument callable to run, e.g.
            ``lambda: get_llm_client().generate_text(prompt)`` or
            ``lambda: convert_attack(raw_attack)``.
    """
    tried_models: set[str] = set()

    while True:
        try:
            return action()
        except ModelUnavailableError as exc:
            print(str(exc))

            client = get_llm_client()
            tried_models.add(client.model_name)
            available = [
                name.removeprefix("models/")
                for name in client.list_text_models()
                if name.removeprefix("models/") not in tried_models
            ]

            if not available:
                raise

            set_llm_model(_prompt_for_model_choice(available))
