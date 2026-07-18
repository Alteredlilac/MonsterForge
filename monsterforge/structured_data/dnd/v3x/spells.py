"""
incantesimi

- Incantesimi 
- livello
- scuola
- come qualità speciale + attacco speciale 

"""
from dataclasses import dataclass, field
from .enums import MagicType

# =====================
# Slot Incantesimi
# =====================
@dataclass(kw_only=True)
class SpellSlots:
    ...

# =====================
# Incantesimi
# =====================
@dataclass(kw_only=True)
class Spell:
    ...


# =====================
# Spellcasting
# =====================

@dataclass(kw_only=True)
class Spellcaster:
    """Represents il fatto che una creatura sia una incatatore"""
    # NOTE:
    # Spellcasting class is kept as a generic string to support classes from
    # different supplements and avoid limiting the model to a fixed set of values.
    spellcasting_class: str | None = None
    spellcasting_type: MagicType | None = None  # arcane, divine, etc.

@dataclass(kw_only=True)
class Spellcasting(Spellcaster):
    """Represents the spellcasting data of a creature."""
    caster_level: int | None = None  # livello incantatore
    spells_known: list[Spell] = field(default_factory=list)  # incantesimi conosciuti
    prepared_spells: list[Spell] = field(default_factory=list)  # incantesimi preparati
    spell_slots: SpellSlots | None = None  # slot incantesimi

    @property
    def is_spellcaster(self) -> bool:
        """Indicates whether the creature has spellcasting ability."""
        return self.caster_level is not None and self.caster_level >= 1 # mi sembra contorta