"""
Body and Spirit stat mapping rules for D&D 3.x conversion.

This module defines how D&D ability modifiers are mapped to the
target system's Body (physical) and Spirit (mental) stats.

Key rules:
- Ability *modifiers* (not raw scores) are used as normalized features.
- Negative modifiers are treated as 0.
- Mappings are static and immutable (MappingProxyType).
- Special cases (e.g. undead, constructs) override the default mappings.

Body mapping:
- strength     → attack
- dexterity    → speed
- constitution → defense

Special cases:
- Undead: defense uses dexterity instead of constitution
- Constructs: defense uses strength instead of constitution

Spirit mapping:
- intelligence → power
- wisdom       → ward
- charisma     → flow

Exception rule (caster-based swap):
- For specific creatures, charisma may replace intelligence for power
  if:
    charisma > intelligence + 3 AND creature is a caster

Notes:
- Incorporeal entities may not have attack/defense (handled elsewhere).
"""

