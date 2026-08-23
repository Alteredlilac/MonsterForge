"""
Defines the states of the human-in-the-loop review process for LLM
semantic classifications.

Unlike domain/enums.py, these values describe a step in the pipeline's
own review workflow, not a game concept — they belong here rather than
in domain/ for the same reason rules/ and transformation/ stay separate:
different packages own different kinds of information.
"""
from enum import Enum


# =====================
# VALIDATION STATUS
# =====================
class ValidationStatus(str, Enum):
    AUTO_APPROVED = "auto_approved"  # confidence above threshold, no review shown
    APPROVED = "approved"            # review shown, human confirmed without changes
    CORRECTED = "corrected"          # review shown, human edited via the review form
    REJECTED = "rejected"            # human discarded the classification, no card produced
