# RPG Data Transformation Engine for Card Generation

> This document describes MonsterForge's original design vision and the
> numeric algorithms that convert D&D/Pathfinder stat blocks into card
> values — the algorithms are still implemented exactly as described here.
> For the current, detailed pipeline architecture see
> [PIPELINE_ARCHITECTURE.md](./monsterforge/docs/PIPELINE_ARCHITECTURE.md);
> for current project status see
> [PROJECT_STATUS.md](./monsterforge/docs/PROJECT_STATUS.md).

## Project Goal

Build a transformation engine capable of converting complex RPG stat
blocks into simplified representations usable as game cards, while
preserving:

- the creature's identity
- differences between archetypes
- numeric balance
- game speed

## Description

- Scraped and parsed OGL RPG data from web sources
- Designed custom lossy transformation algorithms
- LLM-based semantic classifier with human-in-the-loop validation
- Converted complex stat blocks into simplified card representations
- Built a rendering pipeline for printable card layouts
- Planned a JSON API (FastAPI) exposing the converted data, with
  human validation reachable through CLI tooling

## Explanation

A scraping project where I wanted to build a program that uses my own
conversion algorithms (lossy, non-invertible) to transform D&D 3.5 or
Pathfinder 1st edition monster data into game cards. Using `requests` to
download HTML pages and BeautifulSoup on d20.org to extract OGL
information and save it to a SQL DB, then applying the conversions with
my own algorithms and generating the cards as static web pages with a
print option to save them as images.

Numeric data is handled with the algorithms to guarantee balance, while
non-numeric values use an LLM as a semantic classifier plus a human
check for validating/adjusting the proposed values. The LLM does not
freely generate game data — it performs a classification constrained by
a schema. Card validation and manual editing are exposed through a JSON
API and CLI tooling, rather than the desktop tool originally planned
with PyQt5.

## PIPELINE

```
Raw RPG Text
     |
     v
Parser
     |
     v
Structured Data
     |
     +----------------+
     |                |
     v                v
Numerical Rules       LLM Semantic Classification
     |                |
     +-------+--------+
             |
             v
      Human Validation
             |
             v
        Card Generator
```

## Design decisions

- The conversion is deliberately lossy: the system preserves the
  creature's functional identity, not every detail of the original stat
  block.

- Numeric values are generated through deterministic formulas to
  maintain consistency and balance.

- Descriptive data is semantically classified via LLM with human
  validation.

- The maximum number of actions per turn is limited to keep the game
  fast.

---

## ALGORITHMS

#### GENERAL RULE -> all decimal values are rounded down

### Calculating the LIFE value

| LIFE | SIZE       |
|------|------------|
| 1    | Fine       |
| 2    | Diminutive |
| 5    | Tiny       |
| 10   | Small      |
| 15   | Medium     |
| 30   | Large      |
| 45   | Huge       |
| 60   | Gargantuan |
| 90   | Colossal   |

To this, add the average hit die value multiplied by the number of hit dice

| Dice Type | LIFE |
|-----------|------|
| D2        | 1    |
| D4        | 2    |
| D6        | 3    |
| D8        | 4    |
| D10       | 5    |
| D12       | 6    |

#### Conversion example -> Wolf: Medium size, 2d8 HD -> 15 + 2*4 = LIFE 23

-----------------

### Calculating BODY and SPIRIT values

- Use the characteristic modifiers as the indicator for Body and Spirit values
- The characteristic modifiers are used as normalized features, avoiding
  transferring the D&D system directly.
- Negative modifiers count as 0

| D&D CHARACTERISTIC | BODY CHARACTERISTIC |
|---------------------|----------------------|
| Strength             | Attack                |
| Dexterity            | Speed                 |
| Constitution         | Defense               |
| Dexterity*           | Defense (undead)      |

* For undead, Defense uses Dexterity instead of Constitution

| D&D CHARACTERISTIC | SPIRIT CHARACTERISTIC |
|---------------------|------------------------|
| Intelligence         | Power                   |
| Wisdom                | Ward                    |
| Charisma              | Flow                    |

For some monsters, use Charisma to determine Power and Intelligence to determine Flow.

Incorporeal creatures have no Attack or Defense.

#### Conversion example -> Wolf:

| D&D CHARACTERISTIC   | BODY CHARACTERISTIC    |
|-----------------------|--------------------------|
| - Strength = 13        | - Attack = 1              |
| - Dexterity = 15       | - Speed = 2               |
| - Constitution = 15    | - Defense = 2             |
| D&D CHARACTERISTIC   | SPIRIT CHARACTERISTIC  |
| - Intelligence = 2     | - Power = 0                |
| - Wisdom = 12          | - Ward = 1                 |
| - Charisma = 6         | - Flow = 0                 |

-----------------

### Calculating ARMOR and TALISMAN values

- Armor = total AC - Dexterity - 10 (deflection and size bonuses are not considered)
- Talisman = Spell Resistance - 10 + Deflection

#### Conversion example -> Wolf:

| D&D AC                        | ARMOR                                 |
|--------------------------------|-----------------------------------------|
| Total AC = 14                  | 14 - 2 (Dexterity value) - 10 = 2       |
| D&D AC                        | TALISMAN                              |
| --------                       | -----------                             |
| Spell Resistance = 0           | 0                                       |

-----------------

### Calculating INTERPRETATION values

#### There are 6 Interpretation values:
- Athletics
- Empathy
- Perception
- Stealth
- Knowledge
- Crafting

Group the various D&D skills into the 6 Interpretation groups and average
them; the value to assign is derived from that average.

- for each skill in a D&D skill group associated with an Interpretation
  value, take the skill's value using the calculation method described
  below; for each skill in that group compute the average to obtain the
  associated Interpretation value.

- calculation method used:
  description in words:
  Take the associated characteristic, if positive, or take 0 if negative.

  If the value is 0 — i.e. there are no skill ranks assigned or other
  bonuses — take the associated characteristic as the value; otherwise
  take the value and subtract the associated characteristic and 3 (this
  gives the skill ranks),

  then average all the non-zero values in the group being considered.

  Then check: if the reference characteristic for the Interpretation
  value is less than 0, the Interpretation value will be 0 (regardless of
  the average obtained); otherwise it will be the computed average.

- calculation method used, possible Python version:
```python
def calculate_interpretation(skill_values, characteristic_modifier):
    """
    skill_values: list of D&D skill values (e.g. [2,2,0,3,...])
    characteristic_modifier: modifier of the associated characteristic (e.g. +2, -1, etc.)
    """

    # If the characteristic is negative -> final result is 0
    if characteristic_modifier < 0:
        return 0

    # For the calculations, still use max(0, mod)
    char_mod = max(0, characteristic_modifier)

    computed_values = []

    for value in skill_values:
        if value == 0:
            result = char_mod
        else:
            result = value - char_mod - 3

        # only consider non-zero values
        if result != 0:
            computed_values.append(result)

    # avoid division by zero
    if not computed_values:
        return 0

    # final average
    average = sum(computed_values) / len(computed_values)

    return average
```

- Negative modifiers count as 0

| D&D SKILL             | INTERPRETATION |
|------------------------|-----------------|
| Acrobatics              | Athletics       |
| Escape Artist           | Athletics       |
| Ride                    | Athletics       |
| Balance                 | Athletics       |
| Swim                    | Athletics       |
| Jump                    | Athletics       |
| Climb                   | Athletics       |
| -------------           | ----------------- |
| Handle Animal           | Empathy         |
| Diplomacy               | Empathy         |
| Intimidate              | Empathy         |
| Perform                 | Empathy         |
| Sense Motive            | Empathy         |
| Gather Information      | Empathy         |
| Bluff                   | Empathy         |
| -------------           | ----------------- |
| Listen                  | Perception      |
| Search                  | Perception      |
| Spot                    | Perception      |
| -------------           | ----------------- |
| Disguise                | Stealth         |
| Move Silently           | Stealth         |
| Hide                    | Stealth         |
| Sleight of Hand         | Stealth         |
| -------------           | ----------------- |
| Concentration           | Knowledge       |
| Knowledge               | Knowledge       |
| Decipher Script         | Knowledge       |
| Heal                    | Knowledge       |
| Profession              | Knowledge       |
| Spellcraft              | Knowledge       |
| Survival                | Knowledge       |
| Appraise                | Knowledge       |
| -------------           | ----------------- |
| Craft                   | Crafting        |
| Disable Device          | Crafting        |
| Forgery                 | Crafting        |
| Open Lock               | Crafting        |
| Use Rope                | Crafting        |
| Use Magic Device        | Crafting        |
| -------------           | ----------------- |

| D&D REFERENCE CHARACTERISTIC | INTERPRETATION |
|--------------------------------|-----------------|
| Strength                        | Athletics       |
| Charisma                        | Empathy         |
| Wisdom                          | Perception      |
| Dexterity                       | Stealth         |
| Intelligence                    | Knowledge       |
| Intelligence                    | Crafting        |

#### Conversion example -> Wolf: (showing results for simplicity)

Athletics = 2
Empathy = 0
Perception = 2
Stealth = 2
Knowledge = 0
Crafting = 0

-----------------

### Calculating STAMINA and MANA values

#### STAMINA = pool of physical actions per turn
BAB becomes Stamina points -> number of attacks = Stamina

BAB/5 = Stamina (minimum 1)


#### MANA = pool of magical actions per turn

Use caster level to define Mana points

Caster level/5 = Mana (minimum 1 if it has a caster level, otherwise 0)

#### EXTRA on Stamina and Mana points
- bonus -> multiple attacks become bonus points (e.g. a hydra) or the
  ability to use a specific attack card multiple times (e.g. bite)
- for magical abilities with limited uses (in that case there is a
  maximum-uses limit)

##### design note
The maximum number of attacks per turn is capped at 4 to keep the game
fast. Any additional attacks are converted into bonuses or extra ability
uses.
-----------------

- bias towards non-zero skills -> intentional and acknowledged

- ignoring the Constitution value for Life (fewer HP, but balanced by
  size) -> Yes, not a concern

- problem with attacks, special attacks, special qualities, and items ->
  resolved via semantic classification

- how to handle ability drain -> average like HP and halved (minimum 1)
  -> cannot go negative

- how to handle healing -> becomes an average like HP -> 1d6 = 3 HP
  healed
- for absolute values (not modifiers), e.g. 5 -> halved and rounded down

- problem with movement methods (fly, swim, speed) not included -> use
  SPEED as speed and special methods as cards

- damage becomes an average like HP -> 1d6 = 3 damage

----------------

# CLASSIFICATION RULES FOR ATTACKS, TALENTS, SPECIAL QUALITIES AND SPELLS

> **Status note.** This section describes the original, general classification
> vision — an 8-field schema meant to apply uniformly to any ability type
> (attacks, talents, spells, special qualities). What's actually implemented
> so far (see `llm/semantic_classification/attacks.py`) is narrower and
> specific to attacks: only `description`, `move_type`, and `move_range` are
> LLM-classified. `category`, `mode`, `effect`, `target`, `duration`, and
> `usage` are deterministic defaults for the attack case (see
> `attack_converter()`); `resource` is derived from `move_type`, not
> classified; and the damage value is never LLM-computed — it's parsed with
> regex from the fixed dice notation, per this project's non-negotiable
> "regex over LLM whenever the format is fixed" rule. The full 8-field
> classifier below remains future work for talents, spells, and special
> qualities, which don't yet exist in the codebase.

Use AI as a semantic classifier for non-numeric data, a human as
validator/corrector.

Type: Physical / Magical

Attack cards = methods of attack
Defense cards = methods of defense
Special cards = other methods

Attack, defense, and special can each be: Active (requires doing
something) or Passive (always in effect or automatic).

Examples:
Attack-active = punch
Attack-passive = fire aura
Defense-active = parry
Defense-passive = toughness
Special-active = mega jump
Special-passive = regeneration

So:

Type
 ↓
Main Category
 ↓
Mode
 ↓
Effect
 ↓
Target
 ↓
Resource

example:
{
 "type": "Physical",
 "category": "Special",
 "mode": "Passive",
 "effect": "Healing",
 "target": "Self",
 "resource": "None"
}

These two must be added:

"duration": "Instant / Temporary / Permanent"
"usage": "Unlimited / Daily / Limited / Situational"
explanation: (limited, e.g. every 1d4 rounds as for breath weapons;
situational, e.g. sneak attack)

And then these 3 must be added for the card:
- Name
- Description
- Damage value (uses the same logic as HP -> average like HP -> 1d6 = 3 damage)

For human review, a confidence value must be added:
- "confidence": 0.92. If confidence < 0.7 -> send for manual review.

### Practical examples

#### Example 1
##### D&D Input
```text
Bite:
Natural attack that deals 1d6 piercing damage.
```

##### Output
```json
{
  "type": "Physical",
  "category": "Attack",
  "mode": "Active",
  "effect": "Damage",
  "target": "Single",
  "resource": "Stamina",
  "duration": "Instant",
  "usage": "Unlimited",

  "card": {
    "name": "Bite",
    "description": "Natural attack that deals piercing damage.",
    "damage": 3
  }
}
```

#### Example 2
##### D&D Input
```text
Fire aura:
Every adjacent creature automatically takes 1d4 fire damage.
```

##### Output
```json
{
  "type": "Magical",
  "category": "Attack",
  "mode": "Passive",
  "effect": "Area damage",
  "target": "Nearby",
  "resource": "None",
  "duration": "Permanent",
  "usage": "Unlimited",

  "card": {
    "name": "Fire aura",
    "description": "Nearby creatures automatically take fire damage.",
    "damage": 2
  }
}
```

#### Example 3
##### D&D Input
```text
Regeneration 5:
The creature recovers 5 HP every round.
```

##### Output
```json
{
  "type": "Physical",
  "category": "Special",
  "mode": "Passive",
  "effect": "Healing",
  "target": "Self",
  "resource": "None",
  "duration": "Permanent",
  "usage": "Unlimited",

  "card": {
    "name": "Regeneration",
    "description": "The creature recovers hit points every round.",
    "damage": 0
  }
}
```

#### Example 4 -> Talent
##### D&D Input
```text
Power Attack:
You can trade accuracy for extra damage.
```

##### Output
```json
{
  "type": "Physical",
  "category": "Attack",
  "mode": "Passive",
  "effect": "Bonus damage",
  "target": "Self",
  "resource": "None",
  "duration": "Permanent",
  "usage": "Situational",

  "card": {
    "name": "Power Attack",
    "description": "Increases attack damage at the cost of accuracy.",
    "damage": 0
  }
}
```

#### Example 5 -> Ability with limited use
##### D&D Input
```text
Breath weapon:
Once every 1d4 rounds the creature breathes a cone of fire.
Deals 6d6 damage.
```

##### Output
```json
{
  "type": "Magical",
  "category": "Attack",
  "mode": "Active",
  "effect": "Area damage",
  "target": "Area",
  "resource": "Mana",
  "duration": "Instant",
  "usage": "Limited",

  "card": {
    "name": "Breath weapon",
    "description": "Breathes a cone of fire that damages creatures in the area.",
    "damage": 18
  }
}
```

#### Example 6 -> Situational ability
##### D&D Input
```text
Sneak attack:
Deals extra damage when the target is caught off guard.
```

##### Output
```json
{
  "type": "Physical",
  "category": "Attack",
  "mode": "Passive",
  "effect": "Bonus damage",
  "target": "Single",
  "resource": "None",
  "duration": "Instant",
  "usage": "Situational",

  "card": {
    "name": "Sneak attack",
    "description": "Deals additional damage against vulnerable or unprepared targets.",
    "damage": 0
  }
}
```

----------------

# INTERMEDIATE DATA MODEL

The flow is not D&D -> card,

but:

D&D Monster
      |
      v
Monster Intermediate Representation
      |
      v
Card Object

This way it's extensible.

----------------

# GAME SYSTEM

## NARRATIVE DESCRIPTION
Summary description: there are cards of various types:

- CREATURE
- MOVE
- ITEM

So the program creates several cards even for the same monster —
for example, a dragon has a creature card (representing its stats)
and move cards representing (talents, attacks, special qualities,
spells, and special attacks), and it may also have item cards
representing objects it possesses.

So in this game, we say every entity is a deck of cards.

## Game system (draft)
Basic concept
Every entity in the game is represented by a set of cards.
A monster, a character, or a complex entity is not represented by a
single card, but by a personal deck made up of:
- a main card defining the base characteristics;
- ability cards representing the available actions;
- item cards representing equipment and possessions.

## Card types
CREATURE card -> defines who the creature is.
Represents the main entity.
Contains: the creature's general values and available resources.

MOVE card -> Represents a capability usable by the creature.
A move can derive from:
- a natural attack
- a talent
- a special ability
- a special quality
- a spell
- a spell-like ability
- a class feature

### Examples
MOVE

Bite

Type: Physical
Category: Attack
Usage: Unlimited

Effect:
Deals 3 damage to a single target.

---

MOVE

Breath Weapon

Type: Magical
Category: Attack

Usage:
Limited

Effect:
Deals 18 area damage.

---

ITEM card -> Represents a possessed or equipped item.
Can derive from:
- weapons
- armor
- magic items
- treasure
- equipment

### Examples

ITEM

Flaming Sword

Type:
Weapon

Effect:
+2 fire damage on physical attacks.

---

## STRUCTURE OF AN ENTITY
example: Dragon

DRAGON'S DECK

[CREATURE CARD]

Red Dragon


[MOVE CARDS]

Bite
Claw
Tail
Breath Weapon
Frightful Presence
Spells


[ITEM CARDS]

Dragon's Crown
Ancient Treasure
Magic Amulet

## SIMPLIFIED GAME PHILOSOPHY

The system separates:
- Identity = Creature card: "What are you?"
- Actions = Move cards: "What can you do?"
- Customization = Item cards: "What do you own?"

## PIPELINE FOR ENTITY CREATION

D&D / Pathfinder Database

        |
        v

Monster Parser

        |
        v

Entity Model

        |
        +----------------+----------------+
        |                |                |
        v                v                v

Creature Card       Move Cards       Item Cards
        |                |                |
        +----------------+----------------+
                         |
                         v
                 Entity's Deck

----------------

## FINAL NOTE ON "BALANCING"
- Balancing requires playtesting, while this system helps maintain a
  consistent distribution of values and preserve relative power ratios.

The system guarantees:
- numeric consistency
- relative proportions
- normalization

----------------

## RULESET
Since the main project is the transformation engine, not the game, for a
portfolio I'd keep the game as a "target representation" — i.e. the
final format generated by the engine. The complete ruleset is not
included, to avoid deviating from the project's focus.
