# MVP Zero — Attack → MoveCard Vertical Slice

A case study in this project's first complete pipeline slice: a single
D&D 3.x attack, converted end-to-end from raw input into a fully-formed
domain `MoveCard`, serialized to JSON. This document explains what the
slice demonstrates about the project's engineering discipline, not just
that it works — see [PROJECT_STATUS.md](./PROJECT_STATUS.md) for the
current numbers (tests passing, what's built vs. planned).

## What it is

The vertical slice:

```
raw_fields.Attack → structured_data.Attack → domain.MoveCard → JSON
```

Every stage in [PIPELINE_ARCHITECTURE.md](./PIPELINE_ARCHITECTURE.md)'s
diagram between "raw input" and "domain model" is exercised by this one
path, for the single case of a D&D attack. It's the first place in the
codebase where the LLM classification layer, the deterministic
regex/rules layer, and the domain model all connect and run together
against a real API, not mocks.

## Why this specific case

The reference case is a bite attack with a secondary effect: `"1d6+3
plus trip"`. A plain attack with no secondary effect would only exercise
the easy path. This one forces the harder branch too: the "plus trip"
portion becomes its own linked `MoveCard` ("Trip"), referenced from the
bite's `cards_to_add` field rather than being flattened into a
description string. Choosing the harder case up front, instead of the
simplest one that would "just work," is what actually tests whether the
architecture holds together.

## What it demonstrates

**Two-stage parsing.** The attack text never goes directly from raw
input to a typed domain object. It passes through an intermediate
`raw_fields` representation (near-verbatim strings, mirroring how the
attack appears in a stat block) before any typed interpretation happens.
This decouples the fragility of the source format from the logic that
interprets it, and lets a case be tested by hand-constructing a
`RawAttack`, with no scraping or network involved.

**A hard boundary between deterministic and probabilistic parsing.**
Attack damage strings (`"4d8+17/18-20/×3 plus poison"`) look like free
text but are actually fixed notation — dice expressions, critical
thresholds, damage types — all parseable with regex and lookup tables.
None of that goes through the LLM. The one genuinely free-text piece —
what a linked ability like "trip" or "poison" actually *is* — is the
only part an LLM classifies. This split is enforced by construction: the
regex-based parser that extracts damage/critical/effects from an attack
string has no LLM dependency at all, and can be (and is) tested without
mocking anything.

**A pure conversion function, on purpose.** The function that builds a
`structured_data.Attack` from raw input takes the LLM's classification
result as a parameter, rather than calling the LLM itself. That single
decision means the conversion function can be tested by constructing the
classification result by hand — no mocking required — and it creates an
explicit seam where future work (caching, human review of low-confidence
results) can intercept the classification without touching this function
again.

**Golden-file validation for regex-heavy parsing.** Hand-verifying dozens
of real attack strings against a regex parser, one at a time, doesn't
scale and doesn't stay verified as the parser changes. Instead: the
parser's actual output over a full sample set is generated once, checked
by hand, and the corrected file becomes a committed regression fixture —
every future change to the parser is checked against it automatically.
The same generator is reusable for any future parsing pipeline that
needs the same kind of validation, not rewritten per case.

## Verified against the real API

This slice has been run against the live LLM API repeatedly, not just
against mocks — including full runs across a real sample set of
attacks. See [PROJECT_STATUS.md](./PROJECT_STATUS.md) for current test
counts and what those live runs found, including a known, intentionally
unfixed gap in range detection for a handful of ranged attacks.

## What's deliberately out of scope

Multiple/iterative attacks per creature (`FullAttack`), and any
`MoveCard` source other than a single `Attack` (talents, spells, special
qualities), are intentionally not handled by this slice. Both would
currently mean either a dispatcher with a single real branch, or logic
for a case with no second real example yet — premature generalization
for requirements this milestone doesn't have. See
[PROJECT_STATUS.md](./PROJECT_STATUS.md#limitations--not-yet-built) for
the full list of what's planned but not yet built.
