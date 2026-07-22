"""
Raw field representations for D&D 3.x psionic powers.

This module mirrors psionic power entries as they appear in D&D 3.x
sources, preserving their original format instead of converting them into
structured domain types.

It represents the intermediate raw_fields layer described in
PIPELINE_ARCHITECTURE.md: extracted data is normalized into stable Python
structures here, while type casting and semantic interpretation happen
later during the structured_data conversion stage.

Complex psionic rules and interactions (e.g. power-specific tables)
are not explicitly modeled and remain preserved within the power
description when part of the source text.

Psionic features not required by the card-based game system,
such as power points, XP costs, and augmentation rules, are
intentionally excluded from the model.
"""
from dataclasses import dataclass, field

# =====================
# PSIONIC POWER
# =====================
@dataclass(kw_only=True)
class PowerLevel:
    """
    Represents a power level entry for a specific character class.
    e.g. Psion/wilder 5, psychic warrior 3
    """
    character_class: str
    level: str

@dataclass(kw_only=True)
class PsionicSummonedCreature:
    """Represents a creature that can be summoned by a psionic power."""
    creature_name: str
    creature_description: str | None = None

@dataclass(kw_only=True)
class PsionicPower:
    """Represents a psionic power entry extracted from a D&D 3.x source."""
    name: str
    # Description
    discipline: str
    subdiscipline: str | None = None
    descriptor: list[str] = field(default_factory=list) 
    # Level
    level: list[PowerLevel]

    # NOTE:
    # Display manifestations (e.g. auditory, material) are not mapped,
    # as they are not relevant for the current game system.

    # Manifesting Time
    manifesting_time: str  | None = None
    # Range
    power_range: str | None = None
    # Targets
    targets: str | None = None
    # Area
    power_area: str | None = None
    # Effect
    power_effect: str | None = None
    # Duration
    duration: str
    # Saving Throw
    saving_throw: str | None = None
    # Power Resistance
    power_resistance: str | None = None
    # Description
    description: str 

    # NOTE:
    # Power Points and XP Cost are not mapped as they are not
    # relevant for the current game system.

    # NOTE: 
    # Augment descriptions are not mapped as they are not
    # relevant for the current game system.

    # Dispels 
    dispels_usage: str | None = None
    # NOTE:
    # This field is intentionally extracted to simplify later transformation
    # stages (structured_data and domain models). Dispel-related interactions
    # are often embedded in the power description and can be difficult to
    # reconstruct reliably after parsing, so they are captured here explicitly
    # despite not being a standard structured field in the source.
     
    # Summoning
    summoned_creatures: list[PsionicSummonedCreature]  = field(default_factory=list)
    # NOTE:
    # If the power includes a list of summonable creatures, they are
    # represented explicitly in this field e.g. 'Astral Construct'

    # NOTE:
    # Powers with complex tables are not fully mapped and are instead
    # preserved within the power description.
