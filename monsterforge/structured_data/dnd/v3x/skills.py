"""
Abilità
"""
from dataclasses import dataclass, field

# =====================
# Abilità
# =====================
@dataclass(kw_only=True)
class Skills:       # oggetto che rappresenta le abilità di una creatura
    """Represents the skill values of a creature stat block."""
    # NOTE: # Some skills (e.g. Craft, Knowledge, Perform, and Profession) have
    # open-ended specializations in D&D 3.5. They are intentionally modeled
    # as string keys instead of enums to avoid restricting valid values to
    # a predefined list that would not fully represent all possible cases.

    # STANDARD SKILLS 3.5
    appraise: int | None = None              # Valutare    
    balance: int | None = None               # Equilibrio
    bluff: int | None = None                 # Raggirare
    climb: int | None = None                 # Scalare
    concentration: int | None = None         # Concentrazione

    craft: dict[str, int] = field(default_factory=dict) # Artigianato 
    ## Craft (alchemy, weaponsmithing, etc.)

    decipher_script: int | None = None       # Decifrare Scritture
    diplomacy: int | None = None             # Diplomazia
    disable_device: int | None = None        # Disattivare Congegni
    disguise: int | None = None              # Camuffare
    escape_artist: int | None = None         # Artista della Fuga
    forgery: int | None = None               # Falsificare
    gather_information: int | None = None    # Raccogliere Informazioni
    handle_animal: int | None = None         # Addestrare Animali
    heal: int | None = None                  # Guarire
    hide: int | None = None                  # Nascondersi
    intimidate: int | None = None            # Intimidire
    jump: int | None = None                  # Saltare

    knowledge: dict[str, int] = field(default_factory=dict)  # Conoscenze
    ## Knowledge (arcana, nature, religion, etc.)

    listen: int | None = None                # Ascoltare
    move_silently: int | None = None         # Muoversi Silenziosamente
    open_lock: int | None = None             # Scassinare

    perform: dict[str, int] = field(default_factory=dict) # Intrattenere
    # # Perform (sing, dance, oratory, etc.)

    profession: dict[str, int] = field(default_factory=dict) # Professione
    #Profession (farmer, sailor, merchant, etc.)

    ride: int | None = None                  # Cavalcare
    search: int | None = None                # Cercare
    sense_motive: int | None = None          # Percepire Intenzioni
    sleight_of_hand: int | None = None       # Rapidità di Mano

    # NOTE: speak_language is intentionally excluded from skill mapping:
    # languages are tracked separately, as known languages rather than numeric skill values

    spellcraft: int | None = None            # Sapienza Magica
    spot: int | None = None                  # Osservare
    survival: int | None = None              # Sopravvivenza
    swim: int | None = None                  # Nuotare
    tumble: int | None = None                # Acrobazia
    use_magic_device: int | None = None      # Utilizzare Oggetti Magici
    use_rope: int | None = None              # Usare Corde

    # PSIONIC SKILLS 3.5
    autohypnosis: int | None = None          # autoipnosi 
    psicraft: int | None = None              # sapienza psionica 
    use_psionic_device: int | None = None    # Utilizzare Oggetti Psionici

    # NOTE: the following skills are specific to version 3.0.
    # STANDARD SKILLS 3.0
    alchemy: int              # Alchimia
    innuendo: int             # Comunicazione Segreta
    animal_empathy: int       # Empatia Animale
    read_lips: int            # Leggere Labbra
    intuit_direction: int     # Orientamento
    scry: int                 # Scrutare
    pick_pocket: int          # Svuotare Tasche

    # PSIONIC SKILLS 3.0
    stabilize_self: int       # Stabilizzarsi
    remote_view: int          # Vista Remota