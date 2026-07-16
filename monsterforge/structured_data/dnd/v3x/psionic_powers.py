"""
poteri psionici
"""
from dataclasses import dataclass, field

# =====================
# Poteri Psionici
# =====================
@dataclass(kw_only=True)
class Power:
    ...


# =====================
# Incantatore Psionico
# =====================
@dataclass(kw_only=True)
class Psionics:
    """Represents the psionic manifestation data of a creature."""
    psionic_classes: list[str] = field(default_factory=list) # classi psioniche
    manifester_level: int | None = None # livello di manifestazione
    powers_known: list[Power] = field(default_factory=list) # poteri psionici
    power_points: int | None = None  # punti potere

    @property
    def is_psionic(self) -> bool:
        """Indicates whether the creature has psionic manifestation ability."""
        return self.manifester_level is not None and self.manifester_level >= 1
        
