"""
Static mappings used to calculate MonsterForge interpretation values
from D&D 3.x character skills.

This module defines the relationships between source-system skills,
interpretation groups, and reference ability scores.

It does not perform calculations; it only provides the static
conversion rules consumed by the transformation layer.
"""
# NOTE:
# These tables represent game rules and are intentionally immutable.
# They should not be modified during runtime.
from typing import Mapping
from types import MappingProxyType

# =====================
# SKILL GROUP MAPPING
# =====================

# Maps D&D 3.x skills to MonsterForge interpretation groups.
#
# Used during the transformation stage to aggregate source skills
# into the six domain-level interpretation values.
#
# Multiple D&D skills contribute to the same interpretation group,
# whose final value is calculated as the average of the associated
# skill values.
# SKILL_TO_INTERPRETATION_MAPPING   input → output
SKILL_TO_INTERPRETATION_MAPPING: Mapping[str, list[str]] = MappingProxyType({
    "athletics": [
        "tumble",          # Acrobazia
        "escape_artist",   # Artista della Fuga
        "ride",            # Cavalcare
        "balance",         # Equilibrio
        "swim",            # Nuotare
        "jump",            # Saltare
        "climb",           # Scalare
        "stabilize_self",  # Stabilizzarsi (v3.0 psionica)
    ],
    "empathy": [
        "animal_empathy",       # Empatia Animale (v3.0)
        "handle_animal",        # Addestrare Animali
        "diplomacy",            # Diplomazia
        "intimidate",           # Intimidire
        "perform",              # Intrattenere*
        "sense_motive",         # Percepire Intenzioni
        "gather_information",   # Raccogliere Informazioni
        "bluff",                # Raggirare
    ],
    "perception": [
        "intuit_direction", # Orientamento (v3.0)
        "listen",           # Ascoltare
        "search",           # Cercare
        "scry",             # Scrutare (v3.0)
        "spot",             # Osservare
        "read_lips",        # Leggere Labbra (v3.0)
        "remote_view",      # Vista Remota (v3.0 psionica)
    ],
    "stealth": [
        "disguise",        # Camuffare
        "move_silently",   # Muoversi Silenziosamente
        "hide",            # Nascondersi
        "innuendo",        # Comunicazione Segreta (v3.0)
        "sleight_of_hand", # Rapidità di Mano
        "pick_pocket",     # Svuotare Tasche (v3.0)
    ],
    "knowledge": [
        "concentration",   # Concentrazione
        "autohypnosis",    # Autoipnosi 
        "knowledge",       # Conoscenze*
        "decipher_script", # Decifrare Scritture
        "heal",            # Guarire
        "profession",      # Professione*
        "spellcraft",      # Sapienza Magica
        "psicraft",        # Sapienza psionica
        "survival",        # Sopravvivenza
        "appraise",        # Valutare
    ],
    "crafting": [
        "alchemy",            # Alchimia (v3.0)
        "craft",              # Artigianato*
        "disable_device",     # Disattivare Congegni
        "forgery",            # Falsificare
        "open_lock",          # Scassinare Serrature
        "use_rope",           # Utilizzare Corde
        "use_magic_device",   # Utilizzare Oggetti Magici
        "use_psionic_device", # Utilizzare Oggetti Psionici
    ],
})


# =====================
# REFERENCE ABILITY MAPPING
# =====================
# Defines the reference D&D ability score associated with each
# MonsterForge interpretation group.
#
# The reference ability is used during interpretation calculation
# to determine the base value and validate negative modifiers.
INTERPRETATION_TO_ABILITY_MAPPING: Mapping[str, str] = MappingProxyType({
    "athletics": "strength",
    "empathy": "charisma", 
    "perception": "wisdom",
    "stealth": "dexterity" ,
    "knowledge": "intelligence",
    "crafting": "intelligence",
})
