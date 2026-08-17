# Project Status

Snapshot of where MonsterForge stands as of August 17, 2026.
For the system's design and long-term architecture, see [PIPELINE_ARCHITECTURE.md](./PIPELINE_ARCHITECTURE.md)
and [DESIGN.md](../../DESIGN.md). For how the LLM layer specifically is
structured, see [LLM_ARCHITECTURE.md](./LLM_ARCHITECTURE.md).

## In short

The first vertical slice — **"MVP zero"** — is complete and working end to end:
a D&D 3.x attack, entered by hand or with optional semantic context
(creature description, subtype...), converts through the full pipeline into a
domain `MoveCard` and comes out as JSON.
It has been exercised against the real Gemini API repeatedly, not just mocked —
including two independent full-dataset runs (65 real attacks each) kept for
review, one classification-only and one through the complete pipeline.
The current test suite contains 455 passing tests, 0 failing.

Persistence, an HTTP API, and a human-validation workflow are designed
in detail but not yet built — see [Limitations](#limitations--not-yet-built)
below.

## What works today

- **`raw_fields.Attack → structured_data.Attack → domain.MoveCard → JSON`**,
  the full conversion path for a single D&D 3.x attack, including
  attacks with a secondary effect (e.g. a bite granting Trip), which
  produces a nested reference card (`cards_to_add`).

- **LLM semantic classification** (move type, description, range) via
  Gemini, with **explicit model-availability handling** (see
  [LLM_ARCHITECTURE.md](./LLM_ARCHITECTURE.md) for the full design): no silent
  fallback to an arbitrary model. If the configured model is
  unavailable, the tool lists the models reported as available to this API key
  and asks the user to pick one — both before starting (pre-flight check)
  and reactively, if a model that looked available turns out to be
  rejected only once actually invoked.

- **Full optional semantic context, not just the bare attack**: both
  interactive entry points collect `additional_description`,
  `creature_description`, and `creature_subtype` (via a shared
  `entrypoints/_semantic_context_input.py`) and pass them through to
  `classify_attack()` — verified live to actually change the real
  classification (e.g. `creature_subtype=incorporeal` correctly forces
  `move_type=magical` per the prompt's own rule).

- **Three CLI entry points** (`python -m monsterforge.entrypoints.<name>`):
  - `convert_attack_cli` — hand-enter an attack (+ optional context), get its
    MoveCard JSON.
  - `test_llm_prompt_cli` — render any Jinja2 prompt template and send it
    to the real LLM client, for iterating on prompts directly.
  - `collect_real_classifications` / `collect_real_pipeline_conversions` —
    batch tools that run all 65 samples in `SAMPLE_ATTACKS` through, respectively,
    just `classify_attack()` or the complete pipeline, against the real API
    (5s delay between calls, configurable per script), saving raw + parsed
    results to `entrypoints/output/*.json` for manual review. Deliberately two
    independent scripts making two independent rounds of real calls, not one
    reusing the other's data — so results can also be diffed against each
    other to see how much a live classification varies run to run (including
    whether the model's self-reported confidence is at all stable). **Not**
    part of the automated test suite: real API calls, non-deterministic,
    several minutes, quota use.

- **A reusable golden-file validation procedure**
  (`tests/tools/generate_expected_outputs.py`, built on the generic
  dataclass/enum flattener in `monsterforge/serialization/plain_data.py`):
  dumps a conversion function's actual output over a sample set for one-time
  human review, then the corrected file becomes a committed regression
  fixture. Not specific to attacks — meant to be reused for future conversion
  pipelines (feats, spells, special qualities) needing the same
  validate-once-then-pin workflow.

## Test coverage

**455 passing, 0 failing.** A set of 9 pre-existing failures (unrelated
to the attack pipeline itself — stale tests in `tests/domain/`,
`tests/rules/dnd/v3x/`, and `tests/structured_data/dnd/v3x/`, left over
from earlier field/behavior changes elsewhere in the codebase that the
tests hadn't caught up with) has since been fixed in a dedicated pass,
along with one real bug found in the process: `rules/dnd/v3x/
vitality_tables.py`'s hit-die table was missing an entry for D2, present
in `DESIGN.md`'s own LIFE table but absent from the code — a creature
with `hit_dice_type=D2` would have raised `KeyError`.

## Limitations / not yet built

Deliberately out of scope for "MVP zero", to keep it small enough to
ship:

- **`FullAttack`** — only a single `Attack` converts; multiple/iterative
  attacks aren't handled yet.

- **Persistence** — no database; every conversion is computed fresh,
  with no stable/deterministic card IDs across runs.

- **HTTP API** — no FastAPI layer; the pipeline is reachable only via
  the CLI entry points.

- **Human validation workflow** — low-confidence LLM classifications
  aren't routed anywhere for review; there's no CLI or UI validation
  step.

- **Other `MoveCard` sources** — only attacks produce move cards today;
  talents, spells, and special qualities aren't wired in
  (`transformation/dnd/v3x/converters/move_converter.py` remains an
  intentional stub for when a second source exists).

The next phase — "MVP espanso" — has all of the above designed in
detail but not yet built: persistence with stable card identity derived
from a content fingerprint (so the same attack always resolves to the
same card, even across separate runs), a FastAPI HTTP layer, and a
confidence-gated human validation step for low-confidence LLM
classifications.

## Open TODOs

- **`SAMPLE_ATTACKS` only carries the four bare raw fields** (name,
  modifier, attack_type, attack_effect) — no `additional_description`,
  `creature_description`, or `creature_subtype` per case. This means
  the two real-API collection scripts, and any regression test built on
  top of them, currently only ever exercise `classify_attack()` with
  that context defaulted to `None`, even though the code path for
  supplying it is built and verified (see "What works today" above).
  Plan: a separate, richer sample file (not a rewrite of
  `SAMPLE_ATTACKS`, which several existing deterministic parser tests
  already depend on) carrying full context per case, to run through
  both collection scripts and compare classification quality with vs.
  without context.

## Notable fixes and findings

A few things worth calling out about how this slice got built, not as a
full changelog:

- Four blocking bugs in the conversion path were found by **executing**
  the code against real sample data (not just reading it) — a missing
  required field on `SpecialAttack`, a keyword-only argument passed
  positionally, a client call with an argument the function doesn't
  accept, and an unimplemented converter stub. All four would have
  crashed the pipeline on any attack with a secondary effect.
- The golden-file review of the parser surfaced a real classification
  bug (a component with no dice/bonus of its own, e.g. "positive
  energy" alone, was misclassified as damage instead of a special
  attack) — fixed as a general parsing rule, verified to affect only the
  cases it should across all 65 sample attacks.
- The default LLM model (`gemini-1.5-flash`) turned out to be
  deprecated mid-session; reproduced live against the real API and
  replaced with explicit, non-silent handling for both "model doesn't
  exist" and "model exists but is no longer available to this account"
  failure modes — see [LLM_ARCHITECTURE.md](./LLM_ARCHITECTURE.md).
- Running all 65 samples through the *complete* pipeline against the
  real API (not just classification) surfaced a real integration gap
  invisible to both the mocked unit tests and the classification-only
  collection run: 8 of 65 real ranged attacks (Web, Rock, Light ray,
  Electricity ray, Swarm, Psychic lash) hit `UnknownAttackRange` because
  the LLM didn't return a usable range for them and their names aren't
  in `KNOWN_ATTACKS`. Confirmed as **correct, intentional behavior**
  (failing loudly beats silently guessing a range), not a bug to patch —
  but it's a real, now-quantified gap in range-fallback coverage worth
  addressing later (expand `KNOWN_ATTACKS`, tighten the prompt, or add
  an explicit "range undetermined" domain outcome).
- [PIPELINE_ARCHITECTURE.md](./PIPELINE_ARCHITECTURE.md) was revised to settle
  an open question about the not-yet-built `rendering/` stage: whether it
  should share the same `serialization/` output as `api/`, or convert from
  `domain/` independently. Settled on sharing — including the same reduction
  of referenced cards (e.g. `MoveCard.cards_to_add`) to `{"name", "id"}` —
  once it became clear that reduction isn't a network-payload optimization
  but a consequence of the physical card format itself (standard
  Magic-sized cards, ~63×88mm, can't fit another card's full contents).
  A superseded dev-note proposing an earlier, less-motivated version of the
  same fork was removed once its content was folded in.

## Documentation housekeeping

The root [README.md](../../README.md) was rewritten: it now links correctly
to `monsterforge/docs/` (it previously pointed to a root-level `docs/` folder
that never existed), distinguishes current status from the original vision,
and no longer mentions the PyQt5 desktop tool from the original plan (see
[Architecture](./PIPELINE_ARCHITECTURE.md), superseded by a FastAPI JSON API
serving both `api/` and a future `rendering/` stage). The original README is
kept for reference at
[monsterforge/docs/archive/README_v1.md](./archive/README_v1.md).
