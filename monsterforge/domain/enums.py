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

class Usage(str, Enum): # usato per move e Item
    UNLIMITED = "unlimited"       # Illimitato
    DAILY = "daily"                # Giornaliero
    LIMITED = "limited"            # Limitato
    SITUATIONAL = "situational"    # Situazionale

class TimeUnit(str, Enum):  # usato per move e Item
    ROUND = "round"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

class DamageType(str, Enum):    # used for damage classification per move e Item
    PHYSICAL = "physical"
    FIRE = "fire"
    COLD = "cold"
    ACID = "acid"
    LIGHTNING = "lightning"    # elettricità
    THUNDER = "thunder"        # suono
    DISINTEGRATION = "disintegration"
    NEGATIVE_ENERGY = "negative_energy"
    POSITIVE_ENERGY = "positive_energy"

class AffectedAttribute(str, Enum):    # si usa in caso di bonus , malus o cura per move e Item
    #VITA
    TOTAL_LIFE = "total_life"         #VITA
    CURRENT_LIFE  = "current_life"    #VITA_TEMPORANEA
    #PROTEZIONE
    ARMOR  = "armor"                  #ARMATURA
    TALISMAN  = "talisman"            #TALISMANO
    #PUNTI
    STAMINA  = "stamina"              #FIATO
    MANA  = "mana"                    #MAGIA
    #INTERPRETAZIONE
    ATHLETICS  = "athletics"          #ATLETICA
    EMPATHY  = "empathy"              #EMPATIA
    PERCEPTION  = "perception"        #PERCEZIONE
    STEALTH  = "stealth"              #FURTIVITA
    KNOWLEDGE  = "knowledge"          #CULTURA
    CRAFTING  = "crafting"            #ARTIGIANATO
    #CORPO
    ATTACK  = "attack"                #ATTACCO
    DEFENSE  = "defense"              #DIFESA
    SPEED  = "speed"                  #VELOCITA
    #SPIRITO
    POWER  = "power"                  #POTERE
    WARD  = "ward"                    #TANGENZA
    FLOW  = "flow"                    #SPIN

# =====================
# CREATURE
# =====================
class CreatureType(str, Enum):
    ANIMAL = "animal"               # ANIMALE
    MONSTER = "monster"             # BESTIA_MAGICA, ABBERRAZIONE
    CONSTRUCT = "construct"         # COSTRUTTO
    DRAGON = "dragon"               # DRAGO
    ELEMENTAL = "elemental"         # ELEMENTALE
    OUTSIDER = "outsider"           # ESTERNO
    FEY = "fey"                     # FOLLETTO
    OOZE = "ooze"                   # MELMA
    UNDEAD = "undead"               # NON_MORTO
    VERMIN = "vermin"               # PARASSITA
    HUMANOID = "humanoid"           # UMANOIDE, UMANOIDE_MOSTRUOSO, GIGANTE
    PLANT = "plant"                 # VEGETALE

# =====================
# MOVE
# =====================
class MoveType(str, Enum):       # TIPO
    PHYSICAL = "physical"   # Fisico
    MAGICAL = "magical"     # Magico

class MoveCategory(str, Enum):   # Categoria
    ATTACK = "attack"       # Attacco
    DEFENSE = "defense"     # Difesa
    SPECIAL = "special"     # Speciale

class MoveMode(str, Enum):       # Modalita
    ACTIVE = "active"       # Attivo
    PASSIVE = "passive"     # Passivo

class EffectType(str, Enum):     #"Danno", "Cura", Bonus, malus,  fare enumerabile
    DAMAGE = "damage"
    HEALING = "healing"
    BONUS = "bonus"
    MALUS = "malus"
    ENTITY = "entity"       # influenza l'entità in quanto tale aggiunge o toglie carte al mazzo

class EntityEffect(str, Enum):
    CREATURES = "creatures"
    MOVES = "moves"
    ITEMS = "items" 

class Target(str, Enum):         # Bersaglio
    SINGLE = "single"       # Singolo
    MULTIPLE = "multiple"   # multiplo
    AREA = "area"           # Area
    SELF = "self"           # Se stesso

class MoveRange(str, Enum):     # Gittata
    MELEE = "melee"        # contatto
    RANGED = "ranged"      # distanza in metri

class Resource(str, Enum):       # Risorsa
    STAMINA = "stamina"     # Fiato
    MANA = "mana"           # Magia
    NONE = "none"           # Nessuna

class Duration(str, Enum):                 # Durata
    INSTANT = "instant"               # Istantaneo
    CONCENTRATION = "concentration"   # concentrazione
    TEMPORARY = "temporary"           # Temporaneo
    PERMANENT = "permanent"           # Permanente


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
    ATTACK  = "attack"    #ATTACCO
    DEFENSE  = "defense"  #DIFESA
    SPEED  = "speed"      #VELOCITA

class SpiritStat(str, Enum):
    POWER  = "power"  #POTERE
    WARD  = "ward"    #TANGENZA
    FLOW  = "flow"    #SPIN

   