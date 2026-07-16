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

class HitDiceType(str, Enum):
    D4 = "d4"
    D6 = "d6"
    D8 = "d8"
    D10 = "d10"
    D12 = "d12"

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

class UnitSystem(str, Enum):
    METRIC = "metric"
    IMPERIAL = "imperial"

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