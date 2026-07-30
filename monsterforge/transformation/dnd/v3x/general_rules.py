"""
GENERALI

####REGOLA GENERALE -> tutti i valori decimali vengono arrotondati per difetto

risucchio caratteristica = media come per pf e dimezzati (minimo 1) -> non possono diventare negativi

valori di cura  diventano media come pf  -> 1d6 = 3 danni curati 
- nel caso di valori assoluti (non modificatori) esempio 5 =  vengono dimezzati e arrotondati per difetto 

danni diventano media come pf  -> 1d6 = 3 danni 

carte per livello (incantesimi, attacchi eccetera)

property spellcasting_progression in CharacterClass,
che internamente fa branching su max_spell_level per scegliere
tra ProgressionRate.LOW/MEDIUM/HIGH 
"""


