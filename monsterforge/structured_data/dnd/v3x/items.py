"""
Provides structured data models for D&D 3.x items.

Includes base items, magic and psionic items, artifacts,
and intelligent items with supernatural properties.

The module focuses on item data required by the card-based game
system, while leaving unsupported or lore-specific details
unmapped.
"""
from dataclasses import dataclass, field
from .enums import ItemType, ItemPowerType, IntelligentItemType
from .dice_effects import Damage, Healing
from .special_attacks import SpecialAttack
from .special_qualities import SpecialQuality
from .effect_mechanics import EffectModifier, EffectGrant, CriticalHit, EffectRange
from .defenses import DamageReduction

@dataclass(kw_only=True)
class Item:
    name: str | None = None 
    description: str | None = None 
    price: float | None = None    # espresso in monete d'oro 
    weight: float | None = None 

    item_type: ItemType # arma, armatura, generico, strumento, alchemico, vestito, accessorio 
    # NOTE:
    # Class-specific items are classified as tools if they provide bonuses
    # or mechanical benefits, otherwise they are classified as generic items.
    # Examples: spellbook = generic item, alchemist's lab = tool.
    # Magical symbols are classified as accessories.

    item_material_name: str | None = None  
    item_material_properties: str | None = None
    # NOTE:
    # Item materials are not mapped as structured data, as the number of
    # possible materials across D&D supplements is too large.
    # A free-text description is used instead to maintain flexibility. 

    is_consumable: bool = False  # true if the item is destroyed/used up after activation

    # NOTE:
    # Item capacity is intentionally not mapped, as it is not required by the
    # card-based game system.

    # arma
    melee: bool = False      #utilizzabile per attaccare in mischia 
    touch: bool = False     # attacco di contatto
    # Range
    attack_range: EffectRange | None = None
    # Damages
    damages: list[Damage] = field(default_factory=list) # elenco dei danni dell'attacco
    # Critical Hit    
    critical_hit: CriticalHit | None = None   
    # Effects
    attack_effects: list[SpecialAttack] = field(default_factory=list)

    # armatura 
    # riduzione del danno
    damage_reduction: DamageReduction | None = None
    # bonus / malus
    modifiers: list[EffectModifier] = field(default_factory=list) # bonus concessi dall'oggetto
    max_speed: int | None = None # speed limit imposed by the item when worn or carried
     

@dataclass(kw_only=True)
class MagicItem(Item):
    """
    Represents a magic, psionic, or artifact item with supernatural properties.
    """
    # NOTE:
    # Grafts are not modeled as items, but as CreatureModifier instances,
    # as they represent modifications applied to creatures rather than
    # independent objects.

    magic_type: ItemPowerType # magic items, psionic items  
    is_artifact: bool = False
    is_cursed: bool = False

    charges: int | None = None  # cariche dell'oggetto, esempio bacchetta = 50 cariche

    defense_effects: list[SpecialQuality] = field(default_factory=list)
    # Healing
    healing_effects: list[Healing] # elenco delle cure dell'oggetto
    
    # guadagna carte?
    grants: list[EffectGrant] = field(default_factory=list) # creatura, oggetto, effetto



@dataclass
class IntelligentItem(MagicItem):
    """
    Represents a magic item with its own intelligence, personality,
    or supernatural entity.
    """
    intelligent_type: IntelligentItemType # intelligente, simbionte, posseduto
    # NOTE:
    # Symbionts are intentionally mapped as items rather than creatures,
    # as the card-based game system represents them as item cards.
    intelligence: int
    wisdom: int
    charisma: int

    # NOTE:
    # Item perception and communication methods are intentionally not mapped,
    # as they are not required by this domain model.    



# NOTE:
# Vehicles are intentionally not mapped, as they are not supported by the
# current card-based game system.
# They could be represented as creatures in the future by allowing None
# values for Wisdom and Charisma in the Creature model.