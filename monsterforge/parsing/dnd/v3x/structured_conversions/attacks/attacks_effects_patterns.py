"""
Regular-expression patterns used to parse D&D 3.x attack-effect fields.

This module defines the deterministic regular-expression patterns used by
the attack-effects parser to recognize the syntactic components contained in
raw D&D 3.x "attack_effect" values.

The patterns include:

- standard dice expressions and their numeric modifiers
- critical-threat ranges and critical multipliers
- fixed typed damage values
- typed dice damage expressions
- ability-related damage or drain effects

This module contains only pattern definitions. The interpretation of matched
values and their conversion into structured "Damage", "CriticalHit", or
other effect objects is performed by the attack-effects parser and its
helper functions.
"""
import re

# =====================
# DICE PATTERN
# =====================

# Examples:
#   1d6
#   2d8+4
#   1d4-2
DICE_PATTERN = re.compile(
    r"(?P<number>\d+)"
    r"d"
    r"(?P<type>\d+)"
    r"(?P<bonus>[+-]\d+)?",
    re.IGNORECASE,
)


# =====================
# CRITICAL THRESHOLD PATTERN
# =====================
# Examples:
#   /19-20
#   /18-20
CRITICAL_THRESHOLD_PATTERN = re.compile(
    r"/(?P<threshold>\d+)-20",
)

# Examples:
#   /×3
#   /x3
CRITICAL_MULTIPLIER_PATTERN = re.compile(
    r"/(?:×|x)(?P<multiplier>\d+)",
    re.IGNORECASE,
)

# =====================
# FIXED DAMAGE PATTERN
# =====================
# Fixed typed damage:
#   1 fire
#   2 acid
#   1 positive energy
FIXED_TYPED_DAMAGE_PATTERN = re.compile(
    r"^(?P<number>\d+)\s+(?P<type>[a-z ]+)$",
    re.IGNORECASE,
)


# =====================
# TYPED DICE PATTERN
# =====================
# Typed dice damage:
#   1d8 fire
#   2d6 acid
TYPED_DICE_PATTERN = re.compile(
    r"^(?P<dice>\d+d\d+(?:[+-]\d+)?)\s+"
    r"(?P<type>[a-z ]+)$",
    re.IGNORECASE,
)


# =====================
# ABILITY EFFECT PATTERN
# =====================
# Ability effects:
#   Wisdom drain
#   Strength drain
#   1d6 Str
ABILITY_PATTERN = re.compile(
    r"\b("
    r"strength|str|"
    r"dexterity|dex|"
    r"constitution|con|"
    r"intelligence|int|"
    r"wisdom|wis|"
    r"charisma|cha"
    r")\b",
    re.IGNORECASE,
)
