> **Historical document.** This is the project's original README, kept for
> reference (original vision and pitch). It predates the API/serialization
> layer, the LLM model-fallback work, and describes a PyQt5 desktop
> validation tool that was never built and is no longer planned. For the
> current README see [../../../README.md](../../../README.md); for the
> current project state see [../PROJECT_STATUS.md](../PROJECT_STATUS.md).

# MonsterForge — RPG Data Transformation Engine

A Python-based pipeline that transforms semi-structured RPG data into normalized, game entities through deterministic rules and LLM-assisted classification.


![MonsterForge creature card example](./docs/images/creature_card_example.png)
*Example output: a generated creature card and move card for a converted D&D monster.*


## Overview

MonsterForge is a domain-specific data transformation pipeline that converts complex RPG stat blocks (D&D 3.5 / Pathfinder 1E) into simplified, playable card-based representations.

The system focuses on preserving functional identity, relative power, and gameplay usability, rather than performing a lossless conversion.

It combines:

- deterministic numerical transformations
- LLM-based semantic classification
- human-in-the-loop validation

to produce consistent and explainable outputs.

Currently evaluated against a dataset of 40 D&D 3.5 monsters, covering multiple creature types (animals, undead, magical beasts) to stress-test attribute mapping and classification edge cases.

> Full design documentation (conversion algorithms, classification schema, card system) is available in **[DESIGN.md](./DESIGN.md)**.

---

## Demo


- [Short walkthrough (GIF)](./docs/demo.gif) — scraping → classification → card generation, end-to-end 
- [Sample generated cards](./docs/samples/) — pre-rendered output for 5 monsters 

---

## Problem

RPG stat blocks are:

- highly complex
- semi-structured
- inconsistent across sources
- not directly usable in fast-paced game systems

Converting them into a simplified format requires:

- normalization of numerical values
- abstraction of mechanics
- interpretation of textual abilities

---

## Solution

MonsterForge implements a pipeline that:

1. Extracts raw RPG data from web sources
2. Parses and structures stat blocks
3. Transforms numerical values via deterministic rules
4. Classifies abilities using an LLM with a constrained schema
5. Applies human validation when confidence is low
6. Generates card-based representations ready for rendering

---

## Architecture

The system can be viewed as a domain-specific ETL pipeline:

```
Raw RPG Data (HTML / OGL)
        |
        v
Parser
        |
        v
Structured Data
        |
        +----------------------+
        |                      |
        v                      v
Numerical Transformation   LLM Classification
        |                      |
        +----------+-----------+
                   |
                   v
          Human Validation
                   |
                   v
        Intermediate Entity Model
                   |
                   v
            Card Generation
                   |
                   v
        HTML / Image Output
```

This pipeline follows an ETL-like structure where transformation is split between deterministic algorithms and constrained semantic classification.

---

## Key Design Principles

**Lossy Transformation**

The system intentionally reduces complexity:

- preserves gameplay-relevant identity
- removes unnecessary mechanical detail

**Deterministic vs Probabilistic Separation**

- Numerical data → deterministic algorithms
- Semantic data → LLM classification
- Final control → human validation

This ensures consistency, controllability, and explainability.

**Configuration as Code**

Conversion tables (size → HP, characteristic → attribute, skill → interpretation group) are modeled as typed dataclasses rather than external config files. Since balance rules are logic, not just data, keeping them in code (with shared, reusable calculation functions) avoids the false flexibility of a config layer that would still require code changes for most real adjustments.

**Intermediate Representation**

The pipeline does not convert directly from source to output:

```
RPG Data → Entity Model → Cards
```

This allows extensibility, multiple output formats, and decoupling from source systems.

---

## Features

- Web scraping with `requests` + `BeautifulSoup`
- SQL storage of raw and structured data
- Custom transformation algorithms (HP, attributes, resources, skills)
- Semantic classification using an LLM (schema-constrained, not generative)
- Confidence-based human validation workflow
- Card rendering pipeline (HTML → printable format)
- Desktop validation tool built with PyQt5

---

## Example

**Input (simplified)**

```
Wolf
Medium Animal
HD: 2d8
STR 13, DEX 15, CON 15
INT 2, WIS 12, CHA 6
Attack: Bite 1d6
```

**Output (simplified)**

```
CREATURE CARD
HP: 23
Attack: 1        Speed: 2        Defense: 2
Power: 0         Tangency: 1     Spin: 0
Athletics: 2     Empathy: 0      Perception: 2
Stealth: 2       Culture: 0      Craft: 0

MOVE CARD
Name: Bite
Type: Physical | Category: Attack | Mode: Active
Effect: Deal 3 damage to a single target
Cost: 1 Stamina
```

Full attribute derivation (HP, Body/Spirit, Interpretation) is documented in [DESIGN.md](./DESIGN.md).

---

## Pipeline Execution Example

A typical pipeline execution produces traceable logs for each transformation stage:
```text
[2026-07-10 14:32:01] INFO  Loading raw record: monster_id=wolf_001 source=d20srd
[2026-07-10 14:32:01] INFO  Parsing stat block...
[2026-07-10 14:32:01] INFO  Structured data extracted: 6 abilities, 8 skills, 1 attack
[2026-07-10 14:32:01] INFO  Applying numerical transformations (HP, Body, Spirit, Interpretation)...
[2026-07-10 14:32:02] INFO  HP=23  Attack=1  Speed=2  Defense=2
[2026-07-10 14:32:02] INFO  Classifying ability: "Bite" via LLM...
[2026-07-10 14:32:03] INFO  Classification result: confidence=0.94 -> auto-approved
[2026-07-10 14:32:03] INFO  Classifying ability: "Keen Scent" via LLM...
[2026-07-10 14:32:04] WARN  Low confidence classification: ability="Keen Scent" confidence=0.61 -> flagged for manual review
[2026-07-10 14:32:04] INFO  Queued for human validation: 1 item
[2026-07-10 14:32:10] INFO  Human validation completed: 1 approved, 0 corrected
[2026-07-10 14:32:10] INFO  Building intermediate entity model...
[2026-07-10 14:32:11] INFO  Generating card templates (1 creature, 2 moves)...
[2026-07-10 14:32:11] INFO  Export completed: creature_card.html, bite_card.html, keen_scent_card.html
```
Logging makes each transformation stage observable and simplifies debugging, validation, and future rule changes.

---

## Project Structure

```
monsterforge/
├── domain/            # core models (entity, card, ability) — the final,
│                       # source-independent representation
├── config/             # runtime settings (LLM API key, confidence thresholds, DB config — see .env.example)
├── db/                  # RECORD DB schema and access (raw scraped content, generic table)
├── rules/                 # typed conversion tables (dataclasses: size→HP, characteristic→attribute, ...)
├── scraping/                # HTML acquisition (requests + BeautifulSoup), writes to db/
├── parsing/                   # extraction + conversion, per RPG system and edition
│   └── dnd/v3x/
│       ├── raw_fields/          # stage 1: mirrors rulebook tables almost verbatim
│       │                          (e.g. RawArmorFields, RawCreatureFields — still
│       │                          mostly strings, not yet cast or interpreted)
│       └── ...                    # stage 2: casts raw_fields into structured_data,
│                                    routing free-text content to llm/ when needed
├── structured_data/               # typed, source-specific intermediate models
│   └── dnd/v3x/                    # (Creature, Item, Spell, Feat, ...) — the
│                                     "Dati Strutturati" stage from DESIGN.md
├── transformation/                  # numerical algorithms (HP, Body/Spirit, Interpretation)
├── llm/                               # semantic classification (attacks, qualities, feats, spells)
├── validation/                          # human review logic
├── rendering/                             # card generation (HTML/templates)
├── ui/                                     # PyQt5 validation tool
├── pipeline/                                 # orchestration
└── tests/                                     # unit tests
```
**Two-stage parsing.** Extraction is split into `raw_fields/` (source-format
strings, mirroring the rulebook table structure) and a conversion stage that
casts and normalizes into `structured_data/`. This decouples the fragile,
source-specific part of parsing (HTML layout, per-site formatting) from
interpretation and typing, and means:

- multiple scraping sources can converge on the same `raw_fields` shape
  before any interpretation happens;
- **manual input is a first-class path, not a workaround** — a `raw_fields`
  instance can be populated directly (CLI, or a future form) instead of
  scraped, letting a user hand-enter a custom weapon or character and still
  get a generated card, bypassing scraping entirely;
- simple entries with no free-text description can skip LLM classification
  and go straight to `structured_data` via direct type casting.

See **[PIPELINE_ARCHITECTURE.md](./docs/PIPELINE_ARCHITECTURE.md)** for the
full pipeline schema and the rationale behind this split.

---

## Example Usage

```
python -m monsterforge generate --entity wolf
```

Output:

```
Generated:
- creature_card.html
- bite_card.html
```

---

## LLM Integration

The LLM is used strictly as a semantic classifier, not a generator.

- Fixed output schema
- Low temperature
- Confidence scoring
- Automatic fallback to human validation when confidence < threshold

Example output *(simplified — see [DESIGN.md](./DESIGN.md) for the full schema, including duration, usage, and card fields)*:

```json
{
  "type": "Physical",
  "category": "Attack",
  "mode": "Active",
  "target": "Single",
  "resource": "Stamina",
  "confidence": 0.92
}
```

---

## Development

```bash
pip install -r requirements.txt
pytest
```

<!-- Add linting/formatting tools here if used, e.g.: -->
<!-- Code style: `ruff` / `black` -->

---

## Testing

Tests ensure that transformation rules remain stable as the system evolves.

The project includes unit tests for:

- numerical transformations
- attribute mapping
- edge cases
- pipeline consistency

Example:

```python
def test_wolf_conversion():
    monster = load_monster("wolf")
    card = convert(monster)

    assert card.hp == 23
    assert card.attack == 1
```

---

## Limitations

- Final game balance requires playtesting
- Some semantic edge cases require manual validation
- Not all RPG mechanics are fully represented
- Designed primarily for D&D 3.5 / Pathfinder 1E
- Full game ruleset is intentionally out of scope — this project is a transformation engine, not a game

---

## Future Improvements

- Web interface for validation
- Transformation versioning system
- Support for additional RPG systems
- Advanced balancing heuristics
- Batch processing pipeline

---

## Tech Stack

- Python
- requests / BeautifulSoup
- SQLite / SQLAlchemy
- PyQt5
- dataclasses
- Jinja2
- HTML/CSS templates
- LLM API
- pytest

---

## Why This Project

This project is designed to demonstrate real-world software engineering patterns applied to a non-trivial domain:

- data pipeline design (ETL)
- transformation of semi-structured data
- domain modeling
- integration of deterministic and AI-driven components
- human-in-the-loop system design
- end-to-end software architecture

---

## Documentation

- **[DESIGN.md](./DESIGN.md)** — technical documentation: architecture, transformation algorithms, intermediate data model, and LLM classification workflow
- *(optional)* [RULES_REFERENCE.pdf](./docs/RULES_REFERENCE.pdf) — the target game ruleset generated by the engine, included for reference only; not the focus of this project

---

## License & Data Sources

The codebase in this repository is original work.

Monster and rule data are derived from sources released under the **Open Game License (OGL)**. No proprietary, non-OGL content is scraped, stored, or redistributed. This project is a technical/portfolio project and does not aim to reproduce or distribute copyrighted game material beyond what OGL permits.
