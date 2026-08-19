"""
Structured data models for D&D 3.x character classes.

Defines base character classes, prestige classes, and class privileges,
including progression data, saving throw profiles, spellcasting progression,
and requirements needed to access prestige classes.
"""
from dataclasses import dataclass, field
from .enums import (
ProgressionRate,
SaveProgression,
ClassPrivilegeType,
Alignment,
CreatureType,
CreatureSubtype,
DiceType, 
SavingThrowType
)
from .special_attacks import SpecialAttack
from .special_qualities import SpecialQuality
from .feats import Feat
from .attacks import Attack, FullAttack
from .companions import Companion
from .cleric_domains import ClericDomain
from .items import Item
from .psionic_powers import Power, Manifester
from .spells import Spell, Spellcaster
from .creatures import CreatureModifier
from .skills import Skills
from .creature_stats import Abilities, ArmorClass, Saves, Movement
import uuid

# =====================
# HELPER
# =====================
@dataclass(kw_only=True)
class SaveRequirement:
    save_type: SavingThrowType
    minimum_value: int

# =====================
# PRIVILEGES
# =====================
GrantedContent = (
    Attack | FullAttack | SpecialAttack | SpecialQuality | Feat |
    Companion | ClericDomain | Item | Power | Spell | Spellcaster | Manifester |
    CreatureModifier
)
# NOTE:
# A privilege can grant heterogeneous content (attacks, feats, items, etc.),
# so a broad union type is used.
@dataclass(kw_only=True)
class ClassPrivilege:
    """
    Represents a single class privilege granted by a character class.
    """
    name : str
    granted_at_level: int 
    description: str
    privilege_type: ClassPrivilegeType 
    granted_privilege: GrantedContent


# =====================
# CHARACTER CLASS
# =====================
@dataclass(kw_only=True)
class CharacterClass:
    """
    Represents a D&D 3.x character class and its progression.
    """
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    name: str 
    description: str

    hit_die: DiceType

    # NOTE:
    # Class skills are intentionally not mapped: in the card-based game
    # system, skill values are assigned as a fixed number per level
    # regardless of character class, and there is no concept of
    # class-restricted or unavailable skills.

    total_levels: int # total number of class levels, e.g. 5, 10, 20

    base_attack_bonus: ProgressionRate | None = None # low, medium, high — None covers edge cases, mirroring spellcasting progression below

    fortitude_save: SaveProgression # high or low
    reflex_save: SaveProgression # high or low
    will_save: SaveProgression # high or low

    privileges: dict[int, list[ClassPrivilege]] = field(default_factory=dict) # key = level, value = list of privileges granted at that level
    # NOTE:
    # Spellcasting data is intentionally simplified.
    # Spell slots and known spells are not mapped at class level.
    max_spell_level: int | None = None # up to 4 = low, up to 7 = medium, up to 9 = high
    
    @property
    def spellcasting_progression(self) -> ProgressionRate | None:
        # NOTE:
        # Domain-specific term equivalent to base attack bonus progression.
        # Not an original D&D concept.

        if self.max_spell_level is None:
            return None

        if self.max_spell_level <= 4:
            return ProgressionRate.LOW
        elif self.max_spell_level <= 7:
            return ProgressionRate.MEDIUM
        elif self.max_spell_level <= 9:
            return ProgressionRate.HIGH

        return None

# =====================
# PRESTIGE CLASSES
# =====================
@dataclass(kw_only=True)
class PrestigeClass(CharacterClass):
    """
    Represents a D&D 3.x prestige class with prerequisites required
    for character entry, including skill, ability, feat, combat,
    spellcasting, creature, alignment, and special requirements.
    """
    required_skills: Skills | None = None
    required_abilities : Abilities | None = None
    required_armor_class: ArmorClass | None = None
    required_movement: list[Movement] = field(default_factory=list)
    required_creature_type: CreatureType | None = None
    required_creature_subtype: list[CreatureSubtype] = field(default_factory=list)
    required_race: str | None = None # e.g. "elf"
    required_attack_bonus: int | None = None
    required_feats: list[Feat] = field(default_factory=list)
    required_spells: list[Spell] = field(default_factory=list)
    required_saves: list[SaveRequirement] = field(default_factory=list)
    required_caster_level: int | None = None
    required_items: list[Item] = field(default_factory=list)
    required_alignment: list[Alignment] = field(default_factory=list)
    required_special: str | None = None # special options, handled as free text
