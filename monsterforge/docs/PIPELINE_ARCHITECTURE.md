# MonsterForge — Pipeline Architecture

This document fixes the complete conversion pipeline, from raw scraped
text to the rendered card, and the architectural decisions made to get
there. It builds on and makes explicit what's already described in
`DESIGN.md`, adding the level of detail that emerged during the
development of `structured_data/`.

## Why this document

During the development of `structured_data/dnd/v3x/`, a few questions
came up about exactly where to place LLM classification relative to
deterministic parsing, and whether an additional raw-data layer was
needed between HTML and `structured_data/`. This document fixes the
answers reached, so they can be consulted again when writing `parsing/`
and `llm/`.

---

## Complete pipeline schema

```
┌──────────────────────────────────────────────────────────────────────────┐
│  1. RAW HTML                                                             │
│     Downloaded by scraping/, saved as-is in db/ (RECORD DB)              │
│     Single generic table: id, url, type, raw content                    │
└──────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌──────────────────────────────────────────────────────────────────────────┐
│  2a. HTML EXTRACTION  →  parsing/<system>/<version>/html_extraction.py  │
│      Regex / BeautifulSoup, deterministic, per-source if needed          │
│                                                                          │
│      Extracts fields as they appear in the rulebook table, almost       │
│      verbatim, into a dedicated "raw fields" dataclass:                 │
│                                                                          │
│      RawArmorFields(name="...", cost="30 gp", armor_bonus="2", ...)     │
└──────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌──────────────────────────────────────────────────────────────────────────┐
│  2b. RAW FIELDS  →  parsing/<system>/<version>/raw_fields.py            │
│      Dataclasses that mirror the source domain: they reflect the exact  │
│      columns of the game tables (Armor, Weapons, etc.)                  │
│      Fields are still mostly strings, not yet typed/enum                │
│                                                                          │
│      Multi-source convergence point: different HTML sources (different │
│      sites) or manual human input (CLI/form) all produce the SAME       │
│      RawFields                                                          │
│      Bypass point: if only testing the pipeline is needed, a RawFields  │
│      can be built by hand, with no scraping or network at all           │
└──────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌──────────────────────────────────────────────────────────────────────────┐
│  3. STRUCTURED CONVERSION  →  parsing/<system>/<version>/               │
│     structured_conversion.py                                            │
│     Type casting (string → int/enum/dataclass) + decision:              │
│     "does this need semantic classification, or is the object already  │
│     complete?"                                                          │
│                                                                          │
│     ├─► Simple fields/objects (numbers/enums only, no free text)        │
│     │   → go straight into structured_data, no LLM call                 │
│     │                                                                   │
│     └─► Fields with free text to interpret (abilities, talents, spells) │
│         → pass through stage 4 before they can be built                 │
└──────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌──────────────────────────────────────────────────────────────────────────┐
│  4. LLM CLASSIFICATION  →  llm/                                         │
│     ONLY for free-text blocks (special qualities, special attacks,      │
│     feats, spells) that can't be reduced to regex                       │
│                                                                          │
│     A single call per text block, with a fixed output schema            │
│     (Pydantic/dataclass): category, target, duration, usage, AND the    │
│     numeric values already classified into the semantically correct     │
│     field (e.g. "1d4" goes into Damage if it's damage, into EffectGrant │
│     if it's a summoned quantity — the distinction happens in the same   │
│     call, not in two)                                                   │
│                                                                          │
│     Output includes a "confidence" field (transient, never reaches      │
│     domain)                                                             │
└──────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌──────────────────────────────────────────────────────────────────────────┐
│  5. VALIDATION  →  validation/                                          │
│     confidence >= threshold (0.7) → auto-approved                       │
│     confidence <  threshold       → queued for human review (ui/)       │
│                                                                          │
│     Keeps a history of corrections; the final output no longer carries  │
│     "confidence"                                                        │
└──────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌──────────────────────────────────────────────────────────────────────────┐
│  6. STRUCTURED_DATA  →  structured_data/<system>/<version>/             │
│     Now the Creature/Item/CharacterClass is complete: some fields built │
│     in stage 3 (direct regex), others in stage 4+5 (LLM + validation).  │
│     Typed, enum-based, zero leftover raw strings                        │
└──────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌──────────────────────────────────────────────────────────────────────────┐
│  7. TRANSFORMATION  →  transformation/ + rules/                         │
│     Deterministic calculations, zero LLM, zero ambiguity:               │
│     calculate_life_value(), calculate_body_spirit(),                    │
│     calculate_interpretation(), calculate_armor_talisman(),             │
│     calculate_stamina_mana()                                            │
│                                                                          │
│     Content already classified (stage 4/5) is mapped here 1:1 into the  │
│     domain's fields/enums (MoveCard, ItemCard) — no new interpretation  │
└──────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌──────────────────────────────────────────────────────────────────────────┐
│  8. DOMAIN MODEL  →  domain/                                            │
│     Entity(creature_cards, move_cards, item_cards)                      │
│     Final representation, source-independent (D&D or Pathfinder)        │
└──────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌──────────────────────────────────────────────────────────────────────────┐
│  9. SERIALIZATION  →  serialization/                                    │
│     Domain Model → common external structure (JSON-compatible dict)     │
│     Referenced cards (e.g. MoveCard.cards_to_add) are reduced here to   │
│     {"name", "id"} — see decision 6 below for why                       │
└──────────────────────────────────────────────────────────────────────────┘
                              |
              +---------------+---------------+
              v                               v
┌───────────────────────────────┐  ┌───────────────────────────────────┐
│  10a. API  →  api/             │  │  10b. RENDERING  →  rendering/    │
│      dict → HTTP response      │  │      dict → HTML → printable      │
│      (JSON)                    │  │      image (final card)           │
└───────────────────────────────┘  └───────────────────────────────────┘
```

> **Status note.** Stage 5 above diagrams low-confidence classifications
> as routed to `ui/`. The validation design actually settled on later (see
> `.claude/future_plans/EXPANDED_MVP_PLAN.md` §10) is a blocking CLI form
> in `validation/cli_form.py`, not a `ui/` interface — consistent with
> `DESIGN.md`'s "simplest tool" philosophy, and with the fact that the
> original PyQt5 desktop-tool vision was itself superseded (see
> `EXPANDED_MVP_PLAN.md` §2). `ui/` remains an empty, unplanned stub. The
> diagram is left as originally drawn here rather than silently rewritten,
> since it predates that decision; see `PROJECT_STATUS.md` for what's
> actually implemented today — as of this writing, neither `validation/`
> nor `ui/` exist yet.

---

## Key decisions and rationale

### 1. Why a "raw fields" layer is needed between HTML and structured_data

**Problem**: converting directly from HTML to `structured_data` couples
the interpretation/calculation logic to the fragility of the source
format (HTML that changes from site to site, or over time).

**Solution**: an intermediate dataclass layer ("raw fields") that
faithfully mirrors the rulebook's tables (e.g. the exact columns of the
Armor table: name, cost, bonus, penalty...), with fields still mostly
strings.

**Benefits gained**:
- **Multi-source**: different HTML sources converge on the same
  `RawFields` before any interpretation — writing a different
  `html_extraction.py` per source is enough, the rest of the pipeline
  doesn't change.
- **Manual input**: a user can fill in the same `RawFields` structure by
  hand (CLI, or a future form), bypassing scraping and still getting a
  card.
- **Testing without a network**: the entire pipeline (structured_data →
  transformation → domain → rendering) is testable with hand-written
  `RawFields`, with no real scraping and no dependency on BeautifulSoup.
- **Skip LLM when possible**: simple objects (numeric fields only, no
  free text to interpret) go from `RawFields` to `structured_data` with
  only a type cast, never passing through `llm/`.

**Where it lives**: inside `parsing/`, not as a standalone package. It's
not a new architectural stage visible from the outside — it's a detail of
*how* `parsing/` does its job in two steps instead of one.

**Why it isn't a database table**: the idea of persisting this stage as a
SQL table was considered and rejected. Reasons: (1) it would still need a
typed Python representation to be read/written — a DB doesn't "avoid"
dataclasses, it just moves the same complexity onto one more persistence
layer; (2) it would introduce different tables per stat-block type,
contradicting the choice already made for `RECORD DB` to use a single
generic table with a "type" field; (3) this stage is cheap to regenerate
(pure CPU, no network) any time it's needed, starting again from the HTML
already cached in `db/` — there's no real need to persist it.

### 2. Why not an "intermediate JSON" as its own stage

During the initial discussion, a schema came up with an
`HTML → JSON → structured_data` step. This JSON doesn't represent a real
architectural stage with its own rules: it's just the internal way a
parsing library (e.g. BeautifulSoup) returns data before it gets typed.
It doesn't need to be its own module, nor to be persisted: it's a local
working variable inside `html_extraction.py`.

### 3. Where exactly the LLM fits in

The LLM comes into play **only** for free-text blocks that describe
abilities (special qualities, special attacks, feats, spells) — never for
fields with a fixed, predictable format (Hit Dice, Armor Class, Saves,
Abilities), which stay resolved with deterministic regex.

An important point that came up in discussion: classifying the semantic
category (e.g. "is this an attack" vs. "is this healing") and extracting
the numeric values present in the same text (e.g. "1d4") happen **in the
same LLM call**, not in two separate passes. The reason: understanding
*what a number represents* in context (damage? a summoned quantity? a
bonus?) requires the same semantic understanding needed to classify the
ability as a whole — splitting them into two distinct passes wouldn't
have brought any benefit, just one more call.

### 4. Why `CreatureModifier` (and similar concepts) use composition, not inheritance

Not every "variant" of a concept deserves a subclass. The criterion
adopted throughout `structured_data/`: if a category represents a
**delta/modifier** applied on top of a base object (e.g. an archetype
like Lycanthropy applied to a Creature), composition is used (separate
override/additive/modifier fields), not inheritance — because the object
isn't really a special case of the parent, it doesn't share its entire
structural identity.

When, instead, the relationship is a true specialization (e.g.
`PrestigeClass(CharacterClass)`, which is for all purposes a complete
class plus some prerequisites), inheritance remains the correct choice.

### 5. When to extract a shared module vs. keeping fields local

The criterion adopted whenever the same data structure (e.g. `Damage`,
the components of `effect_mechanics.py`) serves several independent
modules (attacks, special qualities, spells, items, talents): extract it
into a shared module, don't duplicate it. The practical test used: *"am I
duplicating the same thing, or do I have two different things that
belong to the same conceptual category?"* — in the first case, a shared
module with a single class; in the second, a shared module with several
related classes (like `creature_stats.py` or `effect_mechanics.py`).

### 6. Why referenced cards stay reduced to name/id in rendering too

With the introduction of the HTTP interface (`api/` + `serialization/`),
the question came up of whether the pipeline should fork right after
`domain/` into two independent conversions (one for `api/`, one for
`rendering/`), or converge first on a single `serialization/` stage
shared by both. Specifically, whether reducing nested cards (e.g.
`MoveCard.cards_to_add`) to `{"name", "id"}` was a compromise specific to
network transport, to be avoided for rendering (which might seem to need
the full detail to draw the card).

**It isn't.** This game's physical card format is a standard size
(Magic-style, about 63×88mm) — there's no room to print the full fields
of several referenced cards inside the card that references them; even a
single nested card expanded in full would make the card unmanageable. The
referenced card (e.g. "Trip") already exists as its own card in the deck,
with its own rendering — the card that references it only needs to be
able to name it, not reproduce its contents.

The reduction to name/id is therefore the correct representation of "a
reference to another card in the deck" in this system, dictated by the
card's physical format even before the API — the printed-space constraint
is tighter, and further upstream, than the network-payload one, and it
holds everywhere one card references another, not only at the HTTP
boundary.

**Consequence**: `serialization/` stays a single stage shared by `api/`
and `rendering/` — the fork happens after that stage, not before.

---

## What does NOT change relative to `DESIGN.md`

This document adds detail, it doesn't replace the founding decisions
already fixed in `DESIGN.md`:
- The deterministic (`rules/`+`transformation/`) vs. probabilistic
  (`llm/`) separation stays unchanged.
- The "dataclasses everywhere, no external JSON/Pydantic for
  configuration" principle stays unchanged.
- The general `RPG Data → Entity Model → Cards` flow stays unchanged;
  this document only details the internal stages of `parsing/`.

---

### Note: StatBlock/CreatureBuild aggregator (not implemented)

The need for an aggregator for multiclass characters with archetypes
(e.g. "bugbear, thief 5, wizard 2, half-fiend") was evaluated. Deferred:
the content scrapable from the three core rulebooks is almost entirely
represented by a single Creature. Revisit only if the project extends to
adventure-module NPCs with multiclass builds.
