"""
Tests for Creature and CreatureModifier.
"""
from monsterforge.structured_data.dnd.v3x.creatures import CreatureModifier
from monsterforge.structured_data.dnd.v3x.enums import (
    CreatureType, CreatureSubtype, MovementMode,
)


def test_creature_minimal_creation(make_creature):
    wolf = make_creature()
    assert wolf.name == "Wolf"
    assert wolf.creature_type == CreatureType.ANIMAL
    assert wolf.hit_points_total == 23


def test_creature_auto_generates_unique_id(make_creature):
    w1 = make_creature()
    w2 = make_creature()
    assert w1.id != w2.id


def test_creature_full_attack_defaults_to_none(make_creature):
    """full_attack is optional by design: a robustness choice for
    creatures whose full attack sequence isn't distinct from their
    single-attack listing."""
    wolf = make_creature()
    assert wolf.full_attack is None


def test_creature_resistances_default_to_none(make_creature):
    wolf = make_creature()
    assert wolf.spell_resistance is None
    assert wolf.power_resistance is None


def test_creature_can_have_multiple_subtypes(make_creature):
    aquatic_elemental = make_creature(
        creature_type=CreatureType.ELEMENTAL,
        creature_subtype=[CreatureSubtype.WATER, CreatureSubtype.EXTRAPLANAR],
    )
    assert len(aquatic_elemental.creature_subtype) == 2


def test_creature_can_have_multiple_spellcasting_progressions(make_creature):
    """A multiclass creature (e.g. a cleric/wizard) may have more than
    one independent spellcasting progression."""
    from monsterforge.structured_data.dnd.v3x.spells import Spellcasting
    multiclass = make_creature(
        spellcasting=[Spellcasting(caster_level=3), Spellcasting(caster_level=2)],
    )
    assert len(multiclass.spellcasting) == 2


def test_creature_abilities_allow_none_for_undead(make_creature, make_abilities):
    skeleton = make_creature(
        creature_type=CreatureType.UNDEAD,
        abilities=make_abilities(constitution=None, intelligence=None),
    )
    assert skeleton.abilities.constitution is None


def test_creature_modifier_minimal_creation():
    lycanthropy = CreatureModifier(
        name="Lycanthropy", added_description="Gains animal traits and a hybrid form.",
    )
    assert lycanthropy.name == "Lycanthropy"
    assert lycanthropy.type_override is None
    assert lycanthropy.added_subtypes == []


def test_creature_modifier_auto_generates_unique_id():
    m1 = CreatureModifier(name="X", added_description="x")
    m2 = CreatureModifier(name="X", added_description="x")
    assert m1.id != m2.id


def test_creature_modifier_type_and_size_overrides():
    vampirism = CreatureModifier(
        name="Vampirism", added_description="Undead traits.",
        type_override=CreatureType.UNDEAD,
    )
    assert vampirism.type_override == CreatureType.UNDEAD
    assert vampirism.size_override is None  # not overridden


def test_creature_modifier_speed_bonus_is_keyed_by_movement_mode():
    """speed_bonus represents additive bonuses to existing movement modes
    (e.g. {LAND: 3}), distinct from added_speed which introduces wholly
    new movement modes (e.g. granting flight)."""
    vampirism = CreatureModifier(
        name="Vampirism", added_description="x",
        speed_bonus={MovementMode.LAND: 3},
    )
    assert vampirism.speed_bonus[MovementMode.LAND] == 3


def test_creature_modifier_added_speed_introduces_new_movement(make_movement):
    vampirism = CreatureModifier(
        name="Vampirism", added_description="x",
        added_speed=[make_movement(movement_type=MovementMode.FLY, movement_speed=18)],
    )
    assert vampirism.added_speed[0].movement_type == MovementMode.FLY


def test_creature_modifier_spell_resistance_progression():
    template = CreatureModifier(
        name="Half-Fiend", added_description="x",
        spell_resistance_base=10, spell_resistance_per_level=1,
    )
    assert template.spell_resistance_base == 10
    assert template.spell_resistance_per_level == 1


def test_creature_modifier_ability_modifiers_are_a_dict():
    template = CreatureModifier(
        name="Half-Fiend", added_description="x",
        ability_modifiers={"strength": 4, "intelligence": 2},
    )
    assert template.ability_modifiers["strength"] == 4


def test_creature_modifier_can_add_equipment():
    """e.g. a lich's phylactery is equipment granted by the template
    itself, not part of the base creature."""
    from monsterforge.structured_data.dnd.v3x.items import Item
    from monsterforge.structured_data.dnd.v3x.enums import ItemType
    phylactery = Item(name="Phylactery", item_type=ItemType.ACCESSORY)
    lichdom = CreatureModifier(
        name="Lichdom", added_description="x", added_equip=[phylactery],
    )
    assert lichdom.added_equip[0].name == "Phylactery"


def test_creature_modifier_can_add_special_qualities(make_effect_target):
    from monsterforge.structured_data.dnd.v3x.special_qualities import SpecialQuality
    from monsterforge.structured_data.dnd.v3x.enums import SpecialAbilityType
    dr = SpecialQuality(name="DR 5/silver", special_ability_type=SpecialAbilityType.EXTRAORDINARY)
    lycanthropy = CreatureModifier(
        name="Lycanthropy", added_description="x",
        added_special_qualities=[dr],
    )
    assert lycanthropy.added_special_qualities[0].name == "DR 5/silver"
