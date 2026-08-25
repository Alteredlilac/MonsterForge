# Project Status

Snapshot of where MonsterForge stands as of August 25, 2026.
For the system's design and long-term architecture, see [PIPELINE_ARCHITECTURE.md](./PIPELINE_ARCHITECTURE.md)
and [DESIGN.md](../../DESIGN.md). For how the LLM layer specifically is
structured, see [LLM_ARCHITECTURE.md](./LLM_ARCHITECTURE.md). For how a
`MoveCard` becomes a printable card and how that's showcased against real
pipeline output, see [RENDERING_AND_GALLERY.md](./RENDERING_AND_GALLERY.md).
For the conversion + human review flow over the web, live, and how to write
a valid attack, see [WEB_UI_AND_REVIEW.md](./WEB_UI_AND_REVIEW.md).

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

That same conversion-and-review flow is now also reachable over the web
(FastAPI + Bootstrap, no framework changes needed on the pipeline side) —
**[try it live](https://monsterforge-tohp.onrender.com/convert)** (free-tier
hosting: the first request after inactivity can take ~30–50s to wake up) —
not just the CLI — with a few things the CLI still doesn't have: an
optional image URL for the card, friendlier error messages instead of a
raw crash on malformed input, and a way to revisit and correct a card's
classification even after it was auto-approved, which previously had no
correction path at all. Rerun (reclassify with an optional note and/or
a different prompt template, then review the new result) now works on
both channels — the web version lands on the same review form/route as
Approve/Correct/Reject, not a separate one, and on any failure falls
back to the classification that was already in effect rather than
losing the reviewer's place.

Which prompt template classifies an attack is now a real choice, not
just a hardcoded default: four curated variants exist (the baseline,
one that keeps the LLM from re-describing the creature in the attack's
own description, one that pushes confidence down when key information
is missing, and one combining both), selectable on first classification
(CLI and web) and on rerun (CLI and web) from the same single source of
truth.

The current test suite contains 590 passing tests, 0 failing.

Persistence and a JSON API for external consumers are designed in detail
but not yet built — see [Limitations](#limitations--not-yet-built) below.

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
  Both the standalone card page and the web UI print at the card's real
  ~63×88mm size (a shared `@page`/`transform: scale()` partial, working
  on both A4 and US Letter without needing to detect which is active)
  — the gallery deliberately doesn't. See
  [RENDERING_AND_GALLERY.md](./RENDERING_AND_GALLERY.md).

- **A static gallery of every card produced against the real API**: one
  page, a clickable entry per sample, each opening a raw-input /
  classification / JSON / rendered-card drill-down — real pipeline
  output, not hand-picked examples. Browsing only — unlike the
  standalone card page or the web UI below, the gallery doesn't offer
  printing (see [RENDERING_AND_GALLERY.md](./RENDERING_AND_GALLERY.md)).

- **The conversion + review flow over the web** (`ui/`, FastAPI +
  Bootstrap — see [WEB_UI_AND_REVIEW.md](./WEB_UI_AND_REVIEW.md)):
  `GET`/`POST /convert` collects a raw attack and classifies
  it; `POST /review` handles approve/correct/reject/rerun; `POST
  /review/edit` reopens review for an already-rendered card without
  reclassifying — closing a gap the CLI still has, where a
  high-confidence but wrong classification has no correction path once
  the JSON is printed. Name is required, a ranged/ranged touch attack
  needs a resolvable range (either a structured value/unit or prose
  already stating one), and a range/unit given explicitly overrides
  whatever the LLM returns for it rather than trusting its own
  reconstruction of a value that was already known. Every rendered card
  carries an optional, user-supplied image URL end to end.

- **Choosing which prompt template classifies an attack** (CLI and
  web, first classification and rerun alike): four curated variants —
  the baseline, one keeping the LLM from re-describing the creature in
  the attack's own description, one that lowers confidence when key
  information is missing, and one combining both — defined once
  (`llm/semantic_classification/attacks.py`'s
  `ATTACK_PROMPT_TEMPLATE_OPTIONS`) and validated against that same
  list everywhere a choice is offered, never a second hardcoded copy.

## Test coverage

**590 passing, 0 failing.** A session hardening the web review flow,
fixing the Jinja2 autoescape gap, adding print support to the standalone
card page, and building prompt-template selection/rerun added 38 tests:
a regression test reproducing the autoescape bug live (an apostrophe in
an LLM rationale corrupting a hidden form field), coverage for the new
mandatory-name/structured-range/melee-disables-range behavior on
`/convert`, the `UnknownAttackRange` bounce-back on both `/convert` and
`/review`, the four prompt-template variants' rendered output (and an
integrity check that every curated template path actually exists on
disk), the CLI's and web's template-choice prompts, and rerun's five
outcomes (successful reclassification, note appended, unknown template,
model unavailable, and any other classification failure — all three
failure cases verified to leave the original classification untouched).

A set of 9 pre-existing failures (unrelated
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

The web layer (`ui/`) added 20 more: all four review outcomes plus the
blank-attack short-circuit over HTTP (FastAPI's `TestClient`, the LLM
always mocked), the constrained `attack_type` dropdown rejecting an
unrecognized value, friendly-error responses for both a classification
failure and a downstream parsing failure, the edit-after-render round
trip, and image URL propagation end to end.

## Limitations / not yet built

Deliberately out of scope for "MVP zero", to keep it small enough to
ship:

- **`FullAttack`** — only a single `Attack` converts; multiple/iterative
  attacks aren't handled yet.

- **Persistence** — no database; every conversion is computed fresh,
  with no stable/deterministic card IDs across runs.

- **JSON API for external consumers** — `api/` is still an empty stub;
  the pipeline is reachable via the CLI or the human-facing web form
  (`ui/`), not as machine-readable JSON over HTTP. Deliberately planned
  for after persistence exists (see below) — an API returning ephemeral,
  non-cacheable conversions has little value on its own.

- **Other `MoveCard` sources** — only attacks produce move cards today;
  talents, spells, and special qualities aren't wired in
  (`transformation/dnd/v3x/converters/move_converter.py` remains an
  intentional stub for when a second source exists).

All of the above is designed in detail but not yet built: persistence
with stable card identity derived from a content fingerprint (so the
same attack always resolves to the same card, even across separate
runs), and the JSON API above. Rendering a `MoveCard` into a printable
card, a confidence-gated human review step for low-confidence LLM
classifications, and that whole flow exposed over the web — all
originally part of this same "later" bucket — have since moved out of
it and are built; see [RENDERING_AND_GALLERY.md](./RENDERING_AND_GALLERY.md)
for the former. The review flow's history still isn't persisted
anywhere (CLI or web) — that lands together with the fingerprint work
above.

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
- Building the web form surfaced a real classification-parsing gap:
  `is_melee()`/`is_touch()` only match fixed English substrings, so a
  free-text `attack_type` field accepted a value like "mischia"
  (Italian for melee) and silently treated it as a ranged attack
  instead of erroring — found via live testing, not code review, and
  fixed by constraining the web form's `attack_type` to a dropdown
  rather than changing the parser.
- A hidden form field carrying a JSON blob wasn't HTML-escaped in a new
  template, corrupting the attribute it was embedded in — traced to
  `rendering/`'s Jinja2 environment never actually enabling autoescape
  for any of its `*.html.jinja2`-suffixed templates (`select_autoescape`
  checks for a literal `.html` extension, which none of these filenames
  end in). First fixed locally for the affected field only; a later
  session found the identical gap independently in `ui/`'s own,
  separately-built Jinja2 environment (Starlette's `Jinja2Templates`
  hits the same extension check) — reproduced live with an apostrophe
  in an LLM-generated rationale breaking a hidden field and crashing
  `/review` with an unhandled `JSONDecodeError`. Both environments now
  set `autoescape=True` explicitly rather than relying on
  `select_autoescape()`, closing the gap for good instead of per field.
- A first attempt at shrinking an oversized card to fit the screen used
  pure CSS (`calc(80vh / 815px)` as a `scale()` argument) — confirmed to
  have no effect in a real browser test, since cross-browser support for
  dividing mixed CSS units into a plain number isn't reliable yet.
  Replaced with a small vanilla JS snippet instead.
- FastAPI's `Form(...)` (required) treats an empty string exactly like a
  missing field — a legitimately blank attack modifier reaching
  `/review` produced a hard 422 "Field required" on every decision,
  including Reject, instead of being accepted as the empty value it
  actually is. Fixed by defaulting those fields to `Form("")` instead of
  `Form(...)`, reserved for fields that must never be blank
  (`semantic_result_json`, `decision`).
- A dice-based damage roll with a negative modifier large enough to
  offset its own average (e.g. `1d4-2`: average 2, minus 2 = 0) rendered
  as "0 PHYSICAL DAMAGE" on the card — found by inspecting real gallery
  output, not something the original algorithm design had considered.
  D&D damage always deals at least 1 point per hit; fixed by clamping
  the dice-plus-modifier sum to a minimum of 1 in
  `damages_converter.py`'s same-damage-type branch.

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
