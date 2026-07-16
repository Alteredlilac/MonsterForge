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

class UnitSystem(str, Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"
    
class Size(str, Enum):   # usato per creature e Item
    FINE = "fine"             #Minuta
    DIMINUTIVE = "diminutive" #Piccolissima
    TINY = "tiny"             #Minuscola
    SMALL = "small"           #Piccola
    MEDIUM = "medium"         #Media
    LARGE = "large"           #Grande
    HUGE = "huge"             #Enorme
    GARGANTUAN = "gargantuan" #Mastodontica
    COLOSSAL = "colossal"     #Colossale

class DiceType(str, Enum):
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
    NEGATES = "negates"       # il tiro salvezza nega completamente l'effetto
    HALF = "half"             # il tiro salvezza dimezza i danni
    PARTIAL = "partial"       # il tiro salvezza riduce parzialmente l'effetto
    DISBELIEF = "disbelief"   # il tiro salvezza permette di dubitare dell'illusione

class TimeUnit(str, Enum):  # usato per move e Item
    ROUND = "round"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

class Usage(str, Enum): # usato per move e Item
    UNLIMITED = "unlimited"       # Illimitato
    DAILY = "daily"                # Giornaliero
    LIMITED = "limited"            # Limitato
    SITUATIONAL = "situational"    # Situazionale

class Duration(str, Enum):                 # Durata
    INSTANT = "instant"               # Istantaneo
    CONCENTRATION = "concentration"   # concentrazione
    TEMPORARY = "temporary"           # Temporaneo
    PERMANENT = "permanent"           # Permanente

class AreaEffectShape(str, Enum):   # Forma dell'area di effetto
    BURST = "burst"              # esplosione (si espande da un punto)
    SPREAD = "spread"            # propagazione (si espande seguendo linee di effetto)
    EMANATION = "emanation"      # emanazione (si estende da una creatura o punto)
    LINE = "line"                # linea
    CONE = "cone"                # cono
    SQUARE = "square"            # quadrato
    CUBE = "cube"                # cubo
    SPHERE = "sphere"            # sfera
    CYLINDER = "cylinder"        # cilindro

# =====================
# CREATURE
# =====================
class CreatureType(str, Enum):
    ANIMAL = "animal"               # ANIMALE
    ABERRATION = "aberration"       # ABBERRAZIONE
    BEAST = "beast"                 # BESTIA  -> V3.0 only
    MAGICAL_BEAST = "magical beast" # BESTIA_MAGICA
    CONSTRUCT = "construct"         # COSTRUTTO
    DRAGON = "dragon"               # DRAGO
    ELEMENTAL = "elemental"         # ELEMENTALE    
    GIANT = "giant"                 # GIGANTE
    OUTSIDER = "outsider"           # ESTERNO
    FEY = "fey"                     # FOLLETTO
    OOZE = "ooze"                   # MELMA
    UNDEAD = "undead"               # NON_MORTO
    VERMIN = "vermin"               # PARASSITA
    HUMANOID = "humanoid"           # UMANOIDE
    MONSTROUS_HUMANOID = "monstrous humanoid" # UMANOIDE_MOSTRUOSO 
    PLANT = "plant"                 # VEGETALE

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
    REPTILIAN = "reptilian" 
    SHAPECHANGER = "shapechanger" 
    SWARM = "swarm" 
    WATER = "water" 

class MovementMode(str, Enum): # metodi di movimento
    LAND = "land"      # movimento via terra
    FLY = "fly"        # volare
    SWIM = "swim"      # nuotare
    CLIMB = "climb"    # scalare
    BURROW = "burrow"  # scavare

class FlyManeuverability(str, Enum): # manovrabilità di volo
    PERFECT = "perfect"  # perfetta
    GOOD = "good"        # buona
    AVERAGE = "average"  # media
    POOR = "poor"        # scarsa
    CLUMSY = "clumsy"    # maldestra

class Alignment(str, Enum):
    LAWFUL_GOOD = "Lawful Good"
    NEUTRAL_GOOD = "Neutral Good"
    CHAOTIC_GOOD = "Chaotic Good"
    LAWFUL_NEUTRAL = "Lawful Neutral"
    NEUTRAL = "Neutral"
    CHAOTIC_NEUTRAL = "Chaotic Neutral"
    LAWFUL_EVIL = "Lawful Evil"
    NEUTRAL_EVIL = "Neutral Evil"
    CHAOTIC_EVIL = "Chaotic Evil"

# =====================
# MAGIC
# =====================
class MagicType(str, Enum):
    ARCANE = "arcane"
    DIVINE = "divine"

# =====================
# ATTACKS
# =====================
class DamageType(str, Enum):
    # FISICI
    BLUDGEONING = "bludgeoning"
    SLASHING = "slashing"
    PIERCING = "piercing"
    PHYSICAL = "physical"
    # NOTE:
    # PHYSICAL is a generic category used when the specific physical damage
    # type is unknown or cannot be mapped to a standard D&D damage type.
    # ENERGY DAMAGE
    FIRE = "fire"              # fuoco
    COLD = "cold"              # freddo
    ACID = "acid"              # acido
    ELECTRICITY = "electricity" # elettricità
    SONIC = "sonic"            # sonoro
    # FORCE / DISINTEGRATION
    DISINTEGRATION = "disintegration"
    FORCE = "force"
    # ENERGIA NEGATIVA/ POSITIVA
    NEGATIVE_ENERGY = "negative_energy"
    POSITIVE_ENERGY = "positive_energy"
    # RISUCCHIO
    ENERGY_DRAIN = "energy_drain"

# =====================
# SPECIAL ABILITY
# =====================
class SpecialAbilityType(str, Enum):
    EXTRAORDINARY = "extraordinary"
    SUPERNATURAL = "supernatural"
    SPELL_LIKE = "spell_like"
