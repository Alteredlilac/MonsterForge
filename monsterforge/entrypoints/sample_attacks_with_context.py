"""
The same 65 cases as sample_attacks.py, each paired with the optional
semantic context (additional_description, creature_description,
creature_subtype) that classify_attack() accepts but that
collect_real_classifications.py/collect_real_pipeline_conversions.py
have so far always defaulted to None (see PROJECT_STATUS.md's Open
TODOs). Reuses SAMPLE_ATTACKS by reference rather than retyping the raw
fields, so the two files can never drift apart on the base attack data.

Each entry is {"raw_attack": <dict from SAMPLE_ATTACKS>, "context": {...}}
rather than one flat dict, since raw_attack is passed to RawAttack(**...)
and context is spread directly into classify_attack(**...) at the call
site -- keeping them separate avoids RawAttack rejecting the extra
context keys as unexpected arguments.

creature_description/additional_description values are invented,
SRD-flavored prose (not copied from any specific published monster).
creature_subtype is left None except where the attack itself implies a
real D&D 3.x subtype (incorporeal touch attacks, fire/energy attacks,
swarms, and similar) -- this is what actually exercises the prompt's
subtype-conditioned rules (e.g. "if creature subtype is incorporeal,
always classify as magical"), rather than decorating every case with an
unearned subtype.
"""
from .sample_attacks import SAMPLE_ATTACKS

SAMPLE_ATTACKS_WITH_CONTEXT = [
    {  # 0: Tentacle, 1d6+8 plus slime
        "raw_attack": SAMPLE_ATTACKS[0],
        "context": {
            "additional_description": "The tentacle leaves behind a smear of caustic slime wherever it strikes.",
            "creature_description": "A bloated, many-limbed horror that drags itself through swamp and cave, each tentacle slick with corrosive mucus.",
            "creature_subtype": None,
        },
    },
    {  # 1: Claw, 2d6+4
        "raw_attack": SAMPLE_ATTACKS[1],
        "context": {
            "additional_description": None,
            "creature_description": "A powerful predator built for close combat, relying on raw strength to bring down prey.",
            "creature_subtype": None,
        },
    },
    {  # 2: Incorporeal touch, 1d4 Wisdom drain
        "raw_attack": SAMPLE_ATTACKS[2],
        "context": {
            "additional_description": "The touch saps the victim's clarity of mind, leaving confusion in its wake.",
            "creature_description": "A restless spirit bound to the site of its death, passing through walls and armor alike to feed on the minds of the living.",
            "creature_subtype": "incorporeal",
        },
    },
    {  # 3: Bite, 1d6 plus poison
        "raw_attack": SAMPLE_ATTACKS[3],
        "context": {
            "additional_description": None,
            "creature_description": "A fanged ambush predator whose bite delivers a potent venom.",
            "creature_subtype": None,
        },
    },
    {  # 4: Web (ranged, no effect text)
        "raw_attack": SAMPLE_ATTACKS[4],
        "context": {
            "additional_description": "In spider or hybrid form (see below), an aranea can throw a web up to six times per day. This is similar to an attack with a net but has a maximum range of 50 feet, with a range increment of 10 feet, and is effective against targets of up to Large size. The web anchors the target in place, allowing no movement.\n\nAn entangled creature can escape with a DC 13 Escape Artist check or burst the web with a DC 17 Strength check. The check DCs are Constitution-based, and the Strength check DC includes a +4 racial bonus. The web has 6 hit points, hardness 0, and takes double damage from fire.",
            "creature_description": "An oversized arachnid that spins thick webbing to snare prey before closing in.",
            "creature_subtype": None,
        },
    },
    {  # 5: Light ray, ranged touch, 1d6
        "raw_attack": SAMPLE_ATTACKS[5],
        "context": {
            "additional_description": "A lantern archon's light rays have a range of 30 feet. This attack overcomes damage reduction of any type.",
            "creature_description": "A radiant guardian construct animated by captured sunlight, standing watch over sacred ground.",
            "creature_subtype": None,
        },
    },
    {  # 6: Electricity ray, ranged touch, 2d6
        "raw_attack": SAMPLE_ATTACKS[6],
        "context": {
            "additional_description": "An arrowhawk can fire this ray once per round, with a range of 50 feet.",
            "creature_description": "A crackling elemental born of storm clouds, its body a shifting mass of charged vapor.",
            "creature_subtype": "air",
        },
    },
    {  # 7: Bite, 1d6+1
        "raw_attack": SAMPLE_ATTACKS[7],
        "context": {
            "additional_description": None,
            "creature_description": "A lean, fast-moving predator that hunts in packs.",
            "creature_subtype": None,
        },
    },
    {  # 8: Morningstar, 3d6+8
        "raw_attack": SAMPLE_ATTACKS[8],
        "context": {
            "additional_description": None,
            "creature_description": "A towering warrior clad in crude armor, favoring a spiked morningstar to crush anything in its path.",
            "creature_subtype": None,
        },
    },
    {  # 9: Rock, ranged, 2d6+8
        "raw_attack": SAMPLE_ATTACKS[9],
        "context": {
            "additional_description": "The range increment is 120 feet for a hill giant's thrown rocks.",
            "creature_description": "A massive humanoid dwelling in hill country, known for hurling stones at trespassers.",
            "creature_subtype": None,
        },
    },
    {  # 10: Warhammer, 1d8+1/x3 plus 1 fire
        "raw_attack": SAMPLE_ATTACKS[10],
        "context": {
            "additional_description": "The warhammer's head glows faintly with residual heat, searing flesh on impact.",
            "creature_description": "A militant humanoid wielding a warhammer whose head has been enchanted to smolder.",
            "creature_subtype": None,
        },
    },
    {  # 11: Shortspear, ranged, 1d6+1 plus 1 fire
        "raw_attack": SAMPLE_ATTACKS[11],
        "context": {
            "additional_description": "The tip of the spear is wreathed in flame that flares briefly on impact. range 20 ft",
            "creature_description": "A nomadic raider who hurls spears wreathed in magical flame at approaching enemies.",
            "creature_subtype": None,
        },
    },
    {  # 12: Slam, 1d8+1
        "raw_attack": SAMPLE_ATTACKS[12],
        "context": {
            "additional_description": None,
            "creature_description": "A crude, hulking construct animated by ancient magic, attacking with heavy blows.",
            "creature_subtype": None,
        },
    },
    {  # 13: Claw, 1d3+2 plus corporeal instability
        "raw_attack": SAMPLE_ATTACKS[13],
        "context": {
            "additional_description": "Its claws seem to blur and phase, disrupting the cohesion of whatever they strike.",
            "creature_description": "A shifting, unstable aberration whose touch destabilizes living tissue at a molecular level.",
            "creature_subtype": None,
        },
    },
    {  # 14: Tentacle, 1d3+3
        "raw_attack": SAMPLE_ATTACKS[14],
        "context": {
            "additional_description": None,
            "creature_description": "A smaller kin of the swamp-dwelling tentacled horrors, still dangerous in close combat.",
            "creature_subtype": None,
        },
    },
    {  # 15: Bite, 1d4-2 plus petrification
        "raw_attack": SAMPLE_ATTACKS[15],
        "context": {
            "additional_description": "A creeping calcification spreads outward from any wound it inflicts.",
            "creature_description": "A reptilian horror whose gaze and bite alike can turn living flesh to solid stone.",
            "creature_subtype": "reptilian",
        },
    },
    {  # 16: Bite, 2d6+9 plus poison
        "raw_attack": SAMPLE_ATTACKS[16],
        "context": {
            "additional_description": None,
            "creature_description": "A large winged reptile whose bite injects a debilitating venom.",
            "creature_subtype": "reptilian",
        },
    },
    {  # 17: Web (ranged, no effect text) -- larger kin of case 4
        "raw_attack": SAMPLE_ATTACKS[17],
        "context": {
            "additional_description": "In spider or hybrid form (see below), an aranea can throw a web up to six times per day. This is similar to an attack with a net but has a maximum range of 50 feet, with a range increment of 10 feet, and is effective against targets of up to Large size. The web anchors the target in place, allowing no movement.\n\nAn entangled creature can escape with a DC 13 Escape Artist check or burst the web with a DC 17 Strength check. The check DCs are Constitution-based, and the Strength check DC includes a +4 racial bonus. The web has 6 hit points, hardness 0, and takes double damage from fire.",
            "creature_description": "An enormous spider, larger and hungrier than its smaller kin, capable of spinning webbing thick enough to trap prey outright.",
            "creature_subtype": None,
        },
    },
    {  # 18: Claw, 1d6+4
        "raw_attack": SAMPLE_ATTACKS[18],
        "context": {
            "additional_description": None,
            "creature_description": "A territorial predator that rakes at intruders with sharp, curved claws.",
            "creature_subtype": None,
        },
    },
    {  # 19: Claw, 2d8+6 plus fear
        "raw_attack": SAMPLE_ATTACKS[19],
        "context": {
            "additional_description": "The sheer violence of the strike is often enough to break an onlooker's resolve.",
            "creature_description": "A fearsome apex predator whose presence alone unsettles lesser creatures.",
            "creature_subtype": None,
        },
    },
    {  # 20: Slam, 1d6+1 plus 1d6 fire
        "raw_attack": SAMPLE_ATTACKS[20],
        "context": {
            "additional_description": None,
            "creature_description": "A creature wreathed in barely-contained flame, its every blow searing as much as it bruises.",
            "creature_subtype": "fire",
        },
    },
    {  # 21: Slam, 1d8+7
        "raw_attack": SAMPLE_ATTACKS[21],
        "context": {
            "additional_description": None,
            "creature_description": "A hulking brute that relies on sheer bulk and crushing blows to overwhelm its foes.",
            "creature_subtype": None,
        },
    },
    {  # 22: Morningstar, 2d6+6
        "raw_attack": SAMPLE_ATTACKS[22],
        "context": {
            "additional_description": None,
            "creature_description": "A disciplined soldier wielding a morningstar as part of a well-drilled war band.",
            "creature_subtype": None,
        },
    },
    {  # 23: Javelin, ranged, 1d8+6
        "raw_attack": SAMPLE_ATTACKS[23],
        "context": {
            "additional_description": "range 30 ft",
            "creature_description": "A swift-footed skirmisher who favors javelins for softening enemies before closing to melee.",
            "creature_subtype": None,
        },
    },
    {  # 24: blank placeholder case -- context intentionally empty too
        "raw_attack": SAMPLE_ATTACKS[24],
        "context": {
            "additional_description": None,
            "creature_description": None,
            "creature_subtype": None,
        },
    },
    {  # 25: Bite, 1d6+1 plus paralysis
        "raw_attack": SAMPLE_ATTACKS[25],
        "context": {
            "additional_description": None,
            "creature_description": "A carrion-feeder whose bite carries a paralytic toxin, useful for immobilizing prey before it can flee.",
            "creature_subtype": None,
        },
    },
    {  # 26: Greatclub, 2d8+12
        "raw_attack": SAMPLE_ATTACKS[26],
        "context": {
            "additional_description": None,
            "creature_description": "An enormous, brutish giant that fells trees to fashion crude but devastating clubs.",
            "creature_subtype": None,
        },
    },
    {  # 27: Slam, 1d4+8
        "raw_attack": SAMPLE_ATTACKS[27],
        "context": {
            "additional_description": None,
            "creature_description": "A swift, hulking creature that strikes with surprising speed despite its size.",
            "creature_subtype": None,
        },
    },
    {  # 28: Rock, ranged, 2d8+12 -- bigger kin of case 9
        "raw_attack": SAMPLE_ATTACKS[28],
        "context": {
            "additional_description": "The range increment is 120 feet for a hill giant's thrown rocks. This creature hurls a boulder large enough to crush a wagon.",
            "creature_description": "A colossal hill-dwelling giant known for flinging boulders at any who trespass on its territory.",
            "creature_subtype": None,
        },
    },
    {  # 29: Bite, 1d10+3
        "raw_attack": SAMPLE_ATTACKS[29],
        "context": {
            "additional_description": "Once its jaws close around a target, it seldom lets go.",
            "creature_description": "A powerful aquatic reptile that lurks at the water's edge, seizing prey in its crushing jaws.",
            "creature_subtype": "reptilian",
        },
    },
    {  # 30: Tentacle, 2d8+12/19-20
        "raw_attack": SAMPLE_ATTACKS[30],
        "context": {
            "additional_description": None,
            "creature_description": "A colossal denizen of the deep, whose whip-like tentacles can shear through hull and bone alike.",
            "creature_subtype": "aquatic",
        },
    },
    {  # 31: Touch, 1d4 Wisdom drain -- undead kin of case 2
        "raw_attack": SAMPLE_ATTACKS[31],
        "context": {
            "additional_description": None,
            "creature_description": "An undead spirit that drains the sanity of the living with a single touch.",
            "creature_subtype": "incorporeal",
        },
    },
    {  # 32: Dagger, 1d6+4/19-20
        "raw_attack": SAMPLE_ATTACKS[32],
        "context": {
            "additional_description": None,
            "creature_description": "A quick, cunning humanoid skilled with a blade, favoring precision over brute strength.",
            "creature_subtype": None,
        },
    },
    {  # 33: Claw, 1d4+4
        "raw_attack": SAMPLE_ATTACKS[33],
        "context": {
            "additional_description": None,
            "creature_description": "A nimble hunter that darts in to rake its prey before retreating out of reach.",
            "creature_subtype": None,
        },
    },
    {  # 34: Burning touch, melee touch, 1d8 fire plus combustion
        "raw_attack": SAMPLE_ATTACKS[34],
        "context": {
            "additional_description": "The touch leaves smoldering embers that can flare into open flame moments later.",
            "creature_description": "A being wreathed in living flame, capable of igniting anything it touches.",
            "creature_subtype": "fire",
        },
    },
    {  # 35: Slam, 1d3+3 plus combustion -- smaller kin of case 34
        "raw_attack": SAMPLE_ATTACKS[35],
        "context": {
            "additional_description": None,
            "creature_description": "A minor flame-touched creature, its body radiating enough heat to scorch on contact.",
            "creature_subtype": "fire",
        },
    },
    {  # 36: Slam, 1d8+4
        "raw_attack": SAMPLE_ATTACKS[36],
        "context": {
            "additional_description": None,
            "creature_description": "A stout, muscular creature that favors overwhelming force in melee.",
            "creature_subtype": None,
        },
    },
    {  # 37: Slam, 1d6+7
        "raw_attack": SAMPLE_ATTACKS[37],
        "context": {
            "additional_description": None,
            "creature_description": "A fast, aggressive predator that closes distance quickly to land crushing blows.",
            "creature_subtype": None,
        },
    },
    {  # 38: Tongue, melee touch, paralysis
        "raw_attack": SAMPLE_ATTACKS[38],
        "context": {
            "additional_description": "The tongue lashes out too quickly to easily dodge, numbing whatever it touches.",
            "creature_description": "An amphibious ambush predator that lashes out with a long, sticky tongue coated in paralytic toxin.",
            "creature_subtype": None,
        },
    },
    {  # 39: Bite, 2d6+6 plus disease
        "raw_attack": SAMPLE_ATTACKS[39],
        "context": {
            "additional_description": None,
            "creature_description": "A filth-encrusted predator whose bite festers with disease, often found lurking in sewers and refuse heaps.",
            "creature_subtype": None,
        },
    },
    {  # 40: Slam, 2d6+4 plus 2d6 acid
        "raw_attack": SAMPLE_ATTACKS[40],
        "context": {
            "additional_description": "A film of caustic acid coats the creature's body, burning anything it strikes.",
            "creature_description": "A corrosive, half-liquid horror whose touch dissolves flesh and metal alike.",
            "creature_subtype": None,
        },
    },
    {  # 41: Bite, 1d6+4 plus poison
        "raw_attack": SAMPLE_ATTACKS[41],
        "context": {
            "additional_description": None,
            "creature_description": "A stealthy hunter whose bite delivers a debilitating venom, favored for ambush tactics.",
            "creature_subtype": None,
        },
    },
    {  # 42: Tail slap, 1d6+1 plus positive energy
        "raw_attack": SAMPLE_ATTACKS[42],
        "context": {
            "additional_description": "The strike carries a surge of positive energy, more harmful to the undead than to the living.",
            "creature_description": "A radiant, good-aligned creature whose tail crackles with the same holy energy that sustains it.",
            "creature_subtype": "good",
        },
    },
    {  # 43: Tail touch, melee touch, positive energy -- kin of case 42
        "raw_attack": SAMPLE_ATTACKS[43],
        "context": {
            "additional_description": None,
            "creature_description": "A benevolent outsider whose touch channels raw positive energy.",
            "creature_subtype": "good",
        },
    },
    {  # 44: Antennae touch, rust
        "raw_attack": SAMPLE_ATTACKS[44],
        "context": {
            "additional_description": "Any metal object touched by the antennae begins to rust and crumble almost immediately.",
            "creature_description": "A skittish, insectoid creature whose antennae corrode metal on contact, reducing weapons and armor to flakes of rust.",
            "creature_subtype": None,
        },
    },
    {  # 45: Incorporeal touch, 1d6 Str
        "raw_attack": SAMPLE_ATTACKS[45],
        "context": {
            "additional_description": None,
            "creature_description": "A vengeful specter that saps the physical vitality of the living with an icy touch.",
            "creature_subtype": "incorporeal",
        },
    },
    {  # 46: Incorporeal touch, 1d8 plus energy drain
        "raw_attack": SAMPLE_ATTACKS[46],
        "context": {
            "additional_description": "Victims touched by the creature feel a portion of their vitality permanently siphoned away.",
            "creature_description": "A malevolent undead horror that drains the very life force from those it touches.",
            "creature_subtype": "incorporeal",
        },
    },
    {  # 47: Short sword, 1d4-2/19-20
        "raw_attack": SAMPLE_ATTACKS[47],
        "context": {
            "additional_description": None,
            "creature_description": "A lightly armed humanoid scout, relying on a short sword for quick, precise strikes.",
            "creature_subtype": None,
        },
    },
    {  # 48: Light crossbow, ranged, 1d6/19-20
        "raw_attack": SAMPLE_ATTACKS[48],
        "context": {
            "additional_description": None,
            "creature_description": "A disciplined marksman who favors the light crossbow for its reliability at range.",
            "creature_subtype": None,
        },
    },
    {  # 49: Swarm, 2d6
        "raw_attack": SAMPLE_ATTACKS[49],
        "context": {
            "additional_description": "In order to attack, a single swarm moves into opponents' spaces, which provokes an attack of opportunity. It can occupy the same space as a creature of any size, since it crawls all over its prey, but remains a creature with a 10-foot space. Swarms never make attacks of opportunity, but they can provoke attacks of opportunity.\n\nUnlike other creatures with a 10-foot space, a swarm is shapeable. It can occupy any four contiguous squares, and it can squeeze through any space large enough to contain one of its component creatures.",
            "creature_description": "A churning mass of biting insects that overwhelms prey through sheer numbers rather than individual strength.",
            "creature_subtype": "swarm",
        },
    },
    {  # 50: Bite, 4d8+17/18-20/x3
        "raw_attack": SAMPLE_ATTACKS[50],
        "context": {
            "additional_description": None,
            "creature_description": "An ancient, immensely powerful dragon whose bite alone can shear through castle gates.",
            "creature_subtype": "reptilian",
        },
    },
    {  # 51: Slam, 2d6+9
        "raw_attack": SAMPLE_ATTACKS[51],
        "context": {
            "additional_description": None,
            "creature_description": "A powerfully built creature that relies on brute force in melee combat.",
            "creature_subtype": None,
        },
    },
    {  # 52: Bite, 1d6+4
        "raw_attack": SAMPLE_ATTACKS[52],
        "context": {
            "additional_description": None,
            "creature_description": "A mid-sized predator with a strong, snapping bite.",
            "creature_subtype": None,
        },
    },
    {  # 53: Short sword, 1d6+2/19-20
        "raw_attack": SAMPLE_ATTACKS[53],
        "context": {
            "additional_description": None,
            "creature_description": "A trained soldier equipped with a short sword, fighting with practiced discipline.",
            "creature_subtype": None,
        },
    },
    {  # 54: Claw, 1d4+2
        "raw_attack": SAMPLE_ATTACKS[54],
        "context": {
            "additional_description": None,
            "creature_description": "A small but aggressive predator that lashes out with sharp claws.",
            "creature_subtype": None,
        },
    },
    {  # 55: Longbow, ranged, 1d8/x3
        "raw_attack": SAMPLE_ATTACKS[55],
        "context": {
            "additional_description": None,
            "creature_description": "A skilled archer favoring the longbow for its range and stopping power.",
            "creature_subtype": None,
        },
    },
    {  # 56: Slam, 1d6+1
        "raw_attack": SAMPLE_ATTACKS[56],
        "context": {
            "additional_description": None,
            "creature_description": "A young or weakened creature, still capable of landing a solid blow.",
            "creature_subtype": None,
        },
    },
    {  # 57: Club, 1d6+1
        "raw_attack": SAMPLE_ATTACKS[57],
        "context": {
            "additional_description": None,
            "creature_description": "A small, disorganized humanoid raider wielding a crude wooden club.",
            "creature_subtype": "goblinoid",
        },
    },
    {  # 58: Bite, 1d6+1
        "raw_attack": SAMPLE_ATTACKS[58],
        "context": {
            "additional_description": None,
            "creature_description": "A young predator, still growing into its full hunting strength.",
            "creature_subtype": None,
        },
    },
    {  # 59: Bite, 1d6+3 plus trip
        "raw_attack": SAMPLE_ATTACKS[59],
        "context": {
            "additional_description": "The bite is as much about dragging prey off balance as wounding it.",
            "creature_description": "A powerful predator that seizes prey in its jaws and hauls it off its feet.",
            "creature_subtype": None,
        },
    },
    {  # 60: Slam, 1d8+5 plus push
        "raw_attack": SAMPLE_ATTACKS[60],
        "context": {
            "additional_description": None,
            "creature_description": "A massive brute whose blows are as much about shoving foes aside as wounding them.",
            "creature_subtype": None,
        },
    },
    {  # 61: Tail sweep, 1d6+2 plus unbalance
        "raw_attack": SAMPLE_ATTACKS[61],
        "context": {
            "additional_description": None,
            "creature_description": "A creature with a long, muscular tail that sweeps low to knock opponents off their footing.",
            "creature_subtype": "reptilian",
        },
    },
    {  # 62: Pincers, 1d4+4 plus grapple
        "raw_attack": SAMPLE_ATTACKS[62],
        "context": {
            "additional_description": None,
            "creature_description": "A heavily armored creature with powerful pincers used to seize and crush prey.",
            "creature_subtype": None,
        },
    },
    {  # 63: Psychic lash, ranged touch, 1d6 plus stagger
        "raw_attack": SAMPLE_ATTACKS[63],
        "context": {
            "additional_description": "The creature emits a wave of psionic energy that strikes a single target within 30 feet. The lash strikes the mind directly, leaving the target reeling and disoriented.",
            "creature_description": "A creature attuned to psionic power, capable of lashing out with raw mental force.",
            "creature_subtype": "psionic",
        },
    },
    {  # 64: Arcane slam, melee touch, 1d4+2 plus disarm
        "raw_attack": SAMPLE_ATTACKS[64],
        "context": {
            "additional_description": "The impact carries a burst of arcane force strong enough to wrench a weapon from an opponent's grip.",
            "creature_description": "A creature suffused with residual arcane energy, its blows crackling with disruptive magic.",
            "creature_subtype": None,
        },
    },
]
