"""
Raw field representations for D&D 3.x spells and cleric domains.

This module mirrors spell entries and cleric domain definitions as they
appear in D&D 3.x sources, preserving their original format instead of
converting them into structured domain types.

It represents the intermediate raw_fields layer described in
PIPELINE_ARCHITECTURE.md: extracted data is normalized into stable Python
structures here, while type casting and semantic interpretation happen
later during the structured_data conversion stage.

Complex tables and rule interactions (e.g. 'permanency', 'polymorph any object' rules)
are not explicitly modeled and are kept within the spell description.
"""
from dataclasses import dataclass, field

# =====================
# SPELL
# =====================
@dataclass(kw_only=True)
class SpellLevel:
    """
    Represents a spell level entry for a specific character class.
    e.g Clr 1, Pal 3, Sor/Wiz 7
    """
    character_class: str
    level: str

@dataclass(kw_only=True)
class SummonedCreature:
    """Represents a creature that can be summoned by a spell."""
    creature_name: str
    creature_description: str | None = None

@dataclass(kw_only=True)
class Spell:
    """Represents a spell entry extracted from a D&D 3.x source."""
    name: str
    # Description
    school: str
    subschool: str | None = None
    descriptor: list[str] = field(default_factory=list) 
    # Level
    level: list[SpellLevel]

    # NOTE:
    # Spell components (e.g. V, S, M) are not mapped as they are not
    # relevant for the current game system.

    # Casting Time
    casting_time: str  | None = None
    # Range
    spell_range: str | None = None
    # Targets
    targets: str | None = None
    # Area
    spell_area: str | None = None
    # Effect
    spell_effect: str | None = None
    # Duration
    duration: str
    # Saving Throw
    saving_throw: str | None = None
    # Spell Resistance
    spell_resistance: str | None = None
    # Description
    description: str 

    # Dispels 
    dispels_usage: str | None = None
    # NOTE:
    # This field is intentionally extracted to simplify later transformation
    # stages (structured_data and domain models). Dispel-related interactions
    # are often embedded in the spell description and can be difficult to
    # reconstruct reliably after parsing, so they are captured here explicitly
    # despite not being a standard structured field in the source.
     
    # Summoning
    summoned_creatures: list[SummonedCreature]  = field(default_factory=list)
    # NOTE:
    # If the spell includes a list of summonable creatures, they are
    # represented explicitly in this field.

    # NOTE:
    # Spells with complex tables (e.g. 'permanency', 'polymorph any object')
    # are not fully mapped and are instead preserved in the description.

# =====================
# CLERIC DOMAIN
# =====================
@dataclass(kw_only=True)
class DomainGrantedSpell:
    """Represents a spell granted by a cleric domain."""
    level: str
    name: str
    description: str | None = None
    extra_description: str | None = None # e.g *Cast as an air spell only. 


@dataclass(kw_only=True)
class ClericDomain:
    """Represents a cleric domain entry extracted from a D&D 3.x source."""
    name: str
    # Granted Powers
    granted_powers: list[str] = field(default_factory=list)
    # Granted Spells
    granted_spells: list[DomainGrantedSpell]
    