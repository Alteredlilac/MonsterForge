"""
Skills
"""
from dataclasses import dataclass, field

# =====================
# Skills
# =====================
@dataclass(kw_only=True)
class Skills:
    """Represents the skill values of a creature stat block."""
    # NOTE: # Some skills (e.g. Craft, Knowledge, Perform, and Profession) have
    # open-ended specializations in D&D 3.5. They are intentionally modeled
    # as string keys instead of enums to avoid restricting valid values to
    # a predefined list that would not fully represent all possible cases.

    # STANDARD SKILLS 3.5
    appraise: int | None = None
    balance: int | None = None
    bluff: int | None = None
    climb: int | None = None
    concentration: int | None = None

    craft: dict[str, int] = field(default_factory=dict)
    ## Craft (alchemy, weaponsmithing, etc.)

    decipher_script: int | None = None
    diplomacy: int | None = None
    disable_device: int | None = None
    disguise: int | None = None
    escape_artist: int | None = None
    forgery: int | None = None
    gather_information: int | None = None
    handle_animal: int | None = None
    heal: int | None = None
    hide: int | None = None
    intimidate: int | None = None
    jump: int | None = None

    knowledge: dict[str, int] = field(default_factory=dict)
    ## Knowledge (arcana, nature, religion, etc.)

    listen: int | None = None
    move_silently: int | None = None
    open_lock: int | None = None

    perform: dict[str, int] = field(default_factory=dict)
    # # Perform (sing, dance, oratory, etc.)

    profession: dict[str, int] = field(default_factory=dict)
    #Profession (farmer, sailor, merchant, etc.)

    ride: int | None = None
    search: int | None = None
    sense_motive: int | None = None
    sleight_of_hand: int | None = None

    # NOTE: speak_language is intentionally excluded from skill mapping:
    # languages are tracked separately, as known languages rather than numeric skill values

    spellcraft: int | None = None
    spot: int | None = None
    survival: int | None = None
    swim: int | None = None
    tumble: int | None = None
    use_magic_device: int | None = None
    use_rope: int | None = None

    # PSIONIC SKILLS 3.5
    autohypnosis: int | None = None
    psicraft: int | None = None
    use_psionic_device: int | None = None

    # NOTE: the following skills are specific to version 3.0.
    # STANDARD SKILLS 3.0
    alchemy: int | None = None
    innuendo: int | None = None
    animal_empathy: int | None = None
    read_lips: int  | None = None
    intuit_direction: int | None = None
    scry: int | None = None
    pick_pocket: int | None = None

    # PSIONIC SKILLS 3.0
    stabilize_self: int | None = None
    remote_view: int | None = None
