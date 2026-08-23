# Project Status

Snapshot of where MonsterForge stands as of August 23, 2026.
For the system's design and long-term architecture, see [PIPELINE_ARCHITECTURE.md](./PIPELINE_ARCHITECTURE.md)
and [DESIGN.md](../../DESIGN.md). For how the LLM layer specifically is
structured, see [LLM_ARCHITECTURE.md](./LLM_ARCHITECTURE.md). For how a
`MoveCard` becomes a printable card and how that's showcased against real
pipeline output, see [RENDERING_AND_GALLERY.md](./RENDERING_AND_GALLERY.md).

## In short

The first vertical slice — **"MVP zero"** — is complete and working end to end:
a D&D 3.x attack, entered by hand or with optional semantic context
(creature description, subtype...), converts through the full pipeline into a
domain `MoveCard` and comes out as JSON.
It has been exercised against the real Gemini API repeatedly, not just mocked —
including four independent full-dataset runs (65 real attacks each) kept for
review: classification-only, through the complete pipeline without semantic
context, through the complete pipeline again with semantic context added, and
a fourth time after adding a description-length constraint to the
classification prompt.

On top of that vertical slice, the `MoveCard` domain object can now be
rendered into an actual printable HTML/CSS card, and every card the
project has produced against the real API can be browsed in a static
gallery page with a raw-input/classification/JSON drill-down per card —
live at <https://alteredlilac.github.io/MonsterForge/>, see
[RENDERING_AND_GALLERY.md](./RENDERING_AND_GALLERY.md) for what that
demonstrates.

A confidence-gated human review step now sits between LLM classification
and the deterministic conversion stages: a low-confidence classification
is shown to a reviewer (raw attack, full LLM context, the classification
itself) before it's trusted downstream, with the option to approve it
as-is, correct specific fields directly, reject it outright (no card is
produced), or rerun the classification — optionally with a different
prompt template — and review the new result under the same menu.

The current test suite contains 532 passing tests, 0 failing.

Persistence and an HTTP API are designed in detail but not yet built —
see [Limitations](#limitations--not-yet-built) below.

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

- **Confidence-gated human review** (`validation/`): a classification
  below a configurable confidence threshold — or every classification,
  if forced on for data-collection purposes — is shown to a reviewer
  (the raw attack, the full LLM context, and the classification itself:
  description, move type, range, confidence, rationale) before the
  pipeline continues downstream. The reviewer can approve it as-is,
  correct `description`/`move_type`/`move_range` directly, reject it
  outright (no card is produced), or rerun the classification — with an
  optional extra note and/or a different prompt template — and review
  the new result under the same menu, repeatable until a decision is
  made. `convert_attack()` now returns `None` rather than always a
  `MoveCard`, for a rejected review or a blank submission (an attack
  with every field empty is skipped before any LLM call at all, rather
  than being classified and then failing downstream).

- **CLI entry points** (`python -m monsterforge.entrypoints.<name>`):
  - `convert_attack_cli` — hand-enter an attack (+ optional context), get
    its MoveCard JSON; triggers the interactive human review above when
    the classification's confidence is low.
  - `test_llm_prompt_cli` — render any Jinja2 prompt template and send it
    to the real LLM client, for iterating on prompts directly.
  - `collect_real_classifications` — batch tool running all 65 cases in
    `SAMPLE_ATTACKS` through just `classify_attack()` against the real API.
  - `collect_real_pipeline_conversions` — batch tool running all 65 cases
    in `SAMPLE_ATTACKS_WITH_CONTEXT` (the same attacks, paired with real
    semantic context) through the complete pipeline against the real API.
  - `collect_real_pipeline_conversions_with_simulated_review` — the same
    65 cases with human review forced on for every one, using a
    deterministic, non-interactive reviewer that cycles through
    approve/correct/reject so all three outcomes get exercised against
    real pipeline output — an observational run, not a source of genuine
    review judgments.

    All batch tools save raw + parsed results to `entrypoints/output/*.json`
    for manual review, with a 5s delay between calls (configurable per
    script). Deliberately independent scripts making independent rounds
    of real calls, not one reusing another's data — so results can also
    be diffed against each other to see how much a live classification
    varies run to run (including whether the model's self-reported
    confidence is at all stable). **Not** part of the automated test suite:
    real API calls, non-deterministic, several minutes, quota use.
  - `render_sample_cards` / `render_gallery` — render the existing
    `collect_real_pipeline_conversions` output into, respectively, one
    static HTML file per card (a manual QA aid) and the browsable gallery
    page. Pure rendering over already-collected data, no new API calls.

- **A reusable golden-file validation procedure**
  (`tests/tools/generate_expected_outputs.py`, built on the generic
  dataclass/enum flattener in `monsterforge/serialization/plain_data.py`):
  dumps a conversion function's actual output over a sample set for one-time
  human review, then the corrected file becomes a committed regression
  fixture. Not specific to attacks — meant to be reused for future conversion
  pipelines (feats, spells, special qualities) needing the same
  validate-once-then-pin workflow.

- **`MoveCard` → printable HTML/CSS card** (`rendering/`), sharing the
  same `serialization/` output the future HTTP API will return rather
  than converting from the domain model independently. Every card
  section has a deterministic size regardless of content — free text
  (the LLM-generated description in particular) is capped rather than
  letting the card grow, matching a physical card's fixed footprint.
  See [RENDERING_AND_GALLERY.md](./RENDERING_AND_GALLERY.md).

- **A static gallery of every card produced against the real API**: one
  page, a clickable entry per sample, each opening a raw-input /
  classification / JSON / rendered-card drill-down — real pipeline
  output, not hand-picked examples.

## Test coverage

**532 passing, 0 failing.** A set of 9 pre-existing failures (unrelated
to the attack pipeline itself — stale tests in `tests/domain/`,
`tests/rules/dnd/v3x/`, and `tests/structured_data/dnd/v3x/`, left over
from earlier field/behavior changes elsewhere in the codebase that the
tests hadn't caught up with) has since been fixed in a dedicated pass,
along with one real bug found in the process: `rules/dnd/v3x/
vitality_tables.py`'s hit-die table was missing an entry for D2, present
in `DESIGN.md`'s own LIFE table but absent from the code — a creature
with `hit_dice_type=D2` would have raised `KeyError`. A second bug found
later the same day, in `damages_converter.py` (a bonus-only typed damage
component silently defaulting to PHYSICAL), came with its own dedicated
test file — previously zero coverage on that file, now covering all 8
damage-classification branches and every resolver.

The confidence-gated human review work (`validation/`, the interactive
review CLI, rerun) added 35 new tests: `needs_review()`'s four
confidence/force-review combinations, the review CLI's branching logic
(enum retry-on-invalid-input, range correction, rerun's note-appending
and failure handling), and the pipeline wiring (the blank-attack
short-circuit, all three review outcomes, and that review is skipped
entirely when no handler is supplied). Entry-point helper modules with
real branching logic get dedicated tests in this project — batch
data-collection scripts and thin CLI wrappers that only glue together
already-tested logic don't.

## Limitations / not yet built

Deliberately out of scope for "MVP zero", to keep it small enough to
ship:

- **`FullAttack`** — only a single `Attack` converts; multiple/iterative
  attacks aren't handled yet.

- **Persistence** — no database; every conversion is computed fresh,
  with no stable/deterministic card IDs across runs.

- **HTTP API** — no FastAPI layer; the pipeline is reachable only via
  the CLI entry points.

- **Other `MoveCard` sources** — only attacks produce move cards today;
  talents, spells, and special qualities aren't wired in
  (`transformation/dnd/v3x/converters/move_converter.py` remains an
  intentional stub for when a second source exists).

All of the above is designed in detail but not yet built: persistence
with stable card identity derived from a content fingerprint (so the
same attack always resolves to the same card, even across separate
runs), and a FastAPI HTTP layer. Rendering a `MoveCard` into a printable
card and a confidence-gated human review step for low-confidence LLM
classifications — both originally part of this same "later" bucket —
have since moved out of it and are built; see
[RENDERING_AND_GALLERY.md](./RENDERING_AND_GALLERY.md) for the former.
The human review step is still CLI-only and stateless — a web form and
a persisted review history remain part of the "later" bucket above.

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

  **Follow-up**: a second sample file
  (`entrypoints/sample_attacks_with_context.py`) pairs the same 65
  cases with real semantic context — creature description, subtype,
  and, for the attacks known to need it, the actual source text stating
  their range — and a fresh full-pipeline run against the real API
  cleared 10 of the 11 errors that run produced (the one remaining
  error was the intentional blank placeholder case, not a real attack
  — see below for how that error was resolved too, later on).
  This reframes the finding above: the gap wasn't primarily a
  `KNOWN_ATTACKS` coverage problem, it was a missing-context problem —
  the LLM resolves a range correctly once the source material actually
  states one. `KNOWN_ATTACKS` as a fallback for genuinely
  context-free lookups remains worth keeping, just not the main fix.
- [PIPELINE_ARCHITECTURE.md](./PIPELINE_ARCHITECTURE.md) was revised to settle
  an open question about the (at the time not-yet-built) `rendering/` stage:
  whether it should share the same `serialization/` output as `api/`, or
  convert from `domain/` independently. Settled on sharing — including the
  same reduction of referenced cards (e.g. `MoveCard.cards_to_add`) to
  `{"name", "id"}` — once it became clear that reduction isn't a
  network-payload optimization but a consequence of the physical card
  format itself (standard Magic-sized cards, ~63×88mm, can't fit another
  card's full contents). A superseded dev-note proposing an earlier,
  less-motivated version of the same fork was removed once its content
  was folded in.
- Once `rendering/` was actually built and used to browse many real
  cards side by side in the gallery, the card's fixed-height layout
  surfaced the description field's real character budget (~180-190
  characters before the card's own line-clamp would truncate it). That
  number was fed back into the classification prompt as an explicit
  160-character cap, then verified — not just assumed to work — by
  running the full 65-case sample set against the real API a third
  time and comparing description lengths against the two earlier runs.
- The one remaining error from the follow-up above (the blank
  placeholder case) turned out to be a real, if minor, inefficiency:
  the pipeline still made a real LLM call on a completely empty
  submission before failing with `UnknownAttackRange` downstream.
  Fixed with an explicit short-circuit — an attack with every field
  empty is now skipped before any LLM call, treated as an empty
  submission rather than something to classify. Verified against a
  fresh full-pipeline run of the same 65 cases: 0 errors this time,
  the blank case now recording no LLM response and no card rather than
  an error. The batch collector script that produces this dataset
  calls the deterministic conversion stages directly (to capture the
  raw LLM response, which the pipeline's own entry point doesn't
  expose), so it needed the same short-circuit applied to it
  separately rather than inheriting it automatically.

## Documentation housekeeping

The root [README.md](../../README.md) was rewritten: it now links correctly
to `monsterforge/docs/` (it previously pointed to a root-level `docs/` folder
that never existed), distinguishes current status from the original vision,
and no longer mentions the PyQt5 desktop tool from the original plan (see
[Architecture](./PIPELINE_ARCHITECTURE.md), superseded by a FastAPI JSON API
serving both `api/` and `rendering/` — the latter still unbuilt at the time
of that rewrite, since built, see above). The original README is
kept for reference at
[monsterforge/docs/archive/README_v1.md](./archive/README_v1.md).

The full commit history was also audited against this project's own
commit-message and documentation conventions and corrected where it
fell short (a handful of early commits predating those conventions,
plus a few written by an AI collaborator that didn't fully follow them)
— consistency in `git log` was treated as worth the one-time rewrite,
since this repository was still private and unshared at the time of
that audit (it has since been made public, with the gallery published
via GitHub Pages).

All remaining Italian-language inline comments across `structured_data/`
and `domain/` (left over from the project's early development, before
an English-only identifiers-and-comments convention was firmly
established) were translated to English or removed where they only
restated the field name — full-codebase language consistency, ahead of
making the repository public.
