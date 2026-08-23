"""
Configuration for the human-in-the-loop review gate (validation/review.py).

Plain module-level constants, not a rules/ table: these are runtime
tuning knobs for the review process itself, not static game data.
"""

CONFIDENCE_THRESHOLD: float = 0.7

# NOTE:
# When True, every classification goes through human review regardless
# of confidence, instead of only the ones below CONFIDENCE_THRESHOLD.
# Useful while collecting data to judge classifier quality even on
# high-confidence cases, or as a temporary "audit" mode without having
# to lower the numeric threshold to force review on everything.
ALWAYS_ON: bool = False
