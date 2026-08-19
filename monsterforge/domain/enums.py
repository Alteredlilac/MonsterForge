"""
Defines enumerations used by the domain models.

Enums provide a controlled set of values for domain concepts such as
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

class Usage(str, Enum): # used for moves and items
    UNLIMITED = "unlimited"
    DAILY = "daily"
    LIMITED = "limited"
    SITUATIONAL = "situational"

class TimeUnit(str, Enum):  # used for moves and items
    ROUND = "round"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

class DamageType(str, Enum):    # used for damage classification per move and item
    PHYSICAL = "physical"
    FIRE = "fire"
    COLD = "cold"
    ACID = "acid"
    LIGHTNING = "lightning"
    THUNDER = "thunder"
    DISINTEGRATION = "disintegration"
    NEGATIVE_ENERGY = "negative_energy"
    POSITIVE_ENERGY = "positive_energy"

class AffectedAttribute(str, Enum):    # used for a bonus, malus, or healing on a move or item
    TOTAL_LIFE = "total_life"
    CURRENT_LIFE  = "current_life"
    ARMOR  = "armor"
    TALISMAN  = "talisman"
    STAMINA  = "stamina"
    MANA  = "mana"
    ATHLETICS  = "athletics"
    EMPATHY  = "empathy"
    PERCEPTION  = "perception"
    STEALTH  = "stealth"
    KNOWLEDGE  = "knowledge"
    CRAFTING  = "crafting"
    ATTACK  = "attack"
    DEFENSE  = "defense"
    SPEED  = "speed"
    POWER  = "power"
    WARD  = "ward"
    FLOW  = "flow"

# =====================
# CREATURE
# =====================
class CreatureType(str, Enum):
    ANIMAL = "animal"
    MONSTER = "monster"             # covers Magical Beast and Aberration
    CONSTRUCT = "construct"
    DRAGON = "dragon"
    ELEMENTAL = "elemental"
    OUTSIDER = "outsider"
    FEY = "fey"
    OOZE = "ooze"
    UNDEAD = "undead"
    VERMIN = "vermin"
    HUMANOID = "humanoid"           # covers Humanoid, Monstrous Humanoid, and Giant
    PLANT = "plant"

# =====================
# MOVE
# =====================
class MoveType(str, Enum):
    PHYSICAL = "physical"
    MAGICAL = "magical"

class MoveCategory(str, Enum):
    ATTACK = "attack"
    DEFENSE = "defense"
    SPECIAL = "special"

class MoveMode(str, Enum):
    ACTIVE = "active"
    PASSIVE = "passive"

class EffectType(str, Enum):
    DAMAGE = "damage"
    HEALING = "healing"
    BONUS = "bonus"
    MALUS = "malus"
    ENTITY = "entity"       # affects the entity itself — adds or removes cards
                             # from the deck; also used for effects like knockback
                             # or other things that affect entities directly
class EntityEffect(str, Enum):
    CREATURES = "creatures"
    MOVES = "moves"
    ITEMS = "items"

class Target(str, Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"
    AREA = "area"
    SELF = "self"

class MoveRange(str, Enum):
    MELEE = "melee"        # touch range
    RANGED = "ranged"      # distance in meters

class Resource(str, Enum):
    STAMINA = "stamina"
    MANA = "mana"
    NONE = "none"

class Duration(str, Enum):
    INSTANT = "instant"
    CONCENTRATION = "concentration"
    TEMPORARY = "temporary"
    PERMANENT = "permanent"


# =====================
# ITEM
# =====================
class ItemType(str, Enum):
    WEAPON = "weapon"          # attack actions
    DEFENSE = "defense"        # defense actions
    EQUIPMENT = "equipment"    # passive effects
    TOOL = "tool"              # active usage

class RequirementType(str, Enum):
    ITEM = "item"
    STAT = "stat"
    MOVE = "move"
    CREATURE = "creature"


# =====================
# DOMAIN STATS
# =====================
# NOTE:
# These enums represent MonsterForge domain concepts.
# They are currently consumed by transformation logic to build
# domain objects from external systems.
class BodyStat(str, Enum):
    ATTACK  = "attack"
    DEFENSE  = "defense"
    SPEED  = "speed"

class SpiritStat(str, Enum):
    POWER  = "power"
    WARD  = "ward"
    FLOW  = "flow"

class Interpretation(str, Enum):
    ATHLETICS  = "athletics"
    EMPATHY  = "empathy"
    PERCEPTION  = "perception"
    STEALTH  = "stealth"
    KNOWLEDGE  = "knowledge"
    CRAFTING  = "crafting"
