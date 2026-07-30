"""
calcolo fiato e magia

### Calcolo dei valori di FIATO e MAGIA

#### FIATO  = pool di azioni fisiche per turno
Bab diventa punti fiato -> numero di attacchi = Fiato 

Bab/5 = Fiato (minimo 1)

 
#### MAGIA  = pool di azioni magiche per turno

Usare livello incatore per definire i punti magia

livello incantatore/5 = Magia (minimo 1 se ha livello incantare, altrimenti 0)

#### EXTRA su puti fiato e magia
- bonus -> Attacchi multipli diventano punti bonus (esempio idra) oppure
possibilità di usare più volte una carta attacco specifica esempio morso
- per capacità magiche con usi limitati (in quel caso si ha limite di utilizzi massimi)

##### nota di design
Il numero massimo di attacchi per turno è limitato a 4 per garantire velocità di gioco.
Eventuali attacchi aggiuntivi vengono convertiti in bonus o utilizzi extra di abilità.
"""