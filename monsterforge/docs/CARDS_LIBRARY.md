# Cards Library — Reopening History Without Corrupting the Present

A case study in what it takes to expose an append-only history to a
human for browsing *and* editing, without letting a view into the past
accidentally overwrite what's currently active. See
[PROJECT_STATUS.md](./PROJECT_STATUS.md) for current test counts.

**See it live:** browse every card the demo has produced so far at
<https://monsterforge-tohp.onrender.com/library/cards> — search by
name or id, open an entry's History tab, and follow a link to reopen
an older attempt for a fresh decision.

## What it is

```
GET /library/cards
        |
        v
Every raw field with a resolved active result, searchable by name
(substring) or id (prefix) — one with no active result yet is
skipped; one whose active result is rejected stays, flagged
        |
        v
GET /library/events/{event_id}/review
        |
        v
Reopens ANY past classification event for review — not just the
one currently active for that raw field
        |
        v
    Reviewer decides: approve / correct / reject / rerun
        |
        v
Is this decision about the raw field's currently active event
(or does the raw field have no active event yet at all)?
        |
   yes -+- no
        |    |
        v    v
   becomes    recorded in its own history,
   the new    the active pointer is left
   active     untouched
   result
```

The library reads from the same nine-table schema described in
[PERSISTENCE.md](./PERSISTENCE.md) — this document is about what
happens once that history is no longer just an internal cache, but
something a person can browse, search, and act on directly.

## What it demonstrates

**Reopening an old event and superseding the active one are two
different actions, not one.** A reviewer can pull up any past attempt,
not only the one currently in effect — but a decision made on an old,
already-superseded attempt shouldn't be able to reach in and disturb a
genuinely good current result just because a human happened to look at
that old attempt again. The fix checks whether the event being decided
is actually the raw field's current active one (or its very first
decision ever, when nothing is active yet) before letting a decision
touch the active pointer at all. Rejecting an old attempt is still
recorded in its own history either way — it just doesn't reach forward
and take over.

**A saved artifact's fields need to come from the row that actually
produced it, not just any row with a plausible answer.** The
classification shown for a saved card was originally read from the
event that *originated* it, not the attack's actual current one —
harmless when a reviewer approves a classification as-is (the two are
identical in that case), wrong after a correction, since the library
kept showing pre-correction values instead of what a reviewer actually
changed them to. Found by deliberately testing a correction (flipping
a physical attack to magical) rather than by a test suite that had
only ever exercised the approval path.

**"Current" isn't one question — it depends which current you're
asking about.** A raw field's original submitted name never changes;
a correction to it is recorded per-event, not per-attack. Resolving
"what name is in effect right now, for the library's main listing" is
a different question from "what name was in effect immediately after
*this specific* old event" — needed when reopening that event for
review, so it doesn't jump ahead to a correction that, from that
event's own point in history, hasn't happened yet. Two separate
resolution functions answer these two separate questions; collapsing
them into one would silently answer the wrong one some of the time.

**The same missing data means something different depending on where
it's found.** If the raw field's *currently active* event has no
saved card behind it, that's a real data-integrity anomaly — a save
interrupted mid-pipeline, reported loudly rather than papered over. If
an *old, reopened* event has no saved card, that's completely normal —
a superseded run a rerun overtook before anyone ever decided on it, or
a rejection, neither of which ever produces a card. Same absence, two
different meanings, handled two different ways on purpose.

**A rejected result stays visible, not hidden.** A raw field whose
active attempt was rejected still gets a library entry — flagged, with
its raw input and full history still reachable — rather than
disappearing entirely. A rejection reachable through a reopened-event
link has to stay reachable itself, history included, or an earlier
good attempt underneath it could never be found and reactivated again.

## Verified against the real pipeline

Exercised against the real repository functions and web routes, not
staged fixtures: reopening a past, already-superseded event and
confirming that approving it reactivates it over whatever was active
before; a rejected reopened attempt no longer deactivating a good
active result; a reopened attempt correctly carrying over its own
saved image, or tolerating a blank one when it never had a card at
all; and a name correction resolving correctly whether reopening a
saved card or an old, already-superseded attempt. See
[PROJECT_STATUS.md](./PROJECT_STATUS.md) for the current count.

The library above is reachable at the same URL as the rest of the live
demo, not a separate staging environment — what it shows today is
exactly what that test suite already covers, not a hand-picked
example.

## What's deliberately out of scope

- **Search is a plain match, not fuzzy or ranked** — a name match is a
  case-insensitive substring, an id match is a prefix; there's no
  relevance ranking or typo tolerance.
- **No authentication** — anyone who can reach the live demo can
  browse and reopen every saved result. Appropriate for a single
  public demo instance today, not something a real multi-user product
  could ship unchanged.
- **Nothing to browse from the CLI channel** — it doesn't persist any
  classification yet (see [PERSISTENCE.md](./PERSISTENCE.md)), so
  there's no history for this library to expose from that side.
- **Decks** — a complete assembled unit of play built from multiple
  cards — aren't part of this library; the underlying table exists,
  but nothing populates it yet.
