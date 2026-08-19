"""
Defines enumerations used by the structured data, dnd V3.x models.

Enums provide a controlled set of values for dnd V3.x models such as
creature types, categories, and other fixed options.
"""

# NOTE: All enums inherit from (str, Enum) rather than plain Enum.
# This makes members JSON-serializable out of the box (e.g. json.dumps(MoveType.PHYSICAL)
# works directly, no need for `.value`), which simplifies building prompts for and
# parsing responses from the LLM classifier in the llm/ module.
from enum import Enum

# =====================
# GENERAL
# =====================
class MoveType(str, Enum):
    PHYSICAL = "physical"
    MAGICAL = "magical"

class UnitSystem(str, Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"

class Size(str, Enum):   # used for creatures and items
    FINE = "fine"
    DIMINUTIVE = "diminutive"
    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"
    GARGANTUAN = "gargantuan"
    COLOSSAL = "colossal"

class DiceType(str, Enum):
    D2 = "d2"
    D3 = "d3"
    D4 = "d4"
    D6 = "d6"
    D8 = "d8"
    D10 = "d10"
    D12 = "d12"

class Ability(str, Enum):
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    CONSTITUTION = "constitution"
    INTELLIGENCE = "intelligence"
    WISDOM = "wisdom"
    CHARISMA = "charisma"

class SavingThrowType(str, Enum):
    FORTITUDE = "fortitude"
    REFLEX = "reflex"
    WILL = "will"

class SavingThrowEffect(str, Enum):
    NEGATES = "negates"       # the saving throw completely negates the effect
    HALF = "half"             # the saving throw halves the damage
    PARTIAL = "partial"       # the saving throw partially reduces the effect
    DISBELIEF = "disbelief"   # the saving throw allows disbelief of the illusion

class TimeUnit(str, Enum):  # used for moves and items
    ROUND = "round"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

class Usage(str, Enum): # used for moves and items
    UNLIMITED = "unlimited"
    DAILY = "daily"
    LIMITED = "limited"
    SITUATIONAL = "situational"

class Duration(str, Enum):
    INSTANT = "instant"
    CONCENTRATION = "concentration"
    TEMPORARY = "temporary"
    PERMANENT = "permanent"

class AreaEffectShape(str, Enum):
    BURST = "burst"              # expands outward from a point
    SPREAD = "spread"            # expands following lines of effect
    EMANATION = "emanation"      # extends from a creature or point
    LINE = "line"
    CONE = "cone"
    SQUARE = "square"
    CUBE = "cube"
    SPHERE = "sphere"
    CYLINDER = "cylinder"

class DamageType(str, Enum):
    # PHYSICAL
    BLUDGEONING = "bludgeoning"
    SLASHING = "slashing"
    PIERCING = "piercing"
    PHYSICAL = "physical"
    # NOTE:
    # PHYSICAL is a generic category used when the specific physical damage
    # type is unknown or cannot be mapped to a standard D&D damage type.
    # ENERGY DAMAGE
    FIRE = "fire"
    COLD = "cold"
    ACID = "acid"
    ELECTRICITY = "electricity"
    SONIC = "sonic"
    # FORCE / DISINTEGRATION
    DISINTEGRATION = "disintegration"
    FORCE = "force"
    # NEGATIVE / POSITIVE ENERGY
    NEGATIVE_ENERGY = "negative_energy"
    POSITIVE_ENERGY = "positive_energy"
    # DRAIN
    ENERGY_DRAIN = "energy_drain"

class ConditionType(str, Enum):
    BLEEDING = "bleeding"
    BLINDED = "blinded"
    BLOWN_AWAY = "blown_away"
    CHECKED = "checked"
    CONFUSED = "confused"
    COWERING = "cowering"
    DAZED = "dazed"
    DAZZLED = "dazzled"
    DEAD = "dead"
    DEAFENED = "deafened"
    DISABLED = "disabled"
    DOMINATED = "dominated"
    DYING = "dying"
    ENERGY_DRAINED = "energy_drained"
    ENTANGLED = "entangled"
    EXHAUSTED = "exhausted"
    FASCINATED = "fascinated"
    FATIGUED = "fatigued"
    FLAT_FOOTED = "flat_footed"
    FRIGHTENED = "frightened"
    GRAPPLING = "grappling"
    HELPLESS = "helpless"
    INCORPOREAL = "incorporeal"
    INVISIBLE = "invisible"
    KNOCKED_DOWN = "knocked_down"
    NAUSEATED = "nauseated"
    PANICKED = "panicked"
    PARALYZED = "paralyzed"
    PETRIFIED = "petrified"
    PINNED = "pinned"
    PRONE = "prone"
    SHAKEN = "shaken"
    SICKENED = "sickened"
    STABLE = "stable"
    STAGGERED = "staggered"
    STUNNED = "stunned"
    TURNED = "turned"
    UNCONSCIOUS = "unconscious"

class TargetType(str, Enum):
    CREATURE = "creature"
    OBJECT = "object"
    AREA = "area"
    EFFECT = "effect"
    SOMETHING = "something"   # creatures and objects
    EVERYTHING = "everything" # also effects and spells, e.g. an antimagic field

class RequirementOperator(str, Enum):
    LESS_THAN = "less_than"
    LESS_OR_EQUAL = "less_or_equal"
    EQUAL = "equal"
    GREATER_OR_EQUAL = "greater_or_equal"
    GREATER_THAN = "greater_than"

class GrantedType(str, Enum):
    CREATURE = "creature"     # e.g. summoning or a charm effect
    PHYSICAL_FORM = "physical_form"
    OBJECT = "object"
    ATTACK = "attack"
    CLASS = "class"
    FEAT = "feat"
    PSIONIC_POWER = "psionic_power"
    SPECIAL_ATTACK = "special_attack"
    SPECIAL_QUALITY = "special_quality"
    SPELL = "spell"

class ModifierTarget(str, Enum):
    HIT_DICE = "hit_dice"
    RANGE = "range"
    HIT_POINTS = "hit_points"
    SKILL_BONUS = "skill_bonus"
    ABILITY_SCORE = "ability_score"
    ATTACK_BONUS = "attack_bonus"  # to-hit roll
    SAVING_THROW = "saving_throw"
    SPELL_RESISTANCE = "spell_resistance"
    POWER_RESISTANCE = "power_resistance"
    DAMAGE = "damage"
    TURN_RESISTANCE = "turn_resistance" # turning undead

class ModifierConditionType(str, Enum):
    EFFECT = "effect"
    CREATURE = "creature"
    OBJECT = "object"


# =====================
# CREATURE
# =====================
class CreatureType(str, Enum):
    ANIMAL = "animal"
    ABERRATION = "aberration"
    BEAST = "beast"                 # V3.0 only
    MAGICAL_BEAST = "magical_beast"
    CONSTRUCT = "construct"
    DRAGON = "dragon"
    ELEMENTAL = "elemental"
    GIANT = "giant"
    OUTSIDER = "outsider"
    FEY = "fey"
    OOZE = "ooze"
    UNDEAD = "undead"
    VERMIN = "vermin"
    HUMANOID = "humanoid"
    MONSTROUS_HUMANOID = "monstrous_humanoid"
    PLANT = "plant"

class CreatureSubtype(str, Enum):
    AIR = "air"
    ANGEL = "angel"
    AQUATIC = "aquatic"
    ARCHON = "archon"
    AUGMENTED = "augmented"
    CHAOTIC = "chaotic"
    COLD = "cold"
    EARTH = "earth"
    EVIL = "evil"
    EXTRAPLANAR = "extraplanar"
    FIRE = "fire"
    GOBLINOID = "goblinoid"
    GOOD = "good"
    INCORPOREAL = "incorporeal"
    LAWFUL = "lawful"
    NATIVE = "native"
    PSIONIC = "psionic"
    REPTILIAN = "reptilian"
    SHAPECHANGER = "shapechanger"
    SWARM = "swarm"
    WATER = "water"

class MovementMode(str, Enum):
    LAND = "land"
    FLY = "fly"
    SWIM = "swim"
    CLIMB = "climb"
    BURROW = "burrow"

class FlyManeuverability(str, Enum):
    PERFECT = "perfect"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    CLUMSY = "clumsy"

class Alignment(str, Enum):
    LAWFUL_GOOD = "Lawful_Good"
    NEUTRAL_GOOD = "Neutral_Good"
    CHAOTIC_GOOD = "Chaotic_Good"
    LAWFUL_NEUTRAL = "Lawful_Neutral"
    NEUTRAL = "Neutral"
    CHAOTIC_NEUTRAL = "Chaotic_Neutral"
    LAWFUL_EVIL = "Lawful_Evil"
    NEUTRAL_EVIL = "Neutral_Evil"
    CHAOTIC_EVIL = "Chaotic_Evil"

# =====================
# MAGIC / PSIONIC
# =====================
class MagicType(str, Enum):
    ARCANE = "arcane"
    DIVINE = "divine"

class MagicSchool(str, Enum):
    ABJURATION = "abjuration"
    CONJURATION = "conjuration"
    DIVINATION = "divination"
    ENCHANTMENT = "enchantment"
    EVOCATION = "evocation"
    ILLUSION = "illusion"
    NECROMANCY = "necromancy"
    TRANSMUTATION = "transmutation"
    UNIVERSAL = "universal"

class PsionicDiscipline(str, Enum):
    CLAIRSENTIENCE = "clairsentience"
    METACREATIVITY = "metacreativity"
    PSYCHOKINESIS = "psychokinesis"
    PSYCHOMETABOLISM = "psychometabolism"
    PSYCHOPORTATION = "psychoportation"
    TELEPATHY = "telepathy"

class CastingTime(str, Enum):
    STANDARD_ACTION = "standard_action"
    MOVE_ACTION = "move_action"
    FULL_ROUND_ACTION = "full-round_action"
    FREE_ACTION = "free_action"
    IMMEDIATE_ACTION = "immediate_action"
    SWIFT_ACTION = "swift_action"
    ROUND = "round"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"

class SpellRangeType(str, Enum):
    TOUCH = "touch"
    PERSONAL = "personal"
    UNLIMITED = "unlimited"

# =====================
# SPECIAL ABILITY
# =====================
class SpecialAbilityType(str, Enum):
    EXTRAORDINARY = "extraordinary"
    SUPERNATURAL = "supernatural"
    SPELL_LIKE = "spell_like"

# =====================
# FEATS
# =====================
class FeatCategory(str, Enum):
    METAMAGIC = "metamagic"
    METAPSIONIC = "metapsionic"
    GRANTS_BONUS = "grants_bonus"    # grants a bonus or modifier
    CRAFTING = "crafting"            # item-creation feats
    GRANTS_ATTACK = "grants_attack"  # grants a special attack
    GRANTS_QUALITY = "grants_quality"# grants a special quality
    PROFICIENCY = "proficiency"      # grants a proficiency
    GRANTS_ITEM = "grants_item"      # grants or simulates possessing an item
    GRANTS_CREATURE = "grants_creature" # grants a creature or companion
    GENERIC = "generic"              # generic catch-all category
    PSIONIC = "psionic"              # psionic feat
    CLASS_RELATED = "class_related"  # feat tied to a specific class

# =====================
# CHARACTER CLASS
# =====================
class ProgressionRate(str, Enum):
    LOW = "low"        # +10 max, e.g. wizard (1/2 level)
    MEDIUM = "medium"  # +15 max, e.g. cleric (3/4 level)
    HIGH = "high"      # +20 max, e.g. fighter (= level)

class SaveProgression(str, Enum):
    POOR = "poor"
    GOOD = "good"

class ClassPrivilegeType(str, Enum):
    ATTACK = "attack"
    FULL_ATTACK = "full_attack"
    SPECIAL_ATTACK = "special_attack"
    SPECIAL_QUALITY = "special_quality"
    FEAT = "feat"
    COMPANION = "companion"
    DOMAIN = "domain"
    ITEM = "item"
    PSIONIC_POWER = "psionic_power"
    SPELL = "spell"
    SPELLCASTING = "spellcasting"
    PSIONIC_MANIFESTING = "psionic_manifesting"
    CREATURE_MODIFIER = "creature_modifier"

# =====================
# COMPANION
# =====================
class CompanionPrivilegeType(str, Enum):
    ATTACK = "attack"
    FULL_ATTACK = "full_attack"
    SPECIAL_ATTACK = "special_attack"
    SPECIAL_QUALITY = "special_quality"
    FEAT = "feat"
    ITEM = "item"
    PSIONIC_POWER = "psionic_power"
    SPELL = "spell"
    CREATURE_MODIFIER = "creature_modifier"

# =====================
# ITEM
# =====================
class ItemType(str, Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    GENERIC = "generic"
    TOOL = "tool"
    ALCHEMICAL = "alchemical"
    POISON = "poison"
    CLOTHING = "clothing"
    ACCESSORY = "accessory"

class ItemPowerType(str, Enum):
    MAGICAL = "magical"
    PSIONIC = "psionic"

class IntelligentItemType(str, Enum):
    INTELLIGENT = "intelligent"
    SYMBIOTIC = "symbiotic"
    POSSESSED = "possessed"

# =====================
# SKILL ID
# =====================
# NOTE:
# These enum is currently consumed by transformation logic to build
# domain objects from external systems.
class SkillId(str, Enum):
    # STANDARD SKILLS 3.5
    APPRAISE = "appraise"
    BALANCE = "balance"
    BLUFF = "bluff"
    CLIMB = "climb"
    CONCENTRATION = "concentration"

    CRAFT = "craft"
    ## Craft (alchemy, weaponsmithing, etc.)

    DECIPHER_SCRIPT = "decipher_script"
    DIPLOMACY = "diplomacy"
    DISABLE_DEVICE = "disable_device"
    DISGUISE = "disguise"
    ESCAPE_ARTIST = "escape_artist"
    FORGERY = "forgery"
    GATHER_INFORMATION = "gather_information"
    HANDLE_ANIMAL = "handle_animal"
    HEAL = "heal"
    HIDE = "hide"
    INTIMIDATE = "intimidate"
    JUMP = "jump"

    KNOWLEDGE = "knowledge"
    ## Knowledge (arcana, nature, religion, etc.)

    LISTEN = "listen"
    MOVE_SILENTLY = "move_silently"
    OPEN_LOCK = "open_lock"

    PERFORM = "perform"
    # Perform (sing, dance, oratory, etc.)

    PROFESSION = "profession"
    # Profession (farmer, sailor, merchant, etc.)

    RIDE = "ride"
    SEARCH = "search"
    SENSE_MOTIVE = "sense_motive"
    SLEIGHT_OF_HAND = "sleight_of_hand"

    # NOTE: speak_language is intentionally excluded from skill mapping:
    # languages are tracked separately, as known languages rather than numeric skill values

    SPELLCRAFT = "spellcraft"
    SPOT = "spot"
    SURVIVAL = "survival"
    SWIM = "swim"
    TUMBLE = "tumble"
    USE_MAGIC_DEVICE = "use_magic_device"
    USE_ROPE = "use_rope"

    # PSIONIC SKILLS 3.5
    AUTOHYPNOSIS = "autohypnosis"
    PSICRAFT = "psicraft"
    USE_PSIONIC_DEVICE = "use_psionic_device"

    # NOTE: the following skills are specific to version 3.0.
    # STANDARD SKILLS 3.0
    ALCHEMY = "alchemy"
    INNUENDO = "innuendo"
    ANIMAL_EMPATHY = "animal_empathy"
    READ_LIPS = "read_lips"
    INTUIT_DIRECTION = "intuit_direction"
    SCRY = "scry"
    PICK_POCKET = "pick_pocket"

    # PSIONIC SKILLS 3.0
    STABILIZE_SELF = "stabilize_self"
    REMOTE_VIEW = "remote_view"
