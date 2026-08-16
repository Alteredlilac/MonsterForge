# LLM Layer Architecture

How MonsterForge talks to an LLM, how it verifies the configured model
actually works, and what happens when it doesn't.

This document covers `llm/client.py`, `llm/clients/gemini.py`, and
`entrypoints/_llm_model_selection.py`. It does not describe a
multi-provider abstraction — none exists yet. See
[Generic vs Gemini-specific](#generic-vs-gemini-specific) below for
exactly how much of this layer is actually provider-agnostic today.

## Layer structure

```
llm/
├── client.py                    # application-facing entry point
│   ├── get_llm_client()           # returns the shared client instance
│   ├── set_llm_model(name)         # switches the shared client's model
│   └── ModelUnavailableError        # re-exported from clients/gemini.py
└── clients/
    └── gemini.py                 # Gemini-specific implementation
        ├── GeminiClient
        └── ModelUnavailableError

entrypoints/
└── _llm_model_selection.py      # interactive model-availability helpers
    ├── ensure_model_available()
    └── call_llm_with_model_fallback()
```

Callers never import `clients/gemini.py` directly — they go through
`llm/client.py`, which is the seam between "the rest of the app" and
"whichever provider is actually configured."

## How the model is chosen and verified

The default model is a module-level constant in `llm/client.py`:

```python
_DEFAULT_MODEL = "gemini-flash-lite-latest"
```

A `"-latest"` alias is used deliberately instead of a dated snapshot
(the previous default, `"gemini-1.5-flash"`, was removed from the API
mid-project): an alias tracks the provider's current recommended model
for that tier, so it's less likely to go stale. This reduces how often
the default becomes unavailable — it doesn't eliminate the possibility,
which is why the rest of this document exists.

Verification happens in two places, at two different times:

1. **Pre-flight, before anything else runs**: `ensure_model_available()`
   calls `GeminiClient.list_text_models()` and checks whether the
   configured model is in that list.
2. **Reactively, at the moment of generation**: even a model
   `list_text_models()` reports as supporting `generateContent` can
   still be rejected when actually invoked (Gemini has models that are
   listed but "no longer available to new users" for a given
   account/tier — a restriction the listing endpoint doesn't surface).
   `call_llm_with_model_fallback()` is what reacts to *that*.

Neither check is optional or implicit — an entry point has to call both
explicitly (see [Consumers](#consumers)).

## What happens if the model isn't available

`GeminiClient.generate_text()` distinguishes two kinds of failure:

```python
except NotFound as exc:
    raise ModelUnavailableError(...) from exc
except GoogleAPIError as exc:
    raise RuntimeError(f"Gemini API error: {exc}") from exc
```

- **`NotFound`** (model doesn't exist, or exists but is rejected for
  this account) → `ModelUnavailableError`, a specific, catchable
  signal that means "the *model* is the problem."
- **Any other `GoogleAPIError`** (rate limits, invalid arguments, ...)
  → a plain `RuntimeError`. These are not model-availability problems
  and must not be treated as one — `call_llm_with_model_fallback()`
  only reacts to `ModelUnavailableError`, everything else propagates
  immediately.

There is **no automatic fallback to an arbitrary model**, in either case.
Because the selected model can affect semantic classification results,
model selection is treated as an explicit user choice rather than an
implementation detail. The system detects model unavailability and asks
the user to choose an alternative; it never silently substitutes a different model

## Role of `ensure_model_available()` and `call_llm_with_model_fallback()`

Both live in `entrypoints/_llm_model_selection.py`, not in `llm/`
itself — they're interactive (`input()`-driven), which doesn't belong
in the provider-agnostic client layer.

- **`ensure_model_available()`** — call once, before doing anything
  else. Cheap pre-check against `list_text_models()`; if the current
  model isn't listed, prints the available models and prompts for a
  choice by number, then calls `set_llm_model()`.

- **`call_llm_with_model_fallback(action)`** — wraps a zero-argument
  callable that eventually reaches the LLM (directly, or several calls
  deep, e.g. through `classify_attack()`). On `ModelUnavailableError`,
  it excludes the failing model from the next round of choices, prompts
  again, and retries `action()` from scratch. If no models remain to
  try, the original error propagates instead of looping forever.

Together they implement the "verify, and if the model turns out to be
unusable, ask — never assume" policy at both points where it can fail:
before starting, and when a listed-but-secretly-rejected model is hit
at generation time.

## Why `get_llm_client()` is a singleton

```python
_client: GeminiClient | None = None

def get_llm_client() -> GeminiClient:
    global _client
    if _client is None:
        _client = GeminiClient(llm_model=_DEFAULT_MODEL)
    return _client
```

A model choice made by `ensure_model_available()`/
`call_llm_with_model_fallback()` at an entry point has to be visible to
`get_llm_client()` calls buried several levels deeper — e.g.
`convert_attack() → classify_attack() → _call_attack_classifier() →
get_llm_client()`. A fresh `GeminiClient` per call would silently
reconstruct the old default every time, undoing the user's choice.

The singleton makes `set_llm_model()` — called once, near the top —
take effect everywhere, without threading a model parameter through
every function in between. The trade-off is explicit: this is shared
mutable state, so tests that exercise real (non-mocked) client code
across multiple cases must reset the module's `_client` global between
cases (see the fixture in `tests/entrypoints/test_llm_model_selection.py`).

## Generic vs Gemini-specific

- **Generic (provider-agnostic surface)**: `llm/client.py` —
  `get_llm_client()`, `set_llm_model()`, and the re-exported
  `ModelUnavailableError`. This is the entire abstraction boundary
  today: three names, nothing more. No `Protocol`/ABC defines what a
  "provider" must implement, and no second provider exists.
- **Gemini-specific**: everything in `llm/clients/gemini.py` —
  `GeminiClient` itself, the Google SDK calls, and the
  `NotFound`/`GoogleAPIError` distinction (specific to how the Gemini
  SDK reports failures).
- **Also provider-agnostic, but outside `llm/`**: the model-selection
  helpers in `entrypoints/_llm_model_selection.py` only call through
  `llm/client.py`'s interface (`get_llm_client()`, `set_llm_model()`,
  `ModelUnavailableError`) — they never import `clients/gemini.py`
  directly, so they'd keep working unchanged if a second provider were
  added later.

There is no multi-provider selection logic, config-driven provider
choice, or provider interface — this section describes how thin the
current seam is, not a plan to widen it.

## Consumers

- `llm/semantic_classification/attacks.py::classify_attack()` — the
  only production caller today; gets the client via `get_llm_client()`,
  never constructs a `GeminiClient` directly.
- `entrypoints/convert_attack_cli.py` and
  `entrypoints/test_llm_prompt_cli.py` — both call
  `ensure_model_available()` once at startup and wrap their LLM-reaching
  call in `call_llm_with_model_fallback()`.
