# MonsterForge — Pipeline Architecture

Questo documento fissa la pipeline completa di conversione, dal testo grezzo
scrapato fino alla carta renderizzata, e le decisioni architetturali prese
per arrivarci. Integra e rende esplicito quanto già descritto in `DESIGN.md`,
aggiungendo il livello di dettaglio emerso durante lo sviluppo di
`structured_data/`.

## Perché questo documento

Durante lo sviluppo di `structured_data/dnd/v3x/` sono emerse alcune domande
su dove collocare esattamente la classificazione LLM rispetto al parsing
deterministico, e se servisse un ulteriore livello di dati grezzi tra
l'HTML e `structured_data/`. Questo documento fissa le risposte raggiunte,
così da poterle riconsultare quando si scriverà `parsing/` e `llm/`.

---

## Schema completo della pipeline

```
┌───────────────────────────────────────────────────────────────────┐
│  1. RAW HTML                                                      │
│     Scaricato da scraping/, salvato as-is in db/ (RECORD DB)      │
│     Tabella generica unica: id, url, tipo, contenuto grezzo       │
└───────────────────────────────────────────────────────────────────┘
                              |
                              v
┌──────────────────────────────────────────────────────────────────────────┐
│  2a. HTML EXTRACTION  →  parsing/<sistema>/<versione>/html_extraction.py │
│      Regex / BeautifulSoup, deterministico, per-fonte se serve           │
│                                                                          │
│      Estrae i campi così come appaiono nella tabella del manuale,        │
│      quasi letteralmente, in una dataclass "raw fields" dedicata:        │
│                                                                          │
│      RawArmorFields(name="...", cost="30 gp", armor_bonus="2", ...)      │
└──────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌──────────────────────────────────────────────────────────────────────────┐
│  2b. RAW FIELDS  →  parsing/<sistema>/<versione>/raw_fields.py           │
│      Dataclass "aderenti al dominio di provenienza": rispecchiano        │
│      le colonne esatte delle tabelle di gioco (Armor, Weapons, ecc.)     │
│      Campi ancora in gran parte stringhe, non ancora tipizzati/enum      │
│                                                                          │
│      Punto di convergenza multi-fonte: fonti HTML diverse (siti diversi) │
│      o input umano manuale (CLI/form) producono la STESSA RawFields      │
│      Punto di bypass: se serve solo testare la pipeline, si costruisce   │
│      un RawFields a mano, senza scraping né rete                         │
└──────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  3. STRUCTURED CONVERSION  →  parsing/<sistema>/<versione>/structured_conversion.py │
│     Cast di tipo (stringa → int/enum/dataclass) + decisione:                        │
│     "serve classificazione semantica o l'oggetto è già completo?"                   │
│                                                                                     │
│     ├─► Campi/oggetti semplici (solo numeri/enum, nessun testo libero)              │
│     │   → direttamente in structured_data, nessuna chiamata LLM                     │
│     │                                                                               │
│     └─► Campi con testo libero da interpretare (abilità, talenti, incantesimi)      │
│         → passano allo stadio 4 prima di poter essere costruiti                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌────────────────────────────────────────────────────────────────────────────────────┐
│  4. LLM CLASSIFICATION  →  llm/                                                    │
│     SOLO per blocchi di testo libero (special qualities, special                   │
│     attacks, feats, spells) che non sono riducibili a regex                        │
│                                                                                    │
│     Una singola chiamata per blocco di testo, con schema di output fisso           │
│     (Pydantic/dataclass): categoria, bersaglio, durata, utilizzo, E i              │
│     valori numerici già classificati nel campo semanticamente corretto             │
│     (es. "1d4" va in Damage se è danno, in EffectGrant se è una quantità           │
│     evocata — la distinzione avviene nella stessa chiamata, non in due)            │
│                                                                                    │
│     Output include un campo "confidence" (transitorio, non finisce mai nel domain) │
└────────────────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌───────────────────────────────────────────────────────────────────────┐
│  5. VALIDATION  →  validation/                                        │
│     confidence >= soglia (0.7) → auto-approvato                       │
│     confidence <  soglia       → coda per revisione umana (ui/)       │
│                                                                       │
│     Storicizza correzioni; l'output finale non porta più "confidence" │
└───────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌───────────────────────────────────────────────────────────────────────┐
│  6. STRUCTURED_DATA  →  structured_data/<sistema>/<versione>/         │
│     Ora il Creature/Item/CharacterClass è completo: alcuni campi      │
│     costruiti in stadio 3 (regex diretta), altri in stadio 4+5 (LLM + │
│     validazione). Tipizzato, enum-based, zero stringhe grezze residue │
└───────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌────────────────────────────────────────────────────────────────────────────────┐
│  7. TRANSFORMATION  →  transformation/ + rules/                                │
│     Calcoli deterministici, zero LLM, zero ambiguità:                          │
│     calcola_vita(), calcola_corpo_spirito(), calcola_interpretazione(),        │
│     calcola_armatura_talismano(), calcola_fiato_magia()                        │
│                                                                                │
│     Il contenuto già classificato (stadio 4/5) viene qui mappato 1:1 nei       │
│     campi/enum del domain (MoveCard, ItemCard) — nessuna nuova interpretazione │
└────────────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌─────────────────────────────────────────────────────────────────────────┐
│  8. DOMAIN MODEL  →  domain/                                            │
│     Entity(creature_cards, move_cards, item_cards)                      │
│     Rappresentazione finale, indipendente dalla fonte (D&D o Pathfinder)│
└─────────────────────────────────────────────────────────────────────────┘
                              |
                              v
┌───────────────────────────────────────────────────────────────────┐
│  9. SERIALIZATION  →  serialization/                              │
│     Domain Model → struttura esterna comune (dict JSON-compatible)│
│     Le carte referenziate (es. MoveCard.cards_to_add) vengono qui │
│     ridotte a {"name", "id"} — vedi decisione 6 sotto sul perché  │
└───────────────────────────────────────────────────────────────────┘
                              |
              +---------------+---------------+
              v                               v
┌───────────────────────────────┐  ┌───────────────────────────────────┐
│  10a. API  →  api/             │  │  10b. RENDERING  →  rendering/    │
│      dict → HTTP response      │  │      dict → HTML → immagine       │
│      (JSON)                    │  │      stampabile (carta finale)    │
└───────────────────────────────┘  └───────────────────────────────────┘
```

---

## Decisioni chiave e motivazioni

### 1. Perché serve un livello "raw fields" tra HTML e structured_data

**Problema**: convertire direttamente da HTML a `structured_data` accoppia
la logica di interpretazione/calcolo alla fragilità del formato sorgente
(HTML che cambia da sito a sito, o nel tempo).

**Soluzione**: un livello intermedio di dataclass ("raw fields"), che
rispecchia fedelmente le tabelle del manuale (es. le colonne esatte della
tabella Armature: nome, costo, bonus, penalità...), con campi ancora in
gran parte stringhe.

**Vantaggi ottenuti**:
- **Multi-fonte**: fonti HTML diverse convergono sulla stessa `RawFields`
  prima di ogni interpretazione — basta scrivere un `html_extraction.py`
  diverso per fonte, il resto della pipeline non cambia.
- **Input manuale**: un utente può compilare a mano (CLI o form futuro)
  la stessa struttura `RawFields`, bypassando lo scraping e ottenendo
  comunque una carta.
- **Testing senza rete**: l'intera pipeline (structured_data →
  transformation → domain → rendering) è testabile con `RawFields`
  scritti a mano, senza scraping reale né dipendenza da BeautifulSoup.
- **Skip LLM quando possibile**: oggetti semplici (solo campi numerici,
  nessun testo libero da interpretare) passano da `RawFields` a
  `structured_data` con solo cast di tipo, senza mai passare per `llm/`.

**Dove vive**: dentro `parsing/`, non come pacchetto a sé stante. Non è un
nuovo stadio architetturale visibile dall'esterno — è un dettaglio di
*come* `parsing/` fa il proprio lavoro in due passi invece di uno.

**Perché non è una tabella di database**: valutata e scartata l'idea di
persistere questo stadio come tabella SQL. Motivi: (1) richiederebbe
comunque una rappresentazione tipizzata in Python per essere letta/scritta
— il DB non "evita" le dataclass, sposta solo la stessa complessità sopra
una persistenza in più; (2) introdurrebbe tabelle diverse per tipo di stat
block, contraddicendo la scelta già presa per `RECORD DB` di usare una
tabella generica unica con un campo "tipo"; (3) questo stadio è economico
da rigenerare (pura CPU, nessuna rete) ogni volta che serve, ripartendo
dall'HTML già in cache in `db/` — non c'è un vero bisogno di persisterlo.

### 2. Perché non un "JSON intermedio" come stadio a sé

Durante la discussione iniziale era emerso uno schema con un passaggio
`HTML → JSON → structured_data`. Questo JSON non rappresenta un vero
stadio architetturale con le sue regole: è solo il modo interno in cui una
libreria di parsing (es. BeautifulSoup) restituisce dati prima che
vengano tipizzati. Non ha bisogno di essere un modulo a sé, né di essere
persistito: è variabile locale di lavoro dentro `html_extraction.py`.

### 3. Dove si inserisce l'LLM, esattamente

L'LLM entra in gioco **solo** per blocchi di testo libero che descrivono
abilità (special qualities, special attacks, feats, spells) — mai per
campi con formato fisso e prevedibile (Hit Dice, Armor Class, Saves,
Abilities), che restano risolti con regex deterministica.

Un punto importante emerso in discussione: la classificazione della
categoria semantica (es. "è un attacco" vs "è una cura") e l'estrazione
dei valori numerici presenti nello stesso testo (es. "1d4") avvengono
**nella stessa chiamata LLM**, non in due passaggi separati. Il motivo:
capire *cosa rappresenta* un numero nel contesto (danno? quantità
evocata? bonus?) richiede la stessa comprensione semantica necessaria per
classificare l'abilità nel suo complesso — separarle in due passaggi
distinti non avrebbe portato benefici, solo una chiamata in più.

### 4. Perché `CreatureModifier` (e concetti simili) usano composizione, non ereditarietà

Non tutte le "varianti" di un concetto meritano una sottoclasse. Il
criterio adottato in tutto `structured_data/`: se una categoria rappresenta
un **delta/modificatore** applicato sopra un oggetto base (es. un
archetipo come Licantropia applicato a una Creature), si usa composizione
(campi separati per override/additive/modifier), non ereditarietà — perché
l'oggetto non è realmente un caso speciale del genitore, non ne condivide
l'intera identità strutturale.

Quando invece la relazione è una vera specializzazione (es.
`PrestigeClass(CharacterClass)`, che è a tutti gli effetti una classe
completa con in più dei prerequisiti), l'ereditarietà resta la scelta
corretta.

### 5. Quando estrarre un modulo condiviso vs tenere i campi locali

Criterio adottato ogniqualvolta la stessa struttura dati (es. `Damage`,
componenti di `effect_mechanics.py`) serve a più moduli indipendenti
(attacchi, qualità speciali, incantesimi, oggetti, talenti): si estrae in
un modulo condiviso, non si duplica. Il test pratico usato: *"sto
duplicando la stessa cosa, o ho due cose diverse che appartengono alla
stessa categoria concettuale?"* — nel primo caso un modulo condiviso con
una classe sola; nel secondo, un modulo condiviso con più classi
correlate (come `creature_stats.py` o `effect_mechanics.py`).

### 6. Perché le carte referenziate restano ridotte a nome/id anche nel rendering

Con l'introduzione dell'interfaccia HTTP (`api/` + `serialization/`), ci si
è chiesti se la pipeline dovesse biforcarsi subito dopo `domain/` in due
conversioni indipendenti (una per `api/`, una per `rendering/`), oppure
convergere prima su un unico stadio `serialization/` condiviso da
entrambi. In particolare, se la riduzione delle carte annidate (es.
`MoveCard.cards_to_add`) a `{"name", "id"}` fosse un compromesso
specifico del trasporto di rete, da evitare per il rendering (che
potrebbe sembrare avere bisogno del dettaglio completo per disegnare la
carta).

**Non lo è.** Il formato fisico delle carte di questo gioco è a
dimensione standard (stile Magic, circa 63×88mm) — non c'è spazio per
riportare per intero i campi di più carte referenziate dentro la carta
che le referenzia; anche una sola carta annidata espansa per intero
renderebbe la carta ingestibile. La carta referenziata (es. "Trip")
esiste già come carta a sé nel mazzo, con il proprio rendering — la
carta che la referenzia deve solo poterla nominare, non riprodurne il
contenuto.

La riduzione a nome/id è quindi la rappresentazione corretta di
"riferimento a un'altra carta del mazzo" in questo sistema, dettata dal
formato fisico della carta prima ancora che dall'API — il vincolo di
spazio stampato è più stringente e più a monte di quello di payload di
rete, e vale ovunque una carta ne referenzia un'altra, non solo al
confine HTTP.

**Conseguenza**: `serialization/` resta un unico stadio condiviso da
`api/` e `rendering/` — la biforcazione avviene dopo quello stadio, non
prima.

---

## Cosa NON cambia rispetto a `DESIGN.md`

Questo documento aggiunge dettaglio, non sostituisce le decisioni fondanti
già fissate in `DESIGN.md`:
- La separazione deterministico (`rules/`+`transformation/`) vs
  probabilistico (`llm/`) resta invariata.
- Il principio "dataclass ovunque, non JSON/Pydantic esterno per la
  configurazione" resta invariato.
- Il flusso generale `RPG Data → Entity Model → Cards` resta invariato;
  questo documento ne dettaglia solo gli stadi interni di `parsing/`.

---

### Nota: StatBlock/CreatureBuild aggregator (non implementato)

Valutata la necessità di un aggregatore per personaggi multiclasse con
archetipi (es. "bugbear, thief 5, wizard 2, half-fiend"). Rimandato:
il contenuto scrapabile dai tre manuali base è quasi interamente
rappresentato da Creature singola. Da rivalutare solo se il progetto
si estende a NPC/moduli avventura con costruzioni multiclasse.