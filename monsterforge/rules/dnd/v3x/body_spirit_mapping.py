"""
calcolo caratteristiche fisice e spirito

definire regola per cui si usa carisma invece di intelligenza 


### Calcolo dei valori di CORPO e SPIRITO

- Usare i modificatori caratteristica come indicatore per valori corpo e spirito
- I modificatori caratteristica vengono utilizzati come feature
normalizzate evitando di trasferire direttamente il sistema D&D.
- modificatori negativi valgono 0

| CARATTERISTICA D&D | CARATTERISTICA CORPO |
|--------------------|----------------------|
| Forza              | Attacco              |
| Destrezza          | Velocità             |
| Costituzione       | Difesa               |
| Destrezza*         | Difesa (non morti)   |

* Per i non morti, la Difesa utilizza la Destrezza invece della Costituzione

| CARATTERISTICA D&D | CARATTERISTICA SPIRITO |
|--------------------|------------------------|
| Intelligenza       | Potere                 |
| Saggezza           | Tangenza               |
| Carisma            | Spin                   |

Per alcuni Mostri usare il Carisma per determinare il Potere e l'intelligenza per determinare lo Spin.

Incorporei non hanno attacco e difesa

#### Esempio conversione -> Lupo : 

| CARATTERISTICA D&D  | CARATTERISTICA CORPO   |
|---------------------|------------------------|
| - Forza = 13        | - Attacco = 1          |
| - Destrezza = 15    | - Velocità = 2         |
| - Costituzione = 15 | - Difesa =  2          |
| CARATTERISTICA D&D  | CARATTERISTICA SPIRITO |
| - Intelligenza = 2  | - Potere =  0          |
| - Saggezza = 12     | - Tangenza = 1         |
| - Carisma = 6       | - Spin = 0             |
"""