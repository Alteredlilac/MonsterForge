"""
Provides structured data models for D&D 3.x feats.

Includes feat definitions, prerequisite requirements, and
feat-granted effects such as modifiers, attacks, qualities,
and granted content.

The module focuses on feat data required by the card-based game
system while keeping complex or supplement-specific requirements
flexible.
"""
from dataclasses import dataclass, field
from .enums import SavingThrowType
from .creature_stats import Abilities
from .skills import Skills
from .enums import FeatCategory
from .effect_mechanics import EffectModifier, EffectGrant
from .special_attacks import SpecialAttack
from .special_qualities import SpecialQuality

# =====================
# HELPER
# =====================
@dataclass(kw_only=True)
class SaveRequirement:
    save_type: SavingThrowType
    minimum_value: int

@dataclass(kw_only=True)
class FeatRequirement:
    """
    Represents a single requirement needed to acquire a feat.
    """
    # NOTE:
    # Feat, class feature, proficiency, and specific class requirements are
    # kept as strings to maintain flexibility across different supplements.
    ability: Abilities | None = None    # caratteristica
    saving_throw: list[SaveRequirement] = field(default_factory=list)
    skill: Skills | None = None         # abilità
    feat: str | None = None   
    character_class_feature: str | None = None # qualità di classe richiesta
    base_attack_bonus: int | None = None
    proficiency: str | None = None  # competenza  
    minimum_level: int | None = None
    required_character_class: str | None = None  # classe specifica richiesta
    spellcasting: bool = False # se richiesto True (richiede di essere incantatori?)
    psionics: bool = False # se richiesto True (richiede capacità psioniche?)
    minimum_spell_level: int | None = None
    minimum_manifester_level: int | None = None
    description: str 
    # NOTE:
    # Description is used for requirements not covered by explicit fields,
    # such as movement methods, special qualities, race requirements, or
    # other uncommon prerequisites, avoiding excessive specialization of
    # the model with rarely used attributes.

# =====================
# FEATS
# =====================
@dataclass(kw_only=True)
class Feat:
    """
    Represents a D&D 3.x feat with prerequisites and effects granted
    to the associated entity.
    """
    name: str
    description: str
    categories: list[FeatCategory] = field(default_factory=list)  # un talento può appartenere a più categorie
    requirements: list[FeatRequirement] = field(default_factory=list)

    # Optional behavioral components, presence coerente con la/le categorie dichiarate
    granted_modifiers: list[EffectModifier] = field(default_factory=list)
    
    granted_attacks: list[SpecialAttack] = field(default_factory=list)
    granted_qualities: list[SpecialQuality] = field(default_factory=list)

    # NOTE:
    # For the card-based game system, metamagic and metapsionic effects are
    # intentionally represented as strings, as a structured model is not required.

    metamagic_effect: str | None = None
    metamagic_level_adjustment: int | None = None  # spell level adjustment

    metapsionic_effect: str | None = None
    metapsionic_power_point_adjustment: int | None = None  # power point cost adjustment

    # guadagna carte?
    grants: list[EffectGrant] = field(default_factory=list) # creatura, oggetto, effetto
