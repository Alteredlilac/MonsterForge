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

class TargetType(str, Enum):
    CREATURE = "creature"
    OBJECT = "object"
    AREA = "area"
    EFFECT = "effect"
    SOMETHING = "something"   # creature ed oggetti
    EVERYTHING = "everything" # anche effetti e incantesimi, esempio (campo antimagia)

class RequirementOperator(str, Enum):
    LESS_THAN = "less_than"
    LESS_OR_EQUAL = "less_or_equal"
    EQUAL = "equal"
    GREATER_OR_EQUAL = "greater_or_equal"
    GREATER_THAN = "greater_than"

class GrantedType(str, Enum):
    CREATURE = "creature"     # esempio evocazione o charme
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
    HIT_DICE = "hit_dice"      # dadi vita
    RANGE = "range"            # portata
    HIT_POINTS = "hit_points"  # punti ferita
    SKILL_BONUS = "skill_bonus"  # abilità
    ABILITY_SCORE = "ability_score" # caratteristiche
    ATTACK_BONUS = "attack_bonus"  # tiro per colpire
    SAVING_THROW = "saving_throw"  # tiro salvezza
    SPELL_RESISTANCE = "spell_resistance" # resistenza incantesimi
    POWER_RESISTANCE = "power_resistance" # resistenza poteri psionici
    DAMAGE = "damage"             # danni
    TURN_RESISTANCE = "turn_resistance" # resistenza allo scacciare

class ModifierConditionType(str, Enum):
    EFFECT = "effect"
    CREATURE = "creature"
    OBJECT = "object"


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
    METAMAGIC = "metamagic"       # metamagico 
    METAPSIONIC = "metapsionic"   # metapsionico
    GRANTS_BONUS = "grants_bonus" # concede bonus (esempio +2 abilità)
    CRAFTING = "crafting"         # fabbricazione (creare bacchette)
    GRANTS_ATTACK = "grants_attack" # concede attachi o attacchi speciali 
    GRANTS_QUALITY = "grants_quality" # concede qualità speciali 
    GRANTS_PROFICIENCY = "grants_proficiency" # concede competenza in qualcosa
    GRANTS_ITEM = "grants_item"    # concede un oggetto o ne simula il possesso
    GRANTS_CREATURE = "grants_creature" # concede una o più creature (autorità, ottenere famiglio)
    GENERIC = "generic"           # generico 
    PSIONIC = "psionic"           # psionico
    CLASS_RELATED = "class_related" # relativo a una classe * o di classe

# =====================
# CHARACTER CLASS
# =====================
class ProgressionRate(str, Enum):
    LOW = "low"        # +10 max -> esempio mago (1/2 liv)
    MEDIUM = "medium"  # +15 max -> esempio chierco  (3/4 liv)
    HIGH = "high"      # +20 max -> esempio guerriero (= liv)

class SaveProgression(str, Enum):
    POOR = "poor"   # basso
    GOOD = "good"   # alto

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