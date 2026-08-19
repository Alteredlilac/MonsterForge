"""
Static mappings used to calculate MonsterForge interpretation values
from D&D 3.x character skills.

This module defines the relationships between source-system skills,
interpretation groups, and reference ability scores.

It does not perform calculations; it only provides the static
conversion rules consumed by the transformation layer.
"""
# NOTE:
# These tables represent game rules and are intentionally immutable.
# They should not be modified during runtime.
from typing import Mapping
from types import MappingProxyType

# =====================
# SKILL GROUP MAPPING
# =====================

# Maps D&D 3.x skills to MonsterForge interpretation groups.
#
# Used during the transformation stage to aggregate source skills
# into the six domain-level interpretation values.
#
# Multiple D&D skills contribute to the same interpretation group,
# whose final value is calculated as the average of the associated
# skill values.
# SKILL_TO_INTERPRETATION_MAPPING   input → output
SKILL_TO_INTERPRETATION_MAPPING: Mapping[str, list[str]] = MappingProxyType({
    "athletics": [
        "tumble",
        "escape_artist",
        "ride",
        "balance",
        "swim",
        "jump",
        "climb",
        "stabilize_self",  # v3.0 psionic
    ],
    "empathy": [
        "animal_empathy",       # v3.0
        "handle_animal",
        "diplomacy",
        "intimidate",
        "perform",              # *
        "sense_motive",
        "gather_information",
        "bluff",
    ],
    "perception": [
        "intuit_direction", # v3.0
        "listen",
        "search",
        "scry",             # v3.0
        "spot",
        "read_lips",        # v3.0
        "remote_view",      # v3.0 psionic
    ],
    "stealth": [
        "disguise",
        "move_silently",
        "hide",
        "innuendo",        # v3.0
        "sleight_of_hand",
        "pick_pocket",     # v3.0
    ],
    "knowledge": [
        "concentration",
        "autohypnosis",
        "knowledge",       # *
        "decipher_script",
        "heal",
        "profession",      # *
        "spellcraft",
        "psicraft",
        "survival",
        "appraise",
    ],
    "crafting": [
        "alchemy",            # v3.0
        "craft",              # *
        "disable_device",
        "forgery",
        "open_lock",
        "use_rope",
        "use_magic_device",
        "use_psionic_device",
    ],
})


# =====================
# REFERENCE ABILITY MAPPING
# =====================
# Defines the reference D&D ability score associated with each
# MonsterForge interpretation group.
#
# The reference ability is used during interpretation calculation
# to determine the base value and validate negative modifiers.
INTERPRETATION_TO_ABILITY_MAPPING: Mapping[str, str] = MappingProxyType({
    "athletics": "strength",
    "empathy": "charisma", 
    "perception": "wisdom",
    "stealth": "dexterity" ,
    "knowledge": "intelligence",
    "crafting": "intelligence",
})
