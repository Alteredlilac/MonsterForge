"""
Raw field representations for D&D 3.x creature attack entries.

This module mirrors the "Attack" and "Full Attack" sections of creature
stat blocks as closely as possible to their rulebook representation,
keeping values as source-formatted strings rather than interpreted or
normalized data.

Composite attack expressions (e.g. "bite +5 ... or web +5 ...") are
assumed to be split into atomic entries during parsing. Each Attack
instance represents a single such atomic unit.

This is part of the intermediate "raw fields" layer described in
PIPELINE_ARCHITECTURE.md: it decouples text extraction from semantic
interpretation, allowing consistent downstream processing regardless of
source formatting differences.

The attack_effect field is intentionally flexible: it may contain damage,
critical information, or additional effects (e.g. poison, trip), and may
also include details extracted from other parts of the stat block when
not explicitly defined inline (e.g. web attacks).
"""
from dataclasses import dataclass

# =====================
# ATTACK
# =====================
@dataclass(kw_only=True)
class Attack:
    """
    Represents a single atomic attack entry already split from composite
    expressions such as "claw +8 ... and bite +3 ..."
    """
    name: str     # e.g. "Shortbow"
    modifier: str # e.g. "+8"
    attack_type: str # e.g. "ranged" 
    attack_effect: str  # raw effect/damage portion, including extracted or referenced effects


# =====================
# FULL ATTACK
# =====================
@dataclass(kw_only=True)
class FullAttack:
    """
    Represents the "Full Attack" entry of a creature, composed of multiple
    attack entries performed in a full-round action.
    """
    attacks: list[Attack]
