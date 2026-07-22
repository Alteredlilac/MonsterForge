"""
Raw field representations for D&D 3.x creature stat blocks.

This module mirrors creature entries as they appear in D&D 3.x sources,
keeping values in their source format rather than converting them into
structured domain types.

It represents the intermediate raw_fields layer described in
PIPELINE_ARCHITECTURE.md: extracted data is normalized into stable Python
structures here, while type casting and semantic interpretation happen
later during the structured_data conversion stage.

Creature fields intentionally exclude encounter and progression-related data
such as organization, treasure, advancement, and level adjustment, as they
do not represent intrinsic creature properties and are not required by the
current card-based game system.
"""
from dataclasses import dataclass, field
from .feats import Feat
from .attacks import Attack, FullAttack

# =====================
# Movement
# =====================
@dataclass(kw_only=True)
class Movement:
    """
    Represents a single movement method extracted from a creature stat block.
    """
    name: str | None = None  # Ground movement has no explicit name.
    description: str | None = None


# =====================
# SPECIAL ABILITIES
# =====================
@dataclass(kw_only=True)
class SpecialAbility:
    """
    Base class for special attack and special quality entries.

    This class is not instantiated directly; only its subclasses represent
    extracted entries from creature stat blocks.
    """
    name: str
    type_description: str | None = None
    description: str | None = None

@dataclass(kw_only=True)
class SpecialAttack(SpecialAbility):
    """
    Represents a special attack entry extracted from a creature stat block.
    """
    pass

@dataclass(kw_only=True)
class SpecialQuality(SpecialAbility):
    """
    Represents a special quality entry extracted from a creature stat block.
    """
    pass

# =====================
# SAVES
# =====================
@dataclass(kw_only=True)
class Saves:
    """
    Represents the saving throws section of a creature stat block.
    """
    fortitude_save: str | None = None
    reflex_save: str | None = None
    will_save: str | None = None
    description: str | None = None
    # NOTE:
    # Description is used for uncommon cases that cannot be represented by
    # explicit fields, such as "as master's saves". In these cases, individual
    # saving throw values may remain undefined.

# =====================
# ABILITIES
# =====================
@dataclass(kw_only=True)
class Abilities:
    """
    Represents the ability scores section of a creature stat block.
    """
    # NOTE:
    # Some ability scores may be undefined ("-") in D&D 3.5 stat blocks.
    # Strength may be absent ("-") for creatures without a physical body (e.g. spectres). 
    # Dexterity may be absent ("-") for immobile creatures (e.g. certain plants or fungi).
    # Constitution is omitted for creatures without a living body (undead,
    # constructs), while Intelligence is omitted for mindless creatures.
    # Wisdom and Charisma may also be undefined in raw data when the source
    # does not provide explicit values.
    strength: str | None = None     
    dexterity: str | None = None    
    constitution: str | None = None 
    intelligence: str | None = None 
    wisdom: str | None = None       
    charisma: str | None = None     

# =====================
# SKILL
# =====================
@dataclass(kw_only=True)
class Skill:
    """
    Represents a single skill entry extracted from a creature stat block.
    """
    name: str
    modifier: str


# =====================
# CREATURE
# =====================
@dataclass(kw_only=True)
class Creature:
    """
    Represents a raw creature stat block entry extracted from a D&D 3.x source.
    """
    # Data
    name: str
    description: str | None = None
    # size and type
    size: str  
    type: str 
    subtype: list[str] = field(default_factory=list)
    # Life
    hit_dice: str  # Hit dice value as written in the source (e.g. "2d8+6").
    total_life: str  # Total hit points as written in the source (e.g. "34 hp").
    # Initiative
    initiative: str
    # Speed
    speed: list[Movement] = field(default_factory=list)  
    # Armor Class
    armor_class: str
    touch: str 
    flat_footed : str 
    # Base Attack / Grapple
    base_attack: str
    grapple: str
    # Attacks
    attack: Attack | None = None
    full_attack: FullAttack | None = None
    # Space / Reach
    space: str
    reach: str
    # Special Abilities
    special_attacks: list[SpecialAttack] = field(default_factory=list)
    special_qualities: list[SpecialQuality] = field(default_factory=list)
    # Saves
    saves: Saves 
    # Abilities
    abilities: Abilities 
    # Skills
    skills: list[Skill] = field(default_factory=list) 
    # Feats
    feats: list[Feat] = field(default_factory=list) 
    # Environment
    environment: str
    # NOTE:
    # Organization is intentionally excluded because it describes encounter
    # composition rather than creature data. It is out of scope for this
    # card-based game system.
    challenge_rating: str
    # NOTE:
    # Treasure is intentionally excluded because it represents loot generation
    # rather than intrinsic creature data, and is out of scope for this project.
    alignment: str
    # NOTE:
    # Advancement and Level Adjustment are intentionally excluded because they
    # describe progression rules rather than intrinsic creature data, and are
    # out of scope for this project.
