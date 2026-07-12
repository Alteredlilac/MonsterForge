# RPG Data Transformation Engine for Card Generation

## Obiettivo del progetto

Creare un motore di trasformazione in grado di convertire
stat block RPG complessi in rappresentazioni semplificate
utilizzabili come carte da gioco mantenendo:

- identità della creatura
- differenze tra archetipi
- bilanciamento numerico
- velocità di gioco

## Descrizione:
- Scraped and parsed OGL RPG data from web sources
- Designed custom lossy transformation algorithms
- LLM-based semantic classifier with human-in-the-loop validation
- Converted complex stat blocks into simplified card representations
- Built a rendering pipeline for printable card layouts
- Developed a desktop validation tool with PyQt5


## Spiegazione

Progetto di scraping in cui volevo fare un programma che usando alcuni algoritmi miei di conversione (lossy non invertibili)
trasformano i dati dei mostri di D&D 3.5 o Pathfinder 1ª edizione in carte da gioco.
Usando requests per scaricare le pagine html e Beautifulsoup sul sito d20.org per prendere le informazioni OGL e salvarle su un DB SQL
e poi applicare le conversioni con i miei algoritmi e generare le carte statiche come pagine web con l'opzione stampa per salvarle come immagini.
Il tutto fatto con una semplice interfaccia fatta con PyQt5 per validare le carte o modificarle manualmente.
per i dati numerici si utilizzano gli algoritmi in modo da garantire bilanciamento, mentre per valori non numerici si utilizza un LLM
come classificatore semantico e un controllo umano per la validazione/modifica dei valori proposti.
L'LLM non genera liberamente dati di gioco, ma effettua una classificazione vincolata da uno schema.


## PIPELINE

Raw RPG Text
     |
     v
Parser
     |
     v
Structured Data
     |
     +----------------+
     |                |
     v                v
Numerical Rules       LLM Semantic Classification
     |                |
     +-------+--------+
             |
             v
      Human Validation
             |
             v
        Card Generator


## Design decisions

- La conversione è volutamente lossy:
  il sistema conserva l'identità funzionale della creatura,
  non tutti i dettagli dello stat block originale.

- I valori numerici vengono generati tramite formule deterministiche
  per mantenere coerenza e bilanciamento.

- I dati descrittivi vengono classificati semanticamente tramite LLM
  con validazione umana.

- Il numero massimo di azioni per turno è limitato per mantenere
  la velocità del gioco.


## ALGORITMI

####REGOLA GENERALE -> tutti i valori decimali vengono arrotondati per difetto

### Calcolo del valore VITA

| VITA | TAGLIA       |
|------|--------------|
| 1    | Minuta       |
| 2    | Piccolissima |
| 5    | Minuscola    |
| 10   | Piccola      |
| 15   | Media        |
| 30   | Grande       |
| 45   | Enorme       |
| 60   | Mastodontica |
| 90   | Colossale    |


A questi aggiungo valore medio del dado vita moltiplicato per il numero di DV

| Tipo di Dado | VITA |
|--------------|------|
| D2           | 1    |
| D4           | 2    |
| D6           | 3    |
| D8           | 4    |
| D10          | 5    |
| D12          | 6    |

#### Esempio conversione -> Lupo : taglia media , 2d8 DV -> 15 + 2*4 = VITA 23

-----------------

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


-----------------

### Calcolo dei valori di ARMATURA e TALISMANO

- Armatura = CA totale - Destrezza- 10 (Deviazione e bonus di taglia non vengono considerati)
- Talismano = Resistenza agli incantesimi -10 + Deviazione

#### Esempio conversione -> Lupo : 

| CA D&D                          | ARMATURA                              |
|---------------------------------|---------------------------------------|
| CA totale = 14                  | 14 - 2 (valore di Destrezza) - 10 = 2 |
| CA D&D                          | TALISMANO                             |
| --------                        | -----------                           |
| Resistenza agli incantesimi = 0 | 0                                     |

-----------------

### Calcolo dei valori di INTERPRETAZIONE

#### Esistono 6 valori di interpretazione: 
- Atletica
- Empatia
- Percezione
- Furtività
- Cultura
- Artigianato

raggruppare le varie abilità di D&D nei 6 gruppi interpretazione e fare una media,
da quella ricavare il valore da esssegnare 

- per ognuna delle abilità di un gruppo di abilità di D&D associate a un valore di interpretazione
si prende il valore dell' abilità utilizzando il metodo di calcolo esposto sotto per
ognuna delle abilità di quel gruppo si fa la media e si ottiene il valore di interpretazione associata


- metodo di calcolo utilizzato:
descrizione a parole: 
Prendo la caratteristica associata, se positiva o prendo 0 se negativa, 

se il valore è 0 cioè non ci sono gadi di abilità assegnati o altri bonus prendo come valore la caratteristica associata,
altrimenti prendo il valore a cui sottraggo la caratteristica associata e 3 (quindi ottengo i gradi di abilità) 

e faccio la media di tutti i valori non nulli del gruppo di valori considerati 


poi controllo, se la caratteristica di riferimento del valore di interpretazione è minore di 0, 
il valore di interpretazione sarà 0 (indipendentemente dalla media ottenuta), altrimenti sarà la media ottenuta.



- metodo di calcolo utilizzato possibile versione in python:
```python
def calcola_interpretazione(valori_abilita, mod_caratteristica):
    """
    valori_abilita: lista dei valori delle abilità D&D (es: [2,2,0,3,...])
    mod_caratteristica: modificatore della caratteristica associata (es: +2, -1, ecc.)
    """

    # Se la caratteristica è negativa → risultato finale sarà 0
    if mod_caratteristica < 0:
        return 0

    # Per i calcoli uso comunque max(0, mod)
    mod_car = max(0, mod_caratteristica)

    valori_calcolati = []

    for val in valori_abilita:
        if val == 0:
            risultato = mod_car
        else:
            risultato = val - mod_car - 3

        # considero solo valori NON nulli
        if risultato != 0:
            valori_calcolati.append(risultato)

    # evitare divisione per zero
    if not valori_calcolati:
        return 0

    # media finale
    media = sum(valori_calcolati) / len(valori_calcolati)

    return media
```


- modificatori negativi valgono 0

| ABILITÀ D&D               | INTERPRETAZIONE   |
|---------------------------|-------------------|
| Acrobazia                 | Atletica          |
| Artista della fuga        | Atletica          |
| Cavalcare                 | Atletica          |
| Equilibrio                | Atletica          |
| Nuotare                   | Atletica          |
| Saltare                   | Atletica          |
| Scalare                   | Atletica          |
| -------------             | ----------------- |
| Addestrare animali        | Empatia           |
| Diplomazia                | Empatia           |
| Intimidire                | Empatia           |
| Intrattenere              | Empatia           |
| Percepire intenzioni      | Empatia           |
| Raccogliere informazioni  | Empatia           |
| Raggirare                 | Empatia           |
| -------------             | ----------------- |
| Ascoltare                 | Percezione        |
| Cercare                   | Percezione        |
| Osservare                 | Percezione        |
| -------------             | ----------------- |
| Camuffare                 | Furtività         |
| Muoversi silenziosamente  | Furtività         |
| Nascondersi               | Furtività         |
| Rapidità di mano          | Furtività         |
| -------------             | ----------------- |
| Concentrazione            | Cultura           |
| Conoscenze                | Cultura           |
| Decifrare scritture       | Cultura           |
| Guarire                   | Cultura           |
| Professione               | Cultura           |
| Sapienza magica           | Cultura           |
| Sopravvivenza             | Cultura           |
| Valutare                  | Cultura           |
| -------------             | ----------------- |
| Artigianato               | Artigianato       |
| Disattivare congegni      | Artigianato       |
| Falsificare               | Artigianato       |
| Scassinare serrature      | Artigianato       |
| Utilizzare corde          | Artigianato       |
| Utilizzare oggetti magici | Artigianato       |
| -------------             | ----------------- |


| CARATTERISTICA DI RIFERIMENTO D&D | INTERPRETAZIONE |
|-----------------------------------|-----------------|
| Forza                             | Atletica        |
| Carisma                           | Empatia         |
| Saggezza                          | Percezione      |
| Destrezza                         | Furtività       |
| Intelligenza                      | Cultura         |
| Intelligenza                      | Artigianato     |

#### Esempio conversione -> Lupo : (mostro i risultati per semplicità)

Atletica = 2
Empatia  = 0
Percezione = 2
Furtività = 2
Cultura = 0
Artigianato = 0

-----------------

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
-----------------

- bias su abilità non nulle -> voluto e conosciuto 

- ignoro valore di costituzione x vita (meno pf ma bilanciato da taglia) -> Si non ci interessa

- problema con attacchi, attacchi speciali, qualità speciali e oggetti -> risolto con classificazione semantica

- vedere come gestire risucchio caratteristiche -> media come per pf e dimezzati (minimo 1) -> non possono diventare negativi

- vedere come gestire cura diventano media come pf  -> 1d6 = 3 danni curati 
- nel caso di valori assoluti (non modificatori) esempio 5 =  vengono dimezzati e arrotondati per difetto 

- problema con metodi di movimento (volare, nuotare, velcità) non inclusi -> uso VELOCITÀ come velocità e metodi speciali come carte

- danni diventano media come pf  -> 1d6 = 3 danni 


----------------

# REGOLE DI CLASSIFICAZIONE DI ATTACCHI, TALENTI QUALITÀ SPECIALI E INCANTESIMI

usare AI come classificatore semantico per dati non numerici, umano come validatore / correttore

Tipo Fisico/ Magico

Carte Attacco = metodi di attacco 
Carte difesa = metodi di difesa
Carte speciali = altri metodi

Attacco, difesa e speciale possono essere = Attivi (deve fare qualcosa per) oppure Passivo (sempre in funzione o automatici)

Esempi:
Attacco-attivo = pugno
Attacco-passivo = aura infuocata
Difesa-attivo = parata
Difesa-passivo = durezza
Speciale-attivo = mega salto
Speciale-passivo = rigenerazione


quindi 

Tipo
 ↓
Categoria principale
 ↓
Modalità
 ↓
Effetto
 ↓
Bersaglio
 ↓
Risorsa


esempio: 
{
 "tipo": "Fisico",
 "categoria": "Speciale",
 "modalita": "Passivo",
 "effetto": "Cura",
 "bersaglio": "Se stesso",
 "risorsa": "Nessuna"
}

vanno aggiunti questi due: 

"durata": "Istantaneo / Temporaneo / Permanente"
"utilizzo": "Illimitato / Giornaliero / Limitato / Situazionale"  
spiegazione: (limitato esempio ogni 1d4 round come per le armi a soffio, situazionale esempio attacco furtivo)

e poi vanno aggiunti questi 3 per la carta:
- Nome 
- descrizione
- valore del danno (usa la stessa logica dei punti vita ->  media come pf  -> 1d6 = 3 danni) 

per revisione umana va aggiunto valore di confidenza 
- "confidence": 0.92 Se confidence < 0.7 -> manda a revisione manuale. 

### Esempi pratici

#### Esempio 1
##### Input D&D
```text
Morso:
Attacco naturale che infligge 1d6 danni perforanti.
```

##### Output
```json
{
  "tipo": "Fisico",
  "categoria": "Attacco",
  "modalita": "Attivo",
  "effetto": "Danno",
  "bersaglio": "Singolo",
  "risorsa": "Fiato",
  "durata": "Istantaneo",
  "utilizzo": "Illimitato",

  "carta": {
    "nome": "Morso",
    "descrizione": "Attacco naturale che infligge danni perforanti.",
    "danno": 3
  }
}
```

#### Esempio 2
##### Input D&D
```text
Aura di fuoco:
Ogni creatura adiacente subisce 1d4 danni da fuoco automaticamente.
```

##### Output
```json
{
  "tipo": "Magico",
  "categoria": "Attacco",
  "modalita": "Passivo",
  "effetto": "Danno area",
  "bersaglio": "Vicini",
  "risorsa": "Nessuna",
  "durata": "Permanente",
  "utilizzo": "Illimitato",

  "carta": {
    "nome": "Aura di fuoco",
    "descrizione": "Le creature vicine subiscono automaticamente danni da fuoco.",
    "danno": 2
  }
}
```

#### Esempio 3
##### Input D&D
```text
Rigenerazione 5:
La creatura recupera 5 PF ogni round.
```

##### Output
```json
{
  "tipo": "Fisico",
  "categoria": "Speciale",
  "modalita": "Passivo",
  "effetto": "Cura",
  "bersaglio": "Se stesso",
  "risorsa": "Nessuna",
  "durata": "Permanente",
  "utilizzo": "Illimitato",

  "carta": {
    "nome": "Rigenerazione",
    "descrizione": "La creatura recupera punti vita ogni round.",
    "danno": 0
  }
}
```


#### Esempio 4 -> Talento
##### Input D&D
```txt
Attacco Poderoso:
Puoi sacrificare precisione per aumentare il danno.
```

##### Output
```json
{
  "tipo": "Fisico",
  "categoria": "Attacco",
  "modalita": "Passivo",
  "effetto": "Bonus danno",
  "bersaglio": "Se stesso",
  "risorsa": "Nessuna",
  "durata": "Permanente",
  "utilizzo": "Situazionale",

  "carta": {
    "nome": "Attacco Poderoso",
    "descrizione": "Aumenta il danno degli attacchi sacrificando precisione.",
    "danno": 0
  }
}
```

#### Esempio 5 -> Capacità con utilizzo limitato
##### Input D&D
```text
Arma a soffio:
Una volta ogni 1d4 round la creatura emette un cono di fuoco.
Infligge 6d6 danni.
```

##### Output
```json
{
  "tipo": "Magico",
  "categoria": "Attacco",
  "modalita": "Attivo",
  "effetto": "Danno area",
  "bersaglio": "Area",
  "risorsa": "Magia",
  "durata": "Istantaneo",
  "utilizzo": "Limitato",

  "carta": {
    "nome": "Arma a soffio",
    "descrizione": "Emette un cono di fuoco che infligge danni alle creature nell'area.",
    "danno": 18
  }
}
```

#### Esempio 6 -> Capacità Situazionale
##### Input D&D
```text
Attacco furtivo:
Infligge danni extra quando il bersaglio è colto alla sprovvista.
```

##### Output
```json
{
  "tipo": "Fisico",
  "categoria": "Attacco",
  "modalita": "Passivo",
  "effetto": "Bonus danno",
  "bersaglio": "Singolo",
  "risorsa": "Nessuna",
  "durata": "Istantaneo",
  "utilizzo": "Situazionale",

  "carta": {
    "nome": "Attacco furtivo",
    "descrizione": "Infligge danni aggiuntivi contro bersagli vulnerabili o impreparati.",
    "danno": 0
  }
}
```
----------------

# MODELLO DATI INTERMEDIO

il flusso non è D&D -> carta 

ma: 

D&D Monster
      |
      v
Monster Intermediate Representation
      |
      v
Card Object

in questo modo è estendibile


----------------

# SISTEMA DI GIOCO

## DESCRIZIONE DISCORSIVA
descrizione sommaria, esistono carte di vario tipo:

- CREATURA

- MOSSA

- OGGETTO


quindi il programma crea varie carte anche per lo stesso mostro, 
esempio il drago ha una carta creatura (che rappresenta i suoi valori)  
e delle carte mossa che rappreentano  (talenti, attacchi, qualità speciali,
 incantesimi e attacchi speciali) e poi può avere delle carte oggetto che 
rappresentano gli oggetti da lui posseduti.

quindi in questo gioco diciamo che ogni entità è un mazzo di carte.

## Sistema di gioco (bozza)
Concetto base
Ogni entità del gioco è rappresentata da un insieme di carte.
Un mostro, un personaggio o un'entità complessa non viene rappresentata da una singola carta,
ma da un mazzo personale composto da:
- una carta principale che definisce le caratteristiche base;
- carte abilità che rappresentano le azioni disponibili;
- carte oggetto che rappresentano equipaggiamento e possedimenti.

## Tipi di carta
Carta CREATURA -> definisce chi è la creatura.
Rappresenta l'entità principale.
Contiene: valori generali della creatura e Risorse disponibili

Carta MOSSA -> Rappresenta una capacità utilizzabile dalla creatura.
Una mossa può derivare da:
- attacco naturale
- talento
- capacità speciale
- qualità speciale
- incantesimo
- capacità magica
- capacità di classe

### Esempi 
MOSSA

Morso

Tipo: Fisico
Categoria: Attacco
Utilizzo: Illimitato

Effetto:
Infligge 3 danni a un bersaglio singolo.

---

MOSSA

Arma a soffio

Tipo: Magico
Categoria: Attacco

Utilizzo:
Limitato

Effetto:
Infligge 18 danni ad area.

---



Carta OGGETTO -> Rappresenta un oggetto posseduto o equipaggiato.
Può derivare da:
- armi
- armature
- oggetti magici
- tesori
- equipaggiamento

### Esempi 

OGGETTO

Spada infuocata

Tipo:
Arma

Effetto:
+2 danni da fuoco agli attacchi fisici.

---

## STRUTTURA DI UN ENTITÀ 
esempio Drago 

MAZZO DEL DRAGO

[CARTA CREATURA]

Drago Rosso


[CARTE MOSSA]

Morso
Artiglio
Coda
Arma a soffio
Presenza terrificante
Incantesimi


[CARTE OGGETTO]

Corona del drago
Tesoro antico
Amuleto magico

## FILOSOFIA DEL GIOCO SEMPLIFICATA

Il sistema separa:
- Identità = Carta creatura: "Che cosa sei?"
- Azioni = Carte mossa: "Che cosa puoi fare?"
- Personalizzazione = Carte oggetto: "Che cosa possiedi?"

## PIPELINE PER CREAZIONE ENTITÀ 

D&D / Pathfinder Database

        |
        v

Monster Parser

        |
        v

Entity Model

        |
        +----------------+----------------+
        |                |                |
        v                v                v

Carta Creatura       Carte Mossa     Carte Oggetto
        |                |                |
        +----------------+----------------+
                         |
                         v
                 Mazzo dell'entità

----------------

## NOTA FINALE SUL "BILANCIAMENTO"
- il bilanciamento richiede playtest,
metre questo sistema permette di mantenere una distribuzione coerente dei valori
e preservare il rapporto di potenza relativo

Il sistema garantisce:
- coerenza numerica
- proporzioni relative
- normalizzazione

----------------

## REGOLAMENTO
POIché il progetto principale è il motore di trasformazione, non il gioco.
Per portfolio terrei il gioco come:
"target representation"
cioè:
il formato finale generato dal motore.
il regolamento completo non è incluso per non deviare dal progetto

----------------

## IPOTESI DI STRUTTURA FINALE DEL PROGETTO

1. Obiettivo

2. Architettura generale

3. Pipeline dati

4. Modello intermedio

5. Algoritmi numerici
   - Vita
   - Corpo/Spirito
   - Armatura
   - Interpretazione
   - Risorse

6. Classificazione semantica LLM

7. Generazione carte

8. Sistema di entità e mazzi

9. Validazione umana

10. Limitazioni e scelte di design

----------------

#OGGETTI PRINCIPALI DEL PROGETTO

Ecco l'elenco completo, organizzato per fase della pipeline:

**1. Acquisizione dati**

- **RECORD DB (OGL)** — riga persistita nel DB SQL dopo lo scraping, prima del parsing

Scraping "dumb" — scarichi la pagina e basta, senza interpretarla: ID, URL, descrizione, contenuto grezzo (HTML/testo).
Questo è il RECORD DB: un contenitore generico, uguale per qualunque tipo di pagina (mostro, incantesimo, talento...).
Fatto per non sovraccaricare il server — una sola passata di scraping, poi lavoro in locale sui dati già salvati.

**2. Dati grezzi

- **SCHEDA D&D** — stat block grezzo scrapato da fonte D&D 3.5 (HTML/testo originale)
- **SCHEDA PF** — stat block grezzo scrapato da fonte Pathfinder 1E

-  **INCANTESIMO D&D** — stat block grezzo scrapato da fonte D&D 3.5 (HTML/testo originale)
-  **TALENTO D&D** — stat block grezzo scrapato da fonte D&D 3.5 (HTML/testo originale)
-  **EQUIP D&D** — stat block grezzo scrapato da fonte D&D 3.5 (HTML/testo originale)
-  **CLASSE D&D** — stat block grezzo scrapato da fonte D&D 3.5 (HTML/testo originale)

-  **INCANTESIMO PF** — stat block grezzo scrapato da fonte Pathfinder 1E
-  **TALENTO PF** — stat block grezzo scrapato da fonte Pathfinder 1E
-  **EQUIP PF** — stat block grezzo scrapato da fonte Pathfinder 1E
-  **CLASSE PF** — stat block grezzo scrapato da fonte Pathfinder 1E


**3. Parsing e struttura**

- **DATI STRUTTURATI** — output del parser: campi tipizzati (caratteristiche, DV, CA, abilità, attacchi grezzi...) pronti per essere smistati tra ramo numerico e ramo LLM

**4. Ramo numerico**

- **RISULTATO ALGORITMI NUMERICI** — output aggregato delle formule deterministiche (Vita, Corpo, Spirito, Armatura, Talismano, Interpretazione, Fiato, Magia) per una singola entità

**5. Ramo semantico (LLM)**

- **TEMPLATE PROMPT** — struttura del prompt inviato all'LLM per la classificazione di un singolo elemento (attacco, talento, qualità speciale, incantesimo)
- **RISPOSTA LLM** — output grezzo del classificatore, secondo lo schema fisso (tipo, categoria, modalità, effetto, bersaglio, risorsa, durata, utilizzo, confidence)

**6. Validazione**

- **RECORD DI VALIDAZIONE UMANA** — esito della revisione: stato (auto-approvato/corretto/rifiutato), valore originale vs corretto, note del validatore, timestamp

**7. Modello intermedio**

- **ENTITY MODEL (Rappresentazione Intermedia)** — oggetto che unifica risultato numerico + risposte LLM validate in un'unica rappresentazione dell'entità, indipendente dal formato di origine (D&D o PF) e dal formato di destinazione (carta); è il punto di estendibilità del sistema

**8. Oggetti di gioco**

- **CARTA CREATURA** — identità e valori base dell'entità
- **CARTA MOSSA** — singola capacità/azione (attacco, talento, incantesimo convertito)
- **CARTA OGGETTO** — equipaggiamento o possedimento
- **MAZZO ENTITÀ** — aggregato di una Carta Creatura + N Carte Mossa + N Carte Oggetto, rappresenta l'intera entità di gioco

**9. Template di rendering**

- **TEMPLATE CARTA CREATURA**
- **TEMPLATE CARTA MOSSA**
- **TEMPLATE CARTA OGGETTO**
- **TEMPLATE MAZZO ENTITÀ** — layout che compone le carte del mazzo in visualizzazione/stampa unificata

**10. Output finale**

- **CARTA RENDERIZZATA / EXPORT** — file finale generato (HTML pronto stampa → immagine), a valle del template, eventualmente versionato

**11. Tabelle di regole conversione**
**Dataclass generica + funzione condivisa** —  non JSON+Pydantic.

Perché funziona bene:
La dataclass resta pura struttura dati (nessuna logica dentro), quindi è facile da leggere, testare, 
ed estendere aggiungendo un elemento alla lista.
La funzione condivisa contiene tutta la logica una volta sola — se cambi la formula 
(es. arrotondamento per eccesso invece che per difetto), la cambi in un punto e si applica automaticamente
 a tutti i gruppi/caratteristiche.
Aggiungere una nuova caratteristica o un nuovo gruppo di interpretazione diventa "aggiungo una riga alla lista", zero nuovo codice.

Motivi, in sintesi di tutto il ragionamento fatto finora:

1. **Il JSON risolve un problema che non hai davvero.** Il vantaggio del JSON è "editabilità senza toccare Python",
ma sei tu il solo sviluppatore/bilanciatore — non c'è nessun altro attore per cui vale la pena pagare quel costo di indirezione.
2. **La maggior parte dei cambi che farai sono logica, non dati puri** (l'hai dimostrato tu stesso con l'esempio Costituzione/arrotondamento)
— quindi finiresti comunque ad aprire Python per la maggior parte delle modifiche, JSON o no.
3. **Una dataclass + una funzione condivisa ti dà il meglio**: struttura pulita, zero duplicazione di logica,
autocompletamento/type-check gratis, e "aggiungere una regola" diventa letteralmente aggiungere una riga a una lista.
4. **Si difende meglio in un colloquio**: mostra che hai scelto lo strumento più semplice che risolve il problema reale,
invece di aggiungere un livello di configurazione esterna "perché sembra più professionale" senza un bisogno concreto dietro.

Tienilo come principio generale per il resto del progetto: JSON/config esterna la introduci solo quando emerge un bisogno
reale di editabilità senza deploy (es. un domani un tool web per il playtest) — non come default.
Per ora, dataclass ovunque per queste tabelle.

###Ipotesi di dataclass

Corpo/Spirito
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class MappingCaratteristica:
    caratteristica_dnd: str
    attributo: str
    condizione: str | None = None  # es. "non_morto", per il caso Difesa/Destrezza

MAPPING_CORPO = [
    MappingCaratteristica("Forza", "Attacco"),
    MappingCaratteristica("Destrezza", "Velocità"),
    MappingCaratteristica("Costituzione", "Difesa"),
    MappingCaratteristica("Destrezza", "Difesa", condizione="non_morto"),
]

MAPPING_SPIRITO = [
    MappingCaratteristica("Intelligenza", "Potere"),
    MappingCaratteristica("Saggezza", "Tangenza"),
    MappingCaratteristica("Carisma", "Spin"),
]

def calcola_attributo(mod_caratteristica: int) -> int:
    return max(0, mod_caratteristica)  # modificatori negativi valgono 0

def calcola_corpo_spirito(mappings: list[MappingCaratteristica], caratteristiche: dict[str, int], is_non_morto: bool = False) -> dict[str, int]:
    risultato = {}
    for m in mappings:
        if m.condizione == "non_morto" and not is_non_morto:
            continue
        if m.condizione is None and is_non_morto and any(x.condizione == "non_morto" and x.attributo == m.attributo for x in mappings):
            continue  # la variante non morto sostituisce quella base
        risultato[m.attributo] = calcola_attributo(caratteristiche[m.caratteristica_dnd])
    return risultato
```

Interpretazione — stessa idea, con un gruppo invece di un singolo mapping:
```python 
@dataclass(frozen=True)
class GruppoInterpretazione:
    nome: str
    caratteristica_riferimento: str
    abilita: list[str]

GRUPPI_INTERPRETAZIONE = [
    GruppoInterpretazione("Atletica", "Forza", ["Acrobazia", "Nuotare", "Scalare", ...]),
    GruppoInterpretazione("Empatia", "Carisma", ["Diplomazia", "Intimidire", ...]),
    GruppoInterpretazione("Percezione", "Saggezza", ["Ascoltare", "Cercare", "Osservare"]),
    # ...
]

def calcola_interpretazione(gruppo: GruppoInterpretazione, valori_abilita: dict[str, int], mod_caratteristiche: dict[str, int]) -> int:
    mod_rif = mod_caratteristiche[gruppo.caratteristica_riferimento]
    if mod_rif < 0:
        return 0

    mod_car = max(0, mod_rif)
    valori_calcolati = []
    for nome_abilita in gruppo.abilita:
        val = valori_abilita.get(nome_abilita, 0)
        risultato = mod_car if val == 0 else val - mod_car - 3
        if risultato != 0:
            valori_calcolati.append(risultato)

    if not valori_calcolati:
        return 0
    return math.floor(sum(valori_calcolati) / len(valori_calcolati))
```

