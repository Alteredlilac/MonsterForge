"""
Tests for D&D 3.x psionic power raw field models.

Covers:
- Nested raw field structures
- Raw value preservation
- Power level representation
- Summoned creature representation
- Default list initialization
"""

from monsterforge.parsing.dnd.v3x.raw_fields.psionics import (
    PowerLevel,
    PsionicSummonedCreature,
    PsionicPower,
)


# =====================
# POWER LEVEL
# =====================

def test_power_level_preserves_class_and_level():
    power_level = PowerLevel(
        character_class="Psion",
        level="5",
    )

    assert power_level.character_class == "Psion"
    assert power_level.level == "5"


# =====================
# SUMMONED CREATURE
# =====================

def test_psionic_summoned_creature_preserves_raw_values():
    creature = PsionicSummonedCreature(
        creature_name="Astral Construct",
        creature_description="A temporary construct created from ectoplasm.",
    )

    assert creature.creature_name == "Astral Construct"
    assert creature.creature_description == (
        "A temporary construct created from ectoplasm."
    )


def test_psionic_summoned_creature_description_defaults_to_none():
    creature = PsionicSummonedCreature(
        creature_name="Astral Construct",
    )

    assert creature.creature_description is None


# =====================
# PSIONIC POWER
# =====================

def test_psionic_power_preserves_required_fields():
    power = PsionicPower(
        name="Mind Thrust",
        discipline="Telepathy",
        level=[
            PowerLevel(
                character_class="Psion",
                level="1",
            )
        ],
        duration="Instantaneous",
        description="A mental attack against a creature.",
    )

    assert power.name == "Mind Thrust"
    assert power.discipline == "Telepathy"
    assert power.duration == "Instantaneous"
    assert power.description == "A mental attack against a creature."


def test_psionic_power_preserves_power_levels():
    levels = [
        PowerLevel(
            character_class="Psion",
            level="1",
        ),
        PowerLevel(
            character_class="Psychic Warrior",
            level="1",
        ),
    ]

    power = PsionicPower(
        name="Vigor",
        discipline="Psychometabolism",
        level=levels,
        duration="1 minute/level",
        description="Creates temporary vitality.",
    )

    assert power.level == levels
    assert len(power.level) == 2
    assert power.level[0].character_class == "Psion"


def test_psionic_power_descriptor_defaults_to_empty_list():
    power = PsionicPower(
        name="Energy Ray",
        discipline="Psychokinesis",
        level=[
            PowerLevel(
                character_class="Psion",
                level="1",
            )
        ],
        duration="Instantaneous",
        description="Creates an energy ray.",
    )

    assert power.descriptor == []


def test_psionic_power_summoned_creatures_defaults_to_empty_list():
    power = PsionicPower(
        name="Astral Construct",
        discipline="Metacreativity",
        level=[
            PowerLevel(
                character_class="Psion",
                level="1",
            )
        ],
        duration="1 round/level",
        description="Creates an astral construct.",
    )

    assert power.summoned_creatures == []


def test_psionic_power_preserves_summoned_creatures():
    summoned = [
        PsionicSummonedCreature(
            creature_name="Astral Construct"
        )
    ]

    power = PsionicPower(
        name="Astral Construct",
        discipline="Metacreativity",
        level=[
            PowerLevel(
                character_class="Psion",
                level="1",
            )
        ],
        duration="1 round/level",
        description="Creates a temporary astral construct.",
        summoned_creatures=summoned,
    )

    assert power.summoned_creatures == summoned
    assert (
        power.summoned_creatures[0].creature_name
        == "Astral Construct"
    )


def test_psionic_power_preserves_optional_raw_fields():
    power = PsionicPower(
        name="Dispel Psionics",
        discipline="Psychokinesis",
        level=[
            PowerLevel(
                character_class="Psion",
                level="3",
            )
        ],
        duration="Instantaneous",
        description="Attempts to dispel psionic effects.",
        dispels_usage="Can dispel one active power.",
    )

    assert power.dispels_usage == "Can dispel one active power."
    