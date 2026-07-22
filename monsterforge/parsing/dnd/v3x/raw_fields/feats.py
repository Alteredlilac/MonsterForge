"""
Raw field representations for D&D 3.x feats.

This module mirrors feat entries as they appear in the rulebook, keeping
their original sections (Prerequisite, Benefit, Normal, Special) as
source-formatted strings rather than interpreted domain data.

This is part of the intermediate "raw fields" layer described in
PIPELINE_ARCHITECTURE.md: it decouples source extraction from semantic
classification and allows different sources to converge on the same
structure before conversion into structured_data.

Complex feat-specific structures, such as additional tables or progression
systems granted by feats (e.g. Improved Familiar, Leadership, or Track),
are intentionally not mapped, as they are not required by the current
card-based game system.
"""
from dataclasses import dataclass

# =====================
# FEAT
# =====================
@dataclass(kw_only=True)
class Feat:
    """
    Represents a single feat entry extracted from a D&D 3.x source.

    The model preserves the original feat sections without interpreting
    their semantic effects.
    """
    name: str
    feat_type: str 
    description: str | None = None
    prerequisite: str | None = None
    benefit: str | None = None 
    # NOTE:
    # Benefit is present in most feat entries, but due to the large number of
    # supplements, some specific feats may define their effects directly in the
    # description field instead.
    normal: str  | None = None
    special: str | None = None
