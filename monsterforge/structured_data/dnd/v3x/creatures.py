"""
Creature data structures for D&D 3.x stat blocks.

This module defines the structured representation of creatures, including
monsters, playable races, and creature modifications such as templates.

Creature modifiers represent changes applied to an existing creature and do
not represent complete stat blocks on their own.

This module only defines data contracts. Rules for combining creatures,
applying modifiers, and resolving derived values are handled separately.
"""
from dataclasses import dataclass, field
from .enums import (
    CreatureType,
    CreatureSubtype,
    Size,
    Alignment,
    )
from .creature_stats import (
    HitDice,
    Movement,
    MovementMode,
    ArmorClass,
    Space,
    Reach,
    Abilities,
    Saves,
)
from .attacks import Attack, FullAttack
from .special_attacks import SpecialAttack
from .special_qualities import SpecialQuality
from .skills import Skills
from .feats import Feat
from .items import Item
from .spells import Spellcasting
from .psionic_powers import Psionics
import uuid

# =====================
# CREATURE 
# =====================
@dataclass(kw_only=True)
class Creature:
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Creature data
    name: str    
    creature_type: CreatureType 
    creature_subtype: list[CreatureSubtype] = field(default_factory=list)
    creature_size: Size
    # Creature Description
    description: str
    # Life
    hit_dice: list[HitDice] = field(default_factory=list)
    hit_points_total: int  # total hit point
    hit_point_bonus: int   # additional hit point modifier from hit dice expression
    # Initiative
    initiative: int
    # Movements
    speed: list[Movement] = field(default_factory=list) 
    # Armor Class
    armor_class: ArmorClass    
    # Resistances
    spell_resistance: int | None = None
    power_resistance: int | None = None
    # Base Attack / Grapple
    base_attack: int # attacco base
    grapple: int     # lotta
    # Attacks
    attacks: list[Attack] = field(default_factory=list) 
    full_attack: FullAttack | None = None # None = scelta di design per robustezza
    # Threatened Area  
    space: Space
    reach: Reach
    # Special Attacks
    special_attacks: list[SpecialAttack] = field(default_factory=list)
    # Special Qualities
    special_qualities: list[SpecialQuality] = field(default_factory=list)
    # Magic
    # A creature may have multiple spellcasting progressions (e.g. multiclass creatures).
    spellcasting: list[Spellcasting] = field(default_factory=list)
    # Psionics
    psionics: Psionics | None = None
    # Saves -> tiri salvezza
    saves: Saves
    # Abilities -> caratteristiche
    abilities: Abilities 
    # Skills -> abilità 
    skills: Skills    
    # Feats -> Talenti
    feats: list[Feat] = field(default_factory=list)  
    # Equipment
    equip: list[Item] = field(default_factory=list) 
    # Environment
    environments: list[str] = field(default_factory=list)
    # NOTE:
    # Environments are intentionally kept as generic strings instead of enums.
    # The list of valid environments can vary between settings and supplements,
    # so restricting values to a predefined enum would reduce flexibility.
    # Organization
    # NOTE:
    # Organization is intentionally excluded because it describes encounter
    # composition rather than creature data. It is out of scope for this
    # card-based game system.
    challenge_rating: str # grado sfida esistono 1/2, 1/3, 1/4, eccetera gestito come str
    # NOTE:
    # Treasure is intentionally excluded because it represents loot generation
    # rather than intrinsic creature data, and is out of scope for this project.
    alignment: Alignment  # allineamento
    # NOTE:
    # Advancement and Level Adjustment are intentionally excluded because they
    # describe progression rules rather than intrinsic creature data, and are
    # out of scope for this project.
    
# =====================
# CreatureModifier
# =====================
@dataclass(kw_only=True)
class CreatureModifier:
    """
    Represents a creature modification such as an acquired template
    (e.g. lycanthropy, vampirism, lichdom) or a base race variant.

    Unlike Creature, this does not describe a complete stat block —
    only the deltas to apply on top of a base Creature.
    """
    # NOTE:
    # Overrides (sostituiscono il valore della creatura base, se presenti)
    # Additive (si sommano a quanto già presente nella creatura base)
    # Modifiers (bonus/penalità da applicare)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # Creature Data
    name: str                        # "Licantropia", "Vampirismo"
    type_override: CreatureType | None = None 
    added_subtypes: list[CreatureSubtype] = field(default_factory=list)
    size_override: Size | None = None
    # Creature Description
    added_description: str # va aggiunta alla descrizione base
    # Life
    added_hit_dice: list[HitDice] = field(default_factory=list)
    added_hit_point_bonus: int | None = None   # additional hit point modifier
    # Initiative
    initiative_modifier: int | None = None # bonus all'iniziativa
    # Movements
    added_speed: list[Movement] = field(default_factory=list)  # nuove modalità di movimento (es. Vampirismo aggiunge "volare 18m")
    speed_bonus: dict[MovementMode, int] = field(default_factory=dict)  # bonus a modalità già esistenti, es. {LAND: 3}
    # Armor Class
    armor_class_modifier: ArmorClass | None = None # bonus alla classe armatura
    armor_class_override: ArmorClass | None = None # nuovi valori da sovrascrivere    
    # Resistances
    spell_resistance_base: int | None = None  # base esempio 10, 11
    spell_resistance_per_level: int | None = None # progressione per livello
    power_resistance_base: int | None = None # base esempio 10, 11
    power_resistance_per_level: int | None = None # progressione per livello
    # Base attack bonus
    added_base_attack: int | None = None
    # Attacks
    added_attacks: list[Attack] = field(default_factory=list)     
    # Threatened Area 
    space_override: Space | None = None
    reach_override: Reach | None = None
    # Special Attacks
    added_special_attacks: list[SpecialAttack] = field(default_factory=list)
    # Special Qualities
    added_special_qualities: list[SpecialQuality] = field(default_factory=list)
    # Magic
    # A CreatureModifier can add only one spellcasting progression.
    added_spellcasting: Spellcasting  | None = None  
    # Psionics
    added_psionics: Psionics | None = None
    # Saves -> tiri salvezza
    saves_modifier: Saves | None = None
    # Abilities -> caratteristiche
    ability_modifiers: dict[str, int] = field(default_factory=dict)
    # Skills -> abilità 
    skills_modifiers: Skills  | None = None  
    # Feats -> Talenti
    added_feats: list[Feat] = field(default_factory=list)
    # Equipment
    # Some CreatureModifiers can add additional equipment to the base creature.
    # This represents equipment granted by the modifier itself (e.g. a lich's phylactery).
    added_equip: list[Item] = field(default_factory=list) 
    # Environment
    environments: list[str] = field(default_factory=list)
    # Challenge Rating
    challenge_rating_modifier: str | None = None 
    # Alignment
    alignment_override: Alignment | None = None
    