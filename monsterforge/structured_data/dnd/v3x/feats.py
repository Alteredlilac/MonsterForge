"""
talenti 
Feat

- Talenti
Tipo (metamagia, bonus, di classe, fabbricazione, psionico, generale, attacco, qualità speciale)
"""
from dataclasses import dataclass, field

# =====================
# FEATS
# =====================
@dataclass(kw_only=True)
class Feat:
    ...

class FeatCategory(str, Enum):
    METAMAGIC = "metamagic"          # metamagico*
    METAPSIONIC = "metapsionic"      # metapsionico*
    GRANTS_BONUS = "grants_bonus"    # concede bonus (dividere bonus abilità?)*
    CRAFTING = "crafting"            # fabbricazione
    GRANTS_ATTACK = "grants_action"  # concede attachi speciali
    GRANTS_QUALITY = "grants_quality" # concede qualità speciali
    competenza = ""                  # concede competenza in qualcosa
    concede_oggetto = ""             # concede un oggetto o ne simula il possesso
    concede_creatura = ""            # concede una o più creature (autorità, ottenere famiglio)
    generico = "generic"              # generico *
    Psionico = ""                    # psionico *
    Relativo_a_una_classe = ""       # relativo a una classe * o di classe (talenti dei guerrieri)


@dataclass(kw_only=True)
class Feat:
    name: str
    description: str
    categories: list[FeatCategory] = field(default_factory=list)  # un talento può appartenere a più categorie
    requirements: list[FeatRequirement] = field(default_factory=list)

    # Optional behavioral components, presence coerente con la/le categorie dichiarate
    metamagic: MetamagicEffect | None = None
    granted_modifiers: list[EffectModifier] = field(default_factory=list)
    crafting: CraftingRequirements | None = None
    granted_action: SpecialAbility | None = None