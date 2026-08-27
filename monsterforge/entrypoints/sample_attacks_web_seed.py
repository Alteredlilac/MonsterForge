"""
Curated attack samples for the live web form's "Auto-fill" convenience
feature (MVP 1.4) — lets someone trying /convert for the first time
populate every field with one click instead of typing an attack by hand.

Deliberately its own module, not a reuse of sample_attacks.py/
sample_attacks_with_context.py: those exist for a different domain
question (deterministic-parser regression coverage, classify_attack()
context exercising) and their shape reflects that — a nested
{"raw_attack": ..., "context": ...} dict, split for Python call-site
convenience, and no structured range field at all (that field didn't
exist yet when those files were written).

Every entry here is a FLAT dict whose keys are exactly the /convert
form's field names (see ui/templates/convert_form.html.jinja2 and the
POST /convert route in ui/app.py), so the auto-fill JS can set each
form field directly from one sample object with no reshaping:
name, modifier, attack_type, attack_effect, range_value, range_unit,
additional_description, creature_description, creature_subtype.
range_value/range_unit/additional_description/creature_description/
creature_subtype are "" when not applicable, matching the live form's
own empty-string convention (every one of those fields posts as
Form("")) rather than None.

The first 64 entries are the same real attacks from sample_attacks.py
(the blank placeholder case excluded), adapted: the 11 that are
ranged/ranged touch gained an explicit range_value/range_unit (mostly
grounded in the same SRD-style range already stated in prose over in
sample_attacks_with_context.py; two — Light crossbow, Longbow — had no
range stated there, so a standard D&D 3.5 weapon range increment was
used instead: 80 ft and 100 ft respectively) to actually exercise the
structured range field the live form has today, which postdates that
older dataset. The one pre-existing gap in the source data — "Swarm"
(index 49 in SAMPLE_ATTACKS) has an empty attack_type, invalid for this
form's constrained dropdown — was given "melee", matching how a swarm's
damage is actually dealt (occupying a creature's space), for this
dataset specifically.

The remaining 36 are new, invented, SRD-flavored magical attacks (not
copied from any specific published monster) added to broaden the
variety on offer: more of the less-represented DamageType keywords
(cold, sonic, disintegration, force, negative energy) than the base 64
cover, more CreatureSubtype coverage, several ability-drain effects,
and two deliberately bare-word special attacks (no dice, no number) to
demonstrate the "unrecognized/typeless word becomes a special attack
name" rule documented in WEB_UI_AND_REVIEW.md.
"""

SAMPLE_ATTACKS_WEB_SEED = [
    # --- 64 real attacks, adapted from sample_attacks.py ---
    {
        "name": "Tentacle", "modifier": "+12", "attack_type": "melee",
        "attack_effect": "1d6+8 plus slime", "range_value": "", "range_unit": "",
        "additional_description": "The tentacle leaves behind a smear of caustic slime wherever it strikes.",
        "creature_description": "A bloated, many-limbed horror that drags itself through swamp and cave, each tentacle slick with corrosive mucus.",
        "creature_subtype": "",
    },
    {
        "name": "Claw", "modifier": "+9", "attack_type": "melee",
        "attack_effect": "2d6+4", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A powerful predator built for close combat, relying on raw strength to bring down prey.",
        "creature_subtype": "",
    },
    {
        "name": "Incorporeal touch", "modifier": "+3", "attack_type": "melee",
        "attack_effect": "1d4 Wisdom drain", "range_value": "", "range_unit": "",
        "additional_description": "The touch saps the victim's clarity of mind, leaving confusion in its wake.",
        "creature_description": "A restless spirit bound to the site of its death, passing through walls and armor alike to feed on the minds of the living.",
        "creature_subtype": "incorporeal",
    },
    {
        "name": "Bite", "modifier": "+5", "attack_type": "melee",
        "attack_effect": "1d6 plus poison", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A fanged ambush predator whose bite delivers a potent venom.",
        "creature_subtype": "",
    },
    {
        "name": "Web", "modifier": "+5", "attack_type": "ranged",
        "attack_effect": "", "range_value": 50, "range_unit": "imperial",
        "additional_description": "The web anchors the target in place, allowing no movement.",
        "creature_description": "An oversized arachnid that spins thick webbing to snare prey before closing in.",
        "creature_subtype": "",
    },
    {
        "name": "Light ray", "modifier": "+2", "attack_type": "ranged touch",
        "attack_effect": "1d6", "range_value": 30, "range_unit": "imperial",
        "additional_description": "This attack overcomes damage reduction of any type.",
        "creature_description": "A radiant guardian construct animated by captured sunlight, standing watch over sacred ground.",
        "creature_subtype": "",
    },
    {
        "name": "Electricity ray", "modifier": "+9", "attack_type": "ranged touch",
        "attack_effect": "2d6", "range_value": 50, "range_unit": "imperial",
        "additional_description": "",
        "creature_description": "A crackling elemental born of storm clouds, its body a shifting mass of charged vapor.",
        "creature_subtype": "air",
    },
    {
        "name": "Bite", "modifier": "+9", "attack_type": "melee",
        "attack_effect": "1d6+1", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A lean, fast-moving predator that hunts in packs.",
        "creature_subtype": "",
    },
    {
        "name": "Morningstar", "modifier": "+16", "attack_type": "melee",
        "attack_effect": "3d6+8", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A towering warrior clad in crude armor, favoring a spiked morningstar to crush anything in its path.",
        "creature_subtype": "",
    },
    {
        "name": "Rock", "modifier": "+9", "attack_type": "ranged",
        "attack_effect": "2d6+8", "range_value": 120, "range_unit": "imperial",
        "additional_description": "",
        "creature_description": "A massive humanoid dwelling in hill country, known for hurling stones at trespassers.",
        "creature_subtype": "",
    },
    {
        "name": "Warhammer", "modifier": "+3", "attack_type": "melee",
        "attack_effect": "1d8+1/×3 plus 1 fire", "range_value": "", "range_unit": "",
        "additional_description": "The warhammer's head glows faintly with residual heat, searing flesh on impact.",
        "creature_description": "A militant humanoid wielding a warhammer whose head has been enchanted to smolder.",
        "creature_subtype": "",
    },
    {
        "name": "Shortspear", "modifier": "+3", "attack_type": "ranged",
        "attack_effect": "1d6+1 plus 1 fire", "range_value": 20, "range_unit": "imperial",
        "additional_description": "The tip of the spear is wreathed in flame that flares briefly on impact.",
        "creature_description": "A nomadic raider who hurls spears wreathed in magical flame at approaching enemies.",
        "creature_subtype": "",
    },
    {
        "name": "Slam", "modifier": "+6", "attack_type": "melee",
        "attack_effect": "1d8+1", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A crude, hulking construct animated by ancient magic, attacking with heavy blows.",
        "creature_subtype": "",
    },
    {
        "name": "Claw", "modifier": "+10", "attack_type": "melee",
        "attack_effect": "1d3+2 plus corporeal instability", "range_value": "", "range_unit": "",
        "additional_description": "Its claws seem to blur and phase, disrupting the cohesion of whatever they strike.",
        "creature_description": "A shifting, unstable aberration whose touch destabilizes living tissue at a molecular level.",
        "creature_subtype": "",
    },
    {
        "name": "Tentacle", "modifier": "+6", "attack_type": "melee",
        "attack_effect": "1d3+3", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A smaller kin of the swamp-dwelling tentacled horrors, still dangerous in close combat.",
        "creature_subtype": "",
    },
    {
        "name": "Bite", "modifier": "+9", "attack_type": "melee",
        "attack_effect": "1d4-2 plus petrification", "range_value": "", "range_unit": "",
        "additional_description": "A creeping calcification spreads outward from any wound it inflicts.",
        "creature_description": "A reptilian horror whose gaze and bite alike can turn living flesh to solid stone.",
        "creature_subtype": "reptilian",
    },
    {
        "name": "Bite", "modifier": "+19", "attack_type": "melee",
        "attack_effect": "2d6+9 plus poison", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A large winged reptile whose bite injects a debilitating venom.",
        "creature_subtype": "reptilian",
    },
    {
        "name": "Web", "modifier": "+11", "attack_type": "ranged",
        "attack_effect": "", "range_value": 50, "range_unit": "imperial",
        "additional_description": "The web anchors the target in place, allowing no movement.",
        "creature_description": "An enormous spider, larger and hungrier than its smaller kin, capable of spinning webbing thick enough to trap prey outright.",
        "creature_subtype": "",
    },
    {
        "name": "Claw", "modifier": "+9", "attack_type": "melee",
        "attack_effect": "1d6+4", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A territorial predator that rakes at intruders with sharp, curved claws.",
        "creature_subtype": "",
    },
    {
        "name": "Claw", "modifier": "+18", "attack_type": "melee",
        "attack_effect": "2d8+6 plus fear", "range_value": "", "range_unit": "",
        "additional_description": "The sheer violence of the strike is often enough to break an onlooker's resolve.",
        "creature_description": "A fearsome apex predator whose presence alone unsettles lesser creatures.",
        "creature_subtype": "",
    },
    {
        "name": "Slam", "modifier": "+6", "attack_type": "melee",
        "attack_effect": "1d6+1 plus 1d6 fire", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A creature wreathed in barely-contained flame, its every blow searing as much as it bruises.",
        "creature_subtype": "fire",
    },
    {
        "name": "Slam", "modifier": "+8", "attack_type": "melee",
        "attack_effect": "1d8+7", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A hulking brute that relies on sheer bulk and crushing blows to overwhelm its foes.",
        "creature_subtype": "",
    },
    {
        "name": "Morningstar", "modifier": "+12", "attack_type": "melee",
        "attack_effect": "2d6+6", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A disciplined soldier wielding a morningstar as part of a well-drilled war band.",
        "creature_subtype": "",
    },
    {
        "name": "Javelin", "modifier": "+5", "attack_type": "ranged",
        "attack_effect": "1d8+6", "range_value": 30, "range_unit": "imperial",
        "additional_description": "",
        "creature_description": "A swift-footed skirmisher who favors javelins for softening enemies before closing to melee.",
        "creature_subtype": "",
    },
    {
        "name": "Bite", "modifier": "+2", "attack_type": "melee",
        "attack_effect": "1d6+1 plus paralysis", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A carrion-feeder whose bite carries a paralytic toxin, useful for immobilizing prey before it can flee.",
        "creature_subtype": "",
    },
    {
        "name": "Greatclub", "modifier": "+17", "attack_type": "melee",
        "attack_effect": "2d8+12", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "An enormous, brutish giant that fells trees to fashion crude but devastating clubs.",
        "creature_subtype": "",
    },
    {
        "name": "Slam", "modifier": "+17", "attack_type": "melee",
        "attack_effect": "1d4+8", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A swift, hulking creature that strikes with surprising speed despite its size.",
        "creature_subtype": "",
    },
    {
        "name": "Rock", "modifier": "+11", "attack_type": "ranged",
        "attack_effect": "2d8+12", "range_value": 120, "range_unit": "imperial",
        "additional_description": "This creature hurls a boulder large enough to crush a wagon.",
        "creature_description": "A colossal hill-dwelling giant known for flinging boulders at any who trespass on its territory.",
        "creature_subtype": "",
    },
    {
        "name": "Bite", "modifier": "+6", "attack_type": "melee",
        "attack_effect": "1d10+3", "range_value": "", "range_unit": "",
        "additional_description": "Once its jaws close around a target, it seldom lets go.",
        "creature_description": "A powerful aquatic reptile that lurks at the water's edge, seizing prey in its crushing jaws.",
        "creature_subtype": "reptilian",
    },
    {
        "name": "Tentacle", "modifier": "+28", "attack_type": "melee",
        "attack_effect": "2d8+12/19-20", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A colossal denizen of the deep, whose whip-like tentacles can shear through hull and bone alike.",
        "creature_subtype": "aquatic",
    },
    {
        "name": "Touch", "modifier": "+12", "attack_type": "melee",
        "attack_effect": "1d4 Wisdom drain", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "An undead spirit that drains the sanity of the living with a single touch.",
        "creature_subtype": "incorporeal",
    },
    {
        "name": "Dagger", "modifier": "+12", "attack_type": "melee",
        "attack_effect": "1d6+4/19-20", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A quick, cunning humanoid skilled with a blade, favoring precision over brute strength.",
        "creature_subtype": "",
    },
    {
        "name": "Claw", "modifier": "+12", "attack_type": "melee",
        "attack_effect": "1d4+4", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A nimble hunter that darts in to rake its prey before retreating out of reach.",
        "creature_subtype": "",
    },
    {
        "name": "Burning touch", "modifier": "+4", "attack_type": "melee touch",
        "attack_effect": "1d8 fire plus combustion", "range_value": "", "range_unit": "",
        "additional_description": "The touch leaves smoldering embers that can flare into open flame moments later.",
        "creature_description": "A being wreathed in living flame, capable of igniting anything it touches.",
        "creature_subtype": "fire",
    },
    {
        "name": "Slam", "modifier": "+4", "attack_type": "melee",
        "attack_effect": "1d3+3 plus combustion", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A minor flame-touched creature, its body radiating enough heat to scorch on contact.",
        "creature_subtype": "fire",
    },
    {
        "name": "Slam", "modifier": "+9", "attack_type": "melee",
        "attack_effect": "1d8+4", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A stout, muscular creature that favors overwhelming force in melee.",
        "creature_subtype": "",
    },
    {
        "name": "Slam", "modifier": "+12", "attack_type": "melee",
        "attack_effect": "1d6+7", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A fast, aggressive predator that closes distance quickly to land crushing blows.",
        "creature_subtype": "",
    },
    {
        "name": "Tongue", "modifier": "+12", "attack_type": "melee touch",
        "attack_effect": "paralysis", "range_value": "", "range_unit": "",
        "additional_description": "The tongue lashes out too quickly to easily dodge, numbing whatever it touches.",
        "creature_description": "An amphibious ambush predator that lashes out with a long, sticky tongue coated in paralytic toxin.",
        "creature_subtype": "",
    },
    {
        "name": "Bite", "modifier": "+12", "attack_type": "melee",
        "attack_effect": "2d6+6 plus disease", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A filth-encrusted predator whose bite festers with disease, often found lurking in sewers and refuse heaps.",
        "creature_subtype": "",
    },
    {
        "name": "Slam", "modifier": "+8", "attack_type": "melee",
        "attack_effect": "2d6+4 plus 2d6 acid", "range_value": "", "range_unit": "",
        "additional_description": "A film of caustic acid coats the creature's body, burning anything it strikes.",
        "creature_description": "A corrosive, half-liquid horror whose touch dissolves flesh and metal alike.",
        "creature_subtype": "",
    },
    {
        "name": "Bite", "modifier": "+7", "attack_type": "melee",
        "attack_effect": "1d6+4 plus poison", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A stealthy hunter whose bite delivers a debilitating venom, favored for ambush tactics.",
        "creature_subtype": "",
    },
    {
        "name": "Tail slap", "modifier": "+4", "attack_type": "melee",
        "attack_effect": "1d6+1 plus positive energy", "range_value": "", "range_unit": "",
        "additional_description": "The strike carries a surge of positive energy, more harmful to the undead than to the living.",
        "creature_description": "A radiant, good-aligned creature whose tail crackles with the same holy energy that sustains it.",
        "creature_subtype": "good",
    },
    {
        "name": "Tail touch", "modifier": "+4", "attack_type": "melee touch",
        "attack_effect": "positive energy", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A benevolent outsider whose touch channels raw positive energy.",
        "creature_subtype": "good",
    },
    {
        "name": "Antennae touch", "modifier": "+3", "attack_type": "melee",
        "attack_effect": "rust", "range_value": "", "range_unit": "",
        "additional_description": "Any metal object touched by the antennae begins to rust and crumble almost immediately.",
        "creature_description": "A skittish, insectoid creature whose antennae corrode metal on contact, reducing weapons and armor to flakes of rust.",
        "creature_subtype": "",
    },
    {
        "name": "Incorporeal touch", "modifier": "+3", "attack_type": "melee",
        "attack_effect": "1d6 Str", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A vengeful specter that saps the physical vitality of the living with an icy touch.",
        "creature_subtype": "incorporeal",
    },
    {
        "name": "Incorporeal touch", "modifier": "+6", "attack_type": "melee",
        "attack_effect": "1d8 plus energy drain", "range_value": "", "range_unit": "",
        "additional_description": "Victims touched by the creature feel a portion of their vitality permanently siphoned away.",
        "creature_description": "A malevolent undead horror that drains the very life force from those it touches.",
        "creature_subtype": "incorporeal",
    },
    {
        "name": "Short sword", "modifier": "+4", "attack_type": "melee",
        "attack_effect": "1d4-2/19-20", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A lightly armed humanoid scout, relying on a short sword for quick, precise strikes.",
        "creature_subtype": "",
    },
    {
        "name": "Light crossbow", "modifier": "+4", "attack_type": "ranged",
        "attack_effect": "1d6/19-20", "range_value": 80, "range_unit": "imperial",
        "additional_description": "",
        "creature_description": "A disciplined marksman who favors the light crossbow for its reliability at range.",
        "creature_subtype": "",
    },
    {
        "name": "Swarm", "modifier": "", "attack_type": "melee",
        "attack_effect": "2d6", "range_value": "", "range_unit": "",
        "additional_description": "A single swarm moves into opponents' spaces, provoking an attack of opportunity, and remains a creature with a 10-foot space.",
        "creature_description": "A churning mass of biting insects that overwhelms prey through sheer numbers rather than individual strength.",
        "creature_subtype": "swarm",
    },
    {
        "name": "Bite", "modifier": "+57", "attack_type": "melee",
        "attack_effect": "4d8+17/18-20/×3", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "An ancient, immensely powerful dragon whose bite alone can shear through castle gates.",
        "creature_subtype": "reptilian",
    },
    {
        "name": "Slam", "modifier": "+12", "attack_type": "melee",
        "attack_effect": "2d6+9", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A powerfully built creature that relies on brute force in melee combat.",
        "creature_subtype": "",
    },
    {
        "name": "Bite", "modifier": "+7", "attack_type": "melee",
        "attack_effect": "1d6+4", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A mid-sized predator with a strong, snapping bite.",
        "creature_subtype": "",
    },
    {
        "name": "Short sword", "modifier": "+7", "attack_type": "melee",
        "attack_effect": "1d6+2/19-20", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A trained soldier equipped with a short sword, fighting with practiced discipline.",
        "creature_subtype": "",
    },
    {
        "name": "Claw", "modifier": "+7", "attack_type": "melee",
        "attack_effect": "1d4+2", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A small but aggressive predator that lashes out with sharp claws.",
        "creature_subtype": "",
    },
    {
        "name": "Longbow", "modifier": "+8", "attack_type": "ranged",
        "attack_effect": "1d8/×3", "range_value": 100, "range_unit": "imperial",
        "additional_description": "",
        "creature_description": "A skilled archer favoring the longbow for its range and stopping power.",
        "creature_subtype": "",
    },
    {
        "name": "Slam", "modifier": "+2", "attack_type": "melee",
        "attack_effect": "1d6+1", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A young or weakened creature, still capable of landing a solid blow.",
        "creature_subtype": "",
    },
    {
        "name": "Club", "modifier": "+2", "attack_type": "melee",
        "attack_effect": "1d6+1", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A small, disorganized humanoid raider wielding a crude wooden club.",
        "creature_subtype": "goblinoid",
    },
    {
        "name": "Bite", "modifier": "+3", "attack_type": "melee",
        "attack_effect": "1d6+1", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A young predator, still growing into its full hunting strength.",
        "creature_subtype": "",
    },
    {
        "name": "Bite", "modifier": "+7", "attack_type": "melee",
        "attack_effect": "1d6+3 plus trip", "range_value": "", "range_unit": "",
        "additional_description": "The bite is as much about dragging prey off balance as wounding it.",
        "creature_description": "A powerful predator that seizes prey in its jaws and hauls it off its feet.",
        "creature_subtype": "",
    },
    {
        "name": "Slam", "modifier": "+9", "attack_type": "melee",
        "attack_effect": "1d8+5 plus push", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A massive brute whose blows are as much about shoving foes aside as wounding them.",
        "creature_subtype": "",
    },
    {
        "name": "Tail sweep", "modifier": "+6", "attack_type": "melee",
        "attack_effect": "1d6+2 plus unbalance", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A creature with a long, muscular tail that sweeps low to knock opponents off their footing.",
        "creature_subtype": "reptilian",
    },
    {
        "name": "Pincers", "modifier": "+8", "attack_type": "melee",
        "attack_effect": "1d4+4 plus grapple", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A heavily armored creature with powerful pincers used to seize and crush prey.",
        "creature_subtype": "",
    },
    {
        "name": "Psychic lash", "modifier": "+5", "attack_type": "ranged touch",
        "attack_effect": "1d6 plus stagger", "range_value": 30, "range_unit": "imperial",
        "additional_description": "The lash strikes the mind directly, leaving the target reeling and disoriented.",
        "creature_description": "A creature attuned to psionic power, capable of lashing out with raw mental force.",
        "creature_subtype": "psionic",
    },
    {
        "name": "Arcane slam", "modifier": "+4", "attack_type": "melee touch",
        "attack_effect": "1d4+2 plus disarm", "range_value": "", "range_unit": "",
        "additional_description": "The impact carries a burst of arcane force strong enough to wrench a weapon from an opponent's grip.",
        "creature_description": "A creature suffused with residual arcane energy, its blows crackling with disruptive magic.",
        "creature_subtype": "",
    },

    # --- 36 new, invented magical attacks (not from a real stat block) ---
    # Added to broaden coverage: less-represented DamageType keywords
    # (cold, sonic, disintegration, force, negative energy), more
    # CreatureSubtype variety, ability-drain effects, and two bare-word
    # special attacks with no dice at all (curse, silence).
    {
        "name": "Frost bolt", "modifier": "+6", "attack_type": "ranged touch",
        "attack_effect": "2d6 cold", "range_value": 60, "range_unit": "imperial",
        "additional_description": "A jagged shard of magical ice hurled with unerring aim.",
        "creature_description": "A creature born of glacial wastes, weaving frost into every strike it makes from a distance.",
        "creature_subtype": "cold",
    },
    {
        "name": "Acid spit", "modifier": "+7", "attack_type": "ranged",
        "attack_effect": "2d4 acid", "range_value": 30, "range_unit": "imperial",
        "additional_description": "",
        "creature_description": "A caustic-blooded beast that spits a jet of corrosive bile at approaching threats.",
        "creature_subtype": "",
    },
    {
        "name": "Lightning lash", "modifier": "+8", "attack_type": "melee touch",
        "attack_effect": "2d8 electricity", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A storm-touched horror whose touch crackles with barely-contained current.",
        "creature_subtype": "air",
    },
    {
        "name": "Sonic shriek", "modifier": "+5", "attack_type": "ranged",
        "attack_effect": "3d6 sonic", "range_value": 40, "range_unit": "imperial",
        "additional_description": "A piercing wail shatters eardrums and rattles bone at range.",
        "creature_description": "A wailing undead spirit whose cry alone can wound the unprepared.",
        "creature_subtype": "",
    },
    {
        "name": "Disintegrating touch", "modifier": "+9", "attack_type": "melee touch",
        "attack_effect": "1d6 disintegration", "range_value": "", "range_unit": "",
        "additional_description": "Matter itself seems to unravel at the creature's touch.",
        "creature_description": "An aberration wrapped in unstable planar energy, its touch erasing whatever it grips.",
        "creature_subtype": "extraplanar",
    },
    {
        "name": "Force spike", "modifier": "+7", "attack_type": "ranged touch",
        "attack_effect": "1d10 force", "range_value": 50, "range_unit": "imperial",
        "additional_description": "",
        "creature_description": "A construct animated by pure magical force, launching spikes of solidified energy.",
        "creature_subtype": "augmented",
    },
    {
        "name": "Withering ray", "modifier": "+6", "attack_type": "ranged touch",
        "attack_effect": "2d6 negative energy", "range_value": 60, "range_unit": "imperial",
        "additional_description": "A beam of cold, draining energy withers flesh on contact.",
        "creature_description": "A gaunt, spectral figure that channels the negative energy plane through its outstretched hand.",
        "creature_subtype": "incorporeal",
    },
    {
        "name": "Radiant touch", "modifier": "+5", "attack_type": "melee touch",
        "attack_effect": "2d6 positive energy", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A being of pure celestial light, its touch searing the unworthy.",
        "creature_subtype": "good",
    },
    {
        "name": "Soul rend", "modifier": "+10", "attack_type": "melee",
        "attack_effect": "1d8 plus energy drain", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A malevolent spirit that tears at the life force of the living with claws that pass through armor.",
        "creature_subtype": "evil",
    },
    {
        "name": "Petrifying gaze", "modifier": "+4", "attack_type": "melee touch",
        "attack_effect": "petrification", "range_value": "", "range_unit": "",
        "additional_description": "A creature that meets the gaze finds its flesh slowly turning to unyielding stone.",
        "creature_description": "A serpentine horror whose stare alone can turn the bravest warrior into a statue.",
        "creature_subtype": "reptilian",
    },
    {
        "name": "Curse touch", "modifier": "+6", "attack_type": "melee touch",
        "attack_effect": "curse", "range_value": "", "range_unit": "",
        "additional_description": "The touch leaves behind a lingering curse of misfortune.",
        "creature_description": "A hexing fey creature that marks its victims with ill fortune at the barest touch.",
        "creature_subtype": "chaotic",
    },
    {
        "name": "Banishing smite", "modifier": "+11", "attack_type": "melee",
        "attack_effect": "2d8+6 plus banish", "range_value": "", "range_unit": "",
        "additional_description": "A blow charged with planar-severing magic.",
        "creature_description": "A holy warrior whose weapon is enchanted to cast extraplanar foes back to their home plane.",
        "creature_subtype": "lawful",
    },
    {
        "name": "Earthen slam", "modifier": "+9", "attack_type": "melee",
        "attack_effect": "2d6+7 plus 1d6 acid", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A creature of living stone and soil, its blows carrying a faint corrosive tang of mineral acid.",
        "creature_subtype": "earth",
    },
    {
        "name": "Tidal slam", "modifier": "+8", "attack_type": "melee",
        "attack_effect": "2d6+5", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A powerful aquatic predator that strikes with the crushing force of a breaking wave.",
        "creature_subtype": "aquatic",
    },
    {
        "name": "Wing buffet", "modifier": "+7", "attack_type": "melee",
        "attack_effect": "1d6+4 plus 1d6 cold", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A frost-feathered avian whose beating wings chill the air around it.",
        "creature_subtype": "cold",
    },
    {
        "name": "Psychic crush", "modifier": "+9", "attack_type": "ranged touch",
        "attack_effect": "3d6 plus stagger", "range_value": 60, "range_unit": "imperial",
        "additional_description": "A wave of raw mental force batters the target's mind from a distance.",
        "creature_description": "A being of pure psionic power, capable of crushing a mind without ever touching its body.",
        "creature_subtype": "psionic",
    },
    {
        "name": "Holy smite", "modifier": "+8", "attack_type": "ranged",
        "attack_effect": "2d8 positive energy", "range_value": 40, "range_unit": "imperial",
        "additional_description": "A bolt of searing holy light, more harmful to the undead and evil-aligned.",
        "creature_description": "A radiant messenger that hurls bolts of pure holy energy at the wicked.",
        "creature_subtype": "angel",
    },
    {
        "name": "Unholy bolt", "modifier": "+8", "attack_type": "ranged touch",
        "attack_effect": "2d8 negative energy", "range_value": 40, "range_unit": "imperial",
        "additional_description": "A bolt of corrupting darkness, more harmful to the good-aligned.",
        "creature_description": "A fiendish outsider that channels the corrupting power of the lower planes into a bolt of pure malice.",
        "creature_subtype": "evil",
    },
    {
        "name": "Shapeshifting claw", "modifier": "+9", "attack_type": "melee",
        "attack_effect": "1d8+6 plus 1d4 acid", "range_value": "", "range_unit": "",
        "additional_description": "The claw briefly reshapes itself into something more monstrous with every strike.",
        "creature_description": "A fluid, ever-changing predator that can reform its limbs into whatever weapon suits the moment.",
        "creature_subtype": "shapechanger",
    },
    {
        "name": "Swarm bite", "modifier": "+4", "attack_type": "melee",
        "attack_effect": "1d4", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A roiling mass of tiny biting creatures acting as a single hungry organism.",
        "creature_subtype": "swarm",
    },
    {
        "name": "Sacred flame", "modifier": "+7", "attack_type": "ranged touch",
        "attack_effect": "2d6 fire plus positive energy", "range_value": 30, "range_unit": "imperial",
        "additional_description": "",
        "creature_description": "A guardian spirit that hurls motes of holy fire at trespassers.",
        "creature_subtype": "archon",
    },
    {
        "name": "Native fury", "modifier": "+10", "attack_type": "melee",
        "attack_effect": "2d6+8", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A powerful outsider bound permanently to this plane, retaining the raw strength of its origin.",
        "creature_subtype": "native",
    },
    {
        "name": "Winter's touch", "modifier": "+6", "attack_type": "melee touch",
        "attack_effect": "1d8 cold plus 1d4 Dex drain", "range_value": "", "range_unit": "",
        "additional_description": "The chill seeps into muscle and bone, slowing every movement.",
        "creature_description": "A creature wreathed in unnatural frost, its touch numbing flesh and stealing coordination alike.",
        "creature_subtype": "cold",
    },
    {
        "name": "Goblin spear", "modifier": "+3", "attack_type": "ranged",
        "attack_effect": "1d6", "range_value": 20, "range_unit": "imperial",
        "additional_description": "",
        "creature_description": "A crude but effective raider armed with a thrown spear.",
        "creature_subtype": "goblinoid",
    },
    {
        "name": "Void gaze", "modifier": "+9", "attack_type": "ranged touch",
        "attack_effect": "1d6 negative energy plus 1d4 Str drain", "range_value": 30, "range_unit": "imperial",
        "additional_description": "The creature's stare alone drains vitality from anyone who meets it.",
        "creature_description": "An aberrant horror whose eyes are windows onto an empty, hungry void.",
        "creature_subtype": "",
    },
    {
        "name": "Chain lightning", "modifier": "+10", "attack_type": "ranged",
        "attack_effect": "4d6 electricity", "range_value": 100, "range_unit": "imperial",
        "additional_description": "A crackling bolt arcs between the target and any nearby creatures.",
        "creature_description": "A storm-forged elemental that channels raw electrical fury across the battlefield.",
        "creature_subtype": "air",
    },
    {
        "name": "Corrosive spit", "modifier": "+6", "attack_type": "melee",
        "attack_effect": "1d6+3 plus 2d4 acid", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A slime-coated creature whose bite leaves a trail of dissolving acid.",
        "creature_subtype": "",
    },
    {
        "name": "Ectoplasmic slam", "modifier": "+7", "attack_type": "melee",
        "attack_effect": "1d8+3 plus 1d4 Str drain", "range_value": "", "range_unit": "",
        "additional_description": "A residue of ectoplasm clings to whatever the blow strikes, sapping strength.",
        "creature_description": "A restless spirit only partially anchored to the material plane, its blows both physical and spectral.",
        "creature_subtype": "incorporeal",
    },
    {
        "name": "Arcane bolt", "modifier": "+8", "attack_type": "ranged touch",
        "attack_effect": "2d6 force", "range_value": 60, "range_unit": "imperial",
        "additional_description": "",
        "creature_description": "A small but dangerous magical construct that fires bolts of pure magical force.",
        "creature_subtype": "augmented",
    },
    {
        "name": "Silence touch", "modifier": "+5", "attack_type": "melee touch",
        "attack_effect": "silence", "range_value": "", "range_unit": "",
        "additional_description": "An unnatural hush follows wherever the creature's hand falls.",
        "creature_description": "A fey creature attuned to the power of stillness and quiet, capable of silencing a target with a touch.",
        "creature_subtype": "chaotic",
    },
    {
        "name": "Draconic claw", "modifier": "+14", "attack_type": "melee",
        "attack_effect": "2d6+9", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A young dragon's claw, still growing into the devastating power of its adult form.",
        "creature_subtype": "reptilian",
    },
    {
        "name": "Water jet", "modifier": "+6", "attack_type": "ranged",
        "attack_effect": "2d6", "range_value": 30, "range_unit": "imperial",
        "additional_description": "A high-pressure blast of water strong enough to knock a target prone.",
        "creature_description": "An aquatic elemental that channels the crushing force of the deep through a focused jet.",
        "creature_subtype": "water",
    },
    {
        "name": "Extraplanar rend", "modifier": "+12", "attack_type": "melee",
        "attack_effect": "2d8+8 plus 1d6 negative energy", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A fiend given form on the material plane, its claws carrying a residue of its home plane's malice.",
        "creature_subtype": "extraplanar",
    },
    {
        "name": "Angelic smite", "modifier": "+13", "attack_type": "melee",
        "attack_effect": "2d8+9 plus positive energy", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A celestial warrior whose blade channels raw holy power with every blow.",
        "creature_subtype": "angel",
    },
    {
        "name": "Psionic blast", "modifier": "+9", "attack_type": "ranged",
        "attack_effect": "3d6", "range_value": 50, "range_unit": "imperial",
        "additional_description": "A concentrated burst of psionic force, no less real for being invisible.",
        "creature_description": "A creature of pure mental discipline, capable of projecting psionic force as a tangible weapon.",
        "creature_subtype": "psionic",
    },
    {
        "name": "Faerie sting", "modifier": "+5", "attack_type": "melee",
        "attack_effect": "1d3 plus 1d4 Dex drain", "range_value": "", "range_unit": "",
        "additional_description": "",
        "creature_description": "A diminutive fey whose sting saps grace and coordination from its target.",
        "creature_subtype": "chaotic",
    },
]
