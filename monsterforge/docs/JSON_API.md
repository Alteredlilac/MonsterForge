# JSON API — A Second Consumer, Not a Second Source of Truth

A case study in what it takes to add a genuinely independent consumer
on top of a pipeline that was designed weeks earlier to eventually
have one, without duplicating the logic that consumer needs to stay
correct. See [PROJECT_STATUS.md](./PROJECT_STATUS.md) for current test
counts.

**See it live:** <https://monsterforge-api.onrender.com/docs> —
`GET /api/cards` lists eight real, pre-seeded cards immediately;
`POST /api/cards` classifies and persists a new attack against the
real Gemini API, right from the Swagger form (free-tier hosting: the
first request after inactivity can take ~30–50s to wake up).

## What it is

Two independent FastAPI applications, deployed as two independent
Render services, sharing nothing but the layers underneath both:

```
      pipeline/ + db/ + validation/
   (fingerprint cache, confidence gate,
      append-only event log, shared)
                   |
       +-----------+-----------+
       |                       |
       v                       v
  ui/app.py               api/app.py
  (Bootstrap forms,       (JSON only --
   human review)           no review, no DELETE)
       |                       |
       v                       v
  Dockerfile               Dockerfile.api
  Render service A          Render service B
```

`POST /api/cards`'s own decision sequence mirrors `/convert`'s exactly,
just returning JSON instead of HTML:

```
POST /api/cards
        |
        v
Fingerprint already has an active, non-rejected result?
        |
   yes -+- no
        |    |
        v    v
  return    classify_attack() -- a real Gemini call
  the       |
  existing  v
  card      needs_review()? (same shared confidence
            threshold /convert reads, never a value
            the request itself supplies)
                   |
              yes -+- no
                   |    |
                   v    v
            report            build the card, persist it,
            pending_review    activate the event, return it
            (event recorded,
             never activated)
```

`POST /api/cards/{id}/rerun` follows the same classify-then-gate tail,
but always skips the fingerprint check at the top — a rerun is a
deliberate manual retry, never deduplicated against a cache built to
avoid *accidental* repeats.

**What each route is for:**

| Route | What it's for |
|---|---|
| `GET /api/cards` | List every attack with a real, currently active card — filterable by name or id |
| `GET /api/cards/{raw_field_id}` | One saved card's full content |
| `POST /api/cards` | Create a card for a new attack, or return the existing one if it's already been submitted |
| `POST /api/cards/{raw_field_id}/rerun` | Reclassify an existing attack from scratch, ignoring any cached result |

Full parameter-level detail (request bodies, every status code, try-it-
yourself forms) lives at `/docs`, generated automatically from the same
Pydantic models the routes validate against — not duplicated here,
since a hand-written copy could drift from the real schema in a way
the live one never can.

## What it demonstrates

**A second consumer proves an earlier architectural bet.** The pipeline's
domain model has forked into `serialization/` → `{api/, rendering/}`
since early in this project, well before an API existed to prove the
"api/" half of that fork was ever real. Building this API needed zero
changes to `serialization/domain_to_json.py::card_to_json()` — it
already produced exactly the JSON this API returns, because that was
the point of deciding the fork's shape that early.

**The confidence gate is reused, not reimplemented, so cross-channel
consistency is structural, not merely tested-in.** `needs_review()`
reads the same shared confidence threshold both `/convert` and
`POST /api/cards` read — no request field anywhere in this API can
override it. That omission was deliberate, not an oversight: the same
attack at the same confidence must resolve identically whether it
arrives from the web form or the API, and the only way to guarantee
that is to never let either channel configure the gate per request.

**Two independently deployable services, sharing nothing but what's
underneath them.** `api/app.py` and `ui/app.py` are separate FastAPI
instances with their own `lifespan()`, built from two nearly-identical
Dockerfiles (`Dockerfile`, `Dockerfile.api`) that differ only in their
final line. Deliberately two files rather than one Dockerfile with a
per-service command override on Render: the two applications are
conceptually independent branches of the same pipeline, even though
today's implementation happens to be nearly identical — an override
would record that near-identity as if it were permanent.

**A public demo needs real data, but never at the cost of a live API
call.** The deployed instance's eight example cards are seeded by
replaying an already-verified Gemini classification through the same
deterministic functions the create route itself calls
(`raw_to_structured_attack()`, `attack_converter()`) — no network call
at seed time. A Render free-tier instance restarts often; reclassifying
the same eight attacks on every restart would spend real quota for no
new information, and risks a different confidence landing a demo card
in pending review instead of ready to view. The seed is also
idempotent for free: it reuses the same fingerprint-lookup function
the create route uses, so a second run (say, a restart that didn't
actually clear the disk) finds every entry already active and adds
nothing.

**Deliberate exclusions, stated as design decisions, not gaps.** No
route here ever resolves an ambiguous classification — a low-confidence
result is reported as pending, never auto-approved to make the response
simpler — and no route deletes anything, matching the schema itself:
nothing is ever deleted anywhere in this project, only superseded.
Both are boundaries decided before writing a line of the API, not
limits discovered afterward.

**Interactive documentation came from models the routes needed anyway,
not extra work.** Every request/response shape is a Pydantic model
(`api/models.py`) built for validation — `AttackCreateRequest` rejects
an unknown `attack_type` or a `range_value` given without its unit
before any handler code runs. FastAPI turns those same models into the
Swagger UI at `/docs` and the schema at `/openapi.json` automatically;
the only line written specifically for that page was its title.

## Verified against the real pipeline

The local test suite exercises every branch of all three routes
against a real (in-memory) database — auto-approval, the fingerprint
cache hit, pending review, a previously rejected attack refusing to
reclassify, an unknown id or prompt template, model-unavailable and
other classification failures, the same range/attack-type validation
`/convert` already enforces, rerun's own fingerprint-skip and
effective-name resolution, and the demo seed's idempotency and
secondary-effect preservation. See
[PROJECT_STATUS.md](./PROJECT_STATUS.md) for the current count.

Separately, against the live deployment itself, not just the local
suite: `GET /api/cards` returns the eight seeded cards on the real
Render instance, `GET /docs` serves the Swagger UI with this project's
own title, and `POST /api/cards` was exercised directly through that
live Swagger form, producing a real classification against the real
Gemini API.

## What's deliberately out of scope

- **No human review of any kind** — approve, correct, and reject exist
  only on the web, through `POST /review`. This API can create or
  retry a classification and report that one is pending, but never
  resolves the ambiguity itself.
- **No `DELETE`** — the schema is an append-only event log by
  architecture; a real delete endpoint would contradict the model the
  rest of the project already commits to, not just add a missing verb.
- **No authentication** — anyone who can reach the live demo can
  create cards against the real Gemini key. Appropriate for a single
  public demo instance, not something a real multi-user product could
  ship unchanged.
- **No rate limiting** — the same free-tier Gemini key backs both live
  deployments; the realistic exposure is temporary quota exhaustion,
  not cost, and is accepted identically for both rather than treated
  as a new risk introduced by this API specifically.
- **The CLI doesn't reach any of this** —
  `pipeline.attack_pipeline.convert_attack()` still computes every
  conversion fresh, with no persistence and no fingerprint cache;
  wiring it in is tracked as future work, not started here.
