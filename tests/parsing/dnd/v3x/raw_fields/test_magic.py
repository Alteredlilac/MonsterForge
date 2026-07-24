"""
Tests for D&D 3.x spell and cleric domain raw field models.

Covers:
- Nested raw field structures
- Raw value preservation
- Default list initialization
- Spell level representation
- Summoned creature representation
- Cleric domain granted spells
"""

from monsterforge.parsing.dnd.v3x.raw_fields.magic import (
    SpellLevel,
    SummonedCreature,
    Spell,
    DomainGrantedSpell,
    ClericDomain,
)


# =====================
# SPELL LEVEL
# =====================

def test_spell_level_preserves_class_and_level():
    spell_level = SpellLevel(
        character_class="Sor/Wiz",
        level="3",
    )

    assert spell_level.character_class == "Sor/Wiz"
    assert spell_level.level == "3"


# =====================
# SUMMONED CREATURE
# =====================

def test_summoned_creature_preserves_raw_values():
    creature = SummonedCreature(
        creature_name="Dire Wolf",
        creature_description="A large wolf with enhanced abilities.",
    )

    assert creature.creature_name == "Dire Wolf"
    assert creature.creature_description == "A large wolf with enhanced abilities."


def test_summoned_creature_description_defaults_to_none():
    creature = SummonedCreature(
        creature_name="Wolf",
    )

    assert creature.creature_description is None


# =====================
# SPELL
# =====================

def test_spell_preserves_required_fields():
    spell = Spell(
        name="Fireball",
        school="Evocation",
        level=[
            SpellLevel(
                character_class="Sor/Wiz",
                level="3",
            )
        ],
        duration="Instantaneous",
        description="A burst of fire dealing damage.",
    )

    assert spell.name == "Fireball"
    assert spell.school == "Evocation"
    assert spell.duration == "Instantaneous"
    assert spell.description == "A burst of fire dealing damage."


def test_spell_preserves_spell_levels():
    levels = [
        SpellLevel(character_class="Sor/Wiz", level="3"),
        SpellLevel(character_class="Fire", level="4"),
    ]

    spell = Spell(
        name="Flame Strike",
        school="Evocation",
        level=levels,
        duration="Instantaneous",
        description="A column of divine fire.",
    )

    assert spell.level == levels
    assert len(spell.level) == 2
    assert spell.level[0].character_class == "Sor/Wiz"


def test_spell_descriptor_defaults_to_empty_list():
    spell = Spell(
        name="Magic Missile",
        school="Evocation",
        level=[
            SpellLevel(
                character_class="Sor/Wiz",
                level="1",
            )
        ],
        duration="Instantaneous",
        description="A missile of magical energy.",
    )

    assert spell.descriptor == []


def test_spell_summoned_creatures_defaults_to_empty_list():
    spell = Spell(
        name="Fireball",
        school="Evocation",
        level=[
            SpellLevel(
                character_class="Sor/Wiz",
                level="3",
            )
        ],
        duration="Instantaneous",
        description="A burst of flame.",
    )

    assert spell.summoned_creatures == []


def test_spell_preserves_summoned_creatures():
    summoned = [
        SummonedCreature(
            creature_name="Celestial Wolf"
        )
    ]

    spell = Spell(
        name="Summon Monster I",
        school="Conjuration",
        level=[
            SpellLevel(
                character_class="Clr",
                level="1",
            )
        ],
        duration="1 round/level",
        description="Summons a celestial creature.",
        summoned_creatures=summoned,
    )

    assert spell.summoned_creatures == summoned
    assert spell.summoned_creatures[0].creature_name == "Celestial Wolf"


# =====================
# CLERIC DOMAIN
# =====================

def test_domain_granted_spell_preserves_raw_values():
    spell = DomainGrantedSpell(
        level="1",
        name="Protection from Evil",
        description="Provides protection against evil creatures.",
        extra_description="Cast as a protection spell only.",
    )

    assert spell.level == "1"
    assert spell.name == "Protection from Evil"
    assert spell.extra_description == "Cast as a protection spell only."


def test_cleric_domain_preserves_granted_spells():
    granted_spell = DomainGrantedSpell(
        level="1",
        name="Bless",
    )

    domain = ClericDomain(
        name="Good",
        granted_spells=[granted_spell],
    )

    assert domain.name == "Good"
    assert domain.granted_spells == [granted_spell]


def test_cleric_domain_granted_powers_defaults_to_empty_list():
    domain = ClericDomain(
        name="Fire",
        granted_spells=[],
    )

    assert domain.granted_powers == []
    