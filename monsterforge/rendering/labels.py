"""
Static presentation strings for rendering/: field labels and per-move-type
accent colors.

These are pure display language, not D&D game rules or domain concepts —
the field labels never vary from one MoveCard to another, and the color
mapping is purely visual (purple/blue for magical, salmon/red for
physical, per the reference mockups in monsterforge/docs/images/). Most
of the card's dynamic text does not need a translation table at all: the
domain enums involved (MoveCategory, MoveType, Resource, MoveRange,
DamageType) are already (str, Enum) with English values, so the template
renders them directly via .value.upper() instead of looking them up here.

This module lives in rendering/ rather than rules/dnd/v3x/ because it is
source-agnostic presentation, not a D&D-specific rule table — same
reasoning that keeps domain/ free of the <system>/<version> nesting
(see NAMING_CONVENTIONS.md §2).
"""

from types import MappingProxyType
from typing import Mapping

from monsterforge.domain.enums import MoveType

# =====================
# FIELD LABELS
# =====================
FIELD_LABELS: Mapping[str, str] = MappingProxyType({
    "name": "NAME",
    "category": "CATEGORY",
    "type": "TYPE",
    "image": "IMAGE",
    "range": "RANGE",
    "effect": "EFFECT",
    "bonus_cards": "BONUS CARDS",
    "description": "DESCRIPTION",
    "id": "ID",
})

# =====================
# MOVE TYPE ACCENT COLORS
# =====================
MOVE_TYPE_TO_COLOR_MAPPING: Mapping[MoveType, str] = MappingProxyType({
    MoveType.PHYSICAL: "#c17f68",  # salmon/terracotta accent
    MoveType.MAGICAL: "#8f8fc2",   # purple/blue accent
})
