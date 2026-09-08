"""
Curated attacks for the JSON API's public demo deployment -- lets
GET /api/cards return something real on a fresh Render instance instead
of an empty list, since api/ has no equivalent of a visitor filling in
their own data the way the web form's Auto-fill button does.

Deliberately separate from sample_attacks_web_seed.py: that module
pairs a raw attack with empty/optional context for a web form to
populate, never a classification result. This one pairs a raw attack
with its ALREADY-VERIFIED real classification (description/move_type/
range/confidence/rationale), because api/demo_seed.py builds and
persists a card directly from it, deterministically, with no LLM call
at seed time -- avoiding real API quota use and a possibly different
confidence on every restart of an ephemeral public deployment.

Each entry's case/context/classification values are copied verbatim
from real Gemini API output already collected and committed in this
project (entrypoints/output/real_pipeline_conversion_samples_with_
context_160char_blank_fixed_damage_fixed.json, generated 2026-08-27),
not invented -- picked for variety: melee/ranged/ranged touch/melee
touch, physical/magical, with and without a secondary effect card,
with and without a creature_subtype.
"""

DEMO_SEED_ATTACKS = [
    {  # Tentacle: melee, physical, secondary effect (Slime)
        "case": {
            "name": "Tentacle", "modifier": "+12", "attack_type": "melee",
            "attack_effect": "1d6+8 plus slime",
        },
        "context": {
            "additional_description": "The tentacle leaves behind a smear of caustic slime wherever it strikes.",
            "creature_description": "A bloated, many-limbed horror that drags itself through swamp and cave, each tentacle slick with corrosive mucus.",
            "creature_subtype": None,
        },
        "classification": {
            "description": "A lashing tentacle strike that leaves behind a smear of caustic slime.",
            "move_type": "physical", "range_value": None, "range_unit": None,
            "confidence": 0.95,
            "rationale": "The attack is a standard melee natural attack (tentacle) dealing physical bludgeoning or crushing damage with an additional physical slime effect.",
        },
    },
    {  # Incorporeal touch: melee, magical (creature_subtype-forced), ability drain
        "case": {
            "name": "Incorporeal touch", "modifier": "+3", "attack_type": "melee",
            "attack_effect": "1d4 Wisdom drain",
        },
        "context": {
            "additional_description": "The touch saps the victim's clarity of mind, leaving confusion in its wake.",
            "creature_description": "A restless spirit bound to the site of its death, passing through walls and armor alike to feed on the minds of the living.",
            "creature_subtype": "incorporeal",
        },
        "classification": {
            "description": "A spectral touch that saps the victim's clarity of mind.",
            "move_type": "magical", "range_value": None, "range_unit": None,
            "confidence": 1.0,
            "rationale": "The creature subtype is incorporeal, which mandates a magical classification per the rules, and the attack deals ability drain.",
        },
    },
    {  # Web: ranged, physical, no attack_effect of its own (range from context prose)
        "case": {
            "name": "Web", "modifier": "+5", "attack_type": "ranged", "attack_effect": "",
        },
        "context": {
            "additional_description": (
                "In spider or hybrid form (see below), an aranea can throw a web up to six times per day. "
                "This is similar to an attack with a net but has a maximum range of 50 feet, with a range "
                "increment of 10 feet, and is effective against targets of up to Large size. The web anchors "
                "the target in place, allowing no movement.\n\nAn entangled creature can escape with a DC 13 "
                "Escape Artist check or burst the web with a DC 17 Strength check. The check DCs are "
                "Constitution-based, and the Strength check DC includes a +4 racial bonus. The web has 6 hit "
                "points, hardness 0, and takes double damage from fire."
            ),
            "creature_description": "An oversized arachnid that spins thick webbing to snare prey before closing in.",
            "creature_subtype": None,
        },
        "classification": {
            "description": "The aranea hurls a sticky web to ensnare and anchor the target in place.",
            "move_type": "physical", "range_value": 50, "range_unit": "imperial",
            "confidence": 0.95,
            "rationale": "The attack functions like a net attack with a defined physical range, hit points, hardness, and escape/strength check DCs.",
        },
    },
    {  # Light ray: ranged touch, magical
        "case": {
            "name": "Light ray", "modifier": "+2", "attack_type": "ranged touch", "attack_effect": "1d6",
        },
        "context": {
            "additional_description": "A lantern archon's light rays have a range of 30 feet. This attack overcomes damage reduction of any type.",
            "creature_description": "A radiant guardian construct animated by captured sunlight, standing watch over sacred ground.",
            "creature_subtype": None,
        },
        "classification": {
            "description": "A focused ray of concentrated sunlight flashes toward the target.",
            "move_type": "magical", "range_value": 30, "range_unit": "imperial",
            "confidence": 0.95,
            "rationale": "The attack is a ranged touch attack using a ray of light, which inherently functions as a magical or supernatural effect overcoming any damage reduction.",
        },
    },
    {  # Electricity ray: ranged touch, magical, creature_subtype present but not decisive
        "case": {
            "name": "Electricity ray", "modifier": "+9", "attack_type": "ranged touch", "attack_effect": "2d6",
        },
        "context": {
            "additional_description": "An arrowhawk can fire this ray once per round, with a range of 50 feet.",
            "creature_description": "A crackling elemental born of storm clouds, its body a shifting mass of charged vapor.",
            "creature_subtype": "air",
        },
        "classification": {
            "description": "A crackling bolt of electrical energy leaps toward the target.",
            "move_type": "magical", "range_value": 50, "range_unit": "imperial",
            "confidence": 0.95,
            "rationale": "The attack is a ranged touch attack that fires a ray of electricity, which is inherently magical or supernatural in nature under D&D 3.x rules.",
        },
    },
    {  # Rock: ranged, physical, range stated only in prose
        "case": {
            "name": "Rock", "modifier": "+9", "attack_type": "ranged", "attack_effect": "2d6+8",
        },
        "context": {
            "additional_description": "The range increment is 120 feet for a hill giant's thrown rocks.",
            "creature_description": "A massive humanoid dwelling in hill country, known for hurling stones at trespassers.",
            "creature_subtype": None,
        },
        "classification": {
            "description": "The hill giant hurls a massive rock through the air at the target.",
            "move_type": "physical", "range_value": 120, "range_unit": "imperial",
            "confidence": 0.95,
            "rationale": "The attack involves throwing a physical rock, and the range increment is explicitly stated as 120 feet in the additional description.",
        },
    },
    {  # Burning touch: melee touch, magical, secondary effect (Combustion)
        "case": {
            "name": "Burning touch", "modifier": "+4", "attack_type": "melee touch",
            "attack_effect": "1d8 fire plus combustion",
        },
        "context": {
            "additional_description": "The touch leaves smoldering embers that can flare into open flame moments later.",
            "creature_description": "A being wreathed in living flame, capable of igniting anything it touches.",
            "creature_subtype": "fire",
        },
        "classification": {
            "description": "A scorching touch leaves smoldering embers that flare into open flame.",
            "move_type": "magical", "range_value": None, "range_unit": None,
            "confidence": 0.95,
            "rationale": "The attack is a melee touch attack dealing elemental fire damage and combustion effects from a fire-subtype creature.",
        },
    },
    {  # Psychic lash: ranged touch, magical (creature_subtype-driven), secondary effect (Stagger)
        "case": {
            "name": "Psychic lash", "modifier": "+5", "attack_type": "ranged touch",
            "attack_effect": "1d6 plus stagger",
        },
        "context": {
            "additional_description": "The creature emits a wave of psionic energy that strikes a single target within 30 feet. The lash strikes the mind directly, leaving the target reeling and disoriented.",
            "creature_description": "A creature attuned to psionic power, capable of lashing out with raw mental force.",
            "creature_subtype": "psionic",
        },
        "classification": {
            "description": "A wave of psionic energy strikes the target's mind, leaving them reeling.",
            "move_type": "magical", "range_value": 30, "range_unit": "imperial",
            "confidence": 0.95,
            "rationale": "The attack uses psionic energy, targets touch AC, and is explicitly tied to a psionic creature subtype.",
        },
    },
]
