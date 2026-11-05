# PLAN.md — Bookpack: libri condensati in pillole, da telefono

> Documento di progetto da dare a Claude Code. Descrive intento, architettura, feature, contratti dati e milestone.
> Lavora **una milestone alla volta**, nell'ordine indicato, e rispetta i criteri di accettazione di ciascuna prima di passare alla successiva.

---

## 1. Intento e obiettivo

**Problema.** Leggere un saggio o un manuale prolisso richiede tempo e concentrazione che da telefono, nei ritagli di tempo, non ci sono. Molti libri ripetono le stesse idee per pagine.

**Obiettivo.** Trasformare un PDF in un **percorso di lettura condensato**, diviso per capitoli. Ogni capitolo diventa una breve sessione di circa 5 minuti fatta di:
- **card** a scorrimento, una idea per card;
- una **mindmap** del capitolo come ripasso visivo;
- poche **flashcard** finali per verificare cosa si è trattenuto.

Il **progresso viene salvato**, così si riprende sempre dal punto esatto.

**Principi guida**
- **Mobile-first**: l'esperienza principale è su telefono, con una mano, in sessioni brevi.
- **App statica, niente backend**: il lettore è una PWA statica che funziona offline. Tutta l'AI sta nel generatore.
- **Contratto dati esplicito**: generatore e lettore comunicano solo tramite il file *book pack*, validato da uno schema JSON condiviso.
- **Fedeltà alla fonte**: ogni card riporta la pagina di origine. La condensazione non deve inventare.
- **Rigenerabile**: migliorare i prompt e rigenerare un libro non richiede modifiche all'app.

**Default di prodotto** (decisi, modificabili in futuro)
- Il target sono **saggistica e manualistica**. La narrativa è fuori scope per l'MVP.
- Il **percorso è libero**: tutti i capitoli sono accessibili e l'app suggerisce il "prossimo" in ordine. Non ci sono blocchi.
- La lingua di output è uguale a quella del libro, oppure forzata con `--lang`.

---

## 2. Architettura

Un monorepo con due progetti separati e uno schema condiviso:

```
bookpack/
├── PLAN.md
├── README.md
├── schema/
│   └── bookpack.schema.json        # generato dai modelli Pydantic — fonte di verità
├── generator/                      # Python — produttore (PDF → book pack)
├── web/                            # Nuxt — lettore (PWA statica)
└── samples/                        # PDF di pubblico dominio + pack generato d'esempio
```

```
 PDF ──► [generator CLI] ──► libro.bookpack.json ──► [web PWA] ──► IndexedDB (libro + progresso)
                 ▲                      │
          LLM provider            validato da schema/bookpack.schema.json
```

- I **modelli Pydantic** in `generator/` sono la fonte di verità del formato.
- `bookpack schema` esporta `schema/bookpack.schema.json`.
- `web/` genera i tipi TypeScript da quello schema con `json-schema-to-typescript` e lo usa per validare i pack importati (con Ajv o Zod generato).
- Se lo schema cambia si incrementa `schemaVersion`. L'app rifiuta con un messaggio chiaro le versioni che non supporta.

---

## 3. Formato *book pack* (v1)

File `*.bookpack.json`. Struttura logica:

```jsonc
{
  "schemaVersion": 1,
  "generator": { "version": "0.1.0", "model": "claude-…", "generatedAt": "ISO-8601" },
  "book": {
    "id": "slug-o-hash-stabile",
    "title": "…",
    "author": "…",
    "lang": "it",
    "sourcePages": 312,
    "coverColor": "#1f6feb"          // opzionale, per la UI
  },
  "overview": {
    "summary": "5–8 frasi sul libro intero",
    "keyIdeas": ["…", "…"],          // 3–7 idee portanti
    "mindmap": "# Titolo\n## Cap 1\n- …"   // markdown per markmap
  },
  "chapters": [
    {
      "id": "ch-01",
      "index": 1,
      "title": "…",
      "pageStart": 12,
      "pageEnd": 34,
      "estMinutes": 5,
      "tldr": "una frase",
      "cards": [
        { "id": "ch-01-c01", "type": "concept",    "title": "…", "body": "…", "page": 14 },
        { "id": "ch-01-c02", "type": "definition", "title": "…", "body": "…", "page": 15 },
        { "id": "ch-01-c03", "type": "example",    "body": "…", "page": 18 },
        { "id": "ch-01-c04", "type": "quote",      "body": "citazione breve", "page": 20 },
        { "id": "ch-01-c05", "type": "takeaway",   "body": "…" }
      ],
      "mindmap": "# Cap 1\n## …\n- …",
      "flashcards": [
        { "id": "ch-01-f01", "q": "…", "a": "…", "page": 14 }
      ]
    }
  ],
  "glossary": [ { "term": "…", "definition": "…", "chapterId": "ch-03" } ]   // opzionale
}
```

**Vincoli (validati dal generatore)**
- `cards` contiene da 5 a 12 elementi per capitolo, e l'ultima card è sempre di tipo `takeaway`.
- `body` è lungo al massimo circa 60 parole, così ogni card si legge in 20–40 secondi. `title` ha al massimo circa 8 parole.
- `quote` contiene al massimo 25 parole, ed è al massimo una per capitolo.
- `flashcards` contiene da 3 a 5 elementi per capitolo.
- Le mindmap sono markdown gerarchico (heading e liste), con profondità massima 4 e circa 25 nodi per capitolo.
- Tutti gli `id` sono stabili e deterministici, perché il progresso li usa come chiave: rigenerando lo stesso libro, gli id dei capitoli non devono cambiare.

---

## 4. Generator (Python)

### Stack
- **uv** per ambiente e dipendenze, Python ≥ 3.12.
- **PyMuPDF** (`pymupdf`) per testo, outline/TOC e numeri di pagina.
- **Pydantic v2** per modelli, validazione ed export dello schema.
- **Typer** per la CLI e **Rich** per output e progress bar.
- **LLM**: un'astrazione `LLMProvider` con output strutturato (JSON validato da Pydantic).
  - Implementazioni: `anthropic` (default) e `openai_compat`, che copre OpenAI, Ollama e LM Studio tramite base URL.
  - Configurazione da `.env` (`BOOKPACK_PROVIDER`, `BOOKPACK_MODEL`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`). Va fornito un `.env.example`.
- **tiktoken** o un'euristica (caratteri/4) per stimare i token.
- **pytest** per i test e **ruff** per lint e format.

### Struttura
```
generator/
├── pyproject.toml
├── .env.example
├── src/bookpack/
│   ├── cli.py                 # comandi Typer
│   ├── models.py              # modelli Pydantic del book pack (fonte di verità)
│   ├── config.py
│   ├── extract/
│   │   ├── pdf.py             # lettura pagine + testo
│   │   ├── toc.py             # rilevamento capitoli
│   │   └── clean.py           # pulizia testo
│   ├── condense/
│   │   ├── chunking.py
│   │   ├── chapter.py         # pipeline per capitolo
│   │   ├── book.py            # overview, mindmap globale, glossario
│   │   └── prompts/           # prompt in file .md versionati
│   ├── llm/
│   │   ├── base.py
│   │   ├── anthropic.py
│   │   └── openai_compat.py
│   ├── validate.py            # vincoli oltre lo schema (lunghezze, conteggi)
│   └── cache.py               # cache su disco delle risposte LLM
└── tests/
```

### Comandi CLI
| Comando | Cosa fa |
|---|---|
| `bookpack inspect libro.pdf` | Senza LLM. Mostra i metadati e i capitoli rilevati (titolo, pagine, parole stimate) e la stima di token e costo. Serve a verificare la divisione prima di spendere. |
| `bookpack toc libro.pdf -o libro.toc.yaml` | Esporta la divisione rilevata in YAML, da correggere a mano. |
| `bookpack build libro.pdf [-o out.bookpack.json] [--toc libro.toc.yaml] [--chapters 1-3] [--lang it] [--model …] [--yes]` | Genera il pack. Prima di partire mostra la stima del costo e chiede conferma, salvo `--yes`. |
| `bookpack validate out.bookpack.json` | Valida contro schema e vincoli. |
| `bookpack schema [-o ../schema/bookpack.schema.json]` | Esporta lo schema JSON. |

### Pipeline di `build`
1. **Estrazione**: testo per pagina, con il numero di pagina conservato.
2. **Rilevamento capitoli**, in ordine di preferenza:
   1. un file `--toc` fornito dall'utente;
   2. l'outline del PDF (`doc.get_toc()`), usando il livello che produce un numero ragionevole di capitoli (da 3 a 60);
   3. euristiche sui titoli (font più grande o grassetto, pattern come "Capitolo N" o "Chapter N", righe brevi isolate);
   4. come fallback, l'LLM sulle prime pagine (indice testuale) e un campione di pagine.
   - Le sezioni non utili (copertina, copyright, indice, ringraziamenti, bibliografia, indice analitico) vanno escluse, con un flag per includerle.
3. **Pulizia**: rimozione di header e footer ripetuti (righe uguali su più pagine), numeri di pagina, sillabazione a fine riga (`para-\nola` → `parola`) e spazi multipli.
4. **Condensazione per capitolo** (map-reduce):
   - se il capitolo entra nel budget di contesto, va in un'unica chiamata;
   - altrimenti si divide in chunk di circa 3–4k token con overlap. Ogni chunk produce note dense con le pagine, e una chiamata finale ricava dalle note le card, la mindmap e le flashcard.
   - L'output è JSON strutturato e validato. Se la validazione fallisce, si ritenta fino a 2 volte passando l'errore all'LLM.
5. **Livello libro**: overview, idee portanti, mindmap globale e glossario, ricavati dalle sintesi dei capitoli (non dal testo intero).
6. **Validazione finale** e scrittura del file.

**Cache e ripresa**: ogni chiamata LLM viene salvata in cache su disco con chiave `hash(prompt + input + modello)`. Se `build` si interrompe, rilanciarlo riprende senza ripagare le chiamate già fatte.

### Regole di condensazione (da mettere nei prompt)
- Una idea per card. Niente card riempitive né ripetizioni tra card.
- Riscrivere con parole proprie e in modo diretto: niente "l'autore dice che…", meglio enunciare l'idea.
- **Non inventare**: solo ciò che è nel testo. Ogni card e flashcard porta la `page` di origine.
- Preferire concetti, definizioni, meccanismi, esempi concreti e implicazioni pratiche. Saltare aneddoti ridondanti e digressioni.
- L'ultima card (`takeaway`) risponde a "cosa mi porto via da questo capitolo".
- Le flashcard sono domande di richiamo attivo, non domande sì/no, con risposte brevi.
- Si scrive nella lingua di output indicata.

### Test minimi
- Rilevamento dei capitoli su un PDF di esempio con outline e su uno senza.
- Pulizia: rimozione di header e footer e gestione della sillabazione.
- Validazione: un pack valido passa, mentre falliscono pack con troppe card, `body` troppo lungo o id duplicati.
- Provider LLM finto (mock) per testare la pipeline end-to-end senza rete.

---

## 5. Web (Nuxt) — lettore PWA

### Stack
- **Nuxt** (ultima major stabile) con `ssr: false`, build statica tramite `nuxt generate`.
- **Nuxt UI** (ultima major) con **Tailwind CSS 4**.
- **@vite-pwa/nuxt** per installabilità e funzionamento offline.
- **Dexie** per IndexedDB (libri e progresso).
- **markmap-lib** e **markmap-view** per le mindmap.
- Carousel per le card: usa `UCarousel` di Nuxt UI (basato su Embla) se basta, altrimenti Embla direttamente.
- Validazione dei pack importati con lo schema JSON condiviso (Ajv) e tipi generati da `schema/bookpack.schema.json`.
- Package manager **pnpm**. Lint con `@nuxt/eslint`.
- Deploy su **GitHub Pages**, con base URL configurabile.

### Pagine e flussi
| Route | Contenuto |
|---|---|
| `/` | **Libreria**: griglia o lista dei libri con titolo, autore, colore, barra di progresso e "ultimo aperto". In cima c'è la CTA **"Riprendi"**, che riporta all'ultimo libro, capitolo e card. Se la libreria è vuota, mostra lo stato vuoto con il pulsante per importare e un link al pack d'esempio. |
| `/import` | Importa da **file** (file picker o drag&drop) o da **URL**. Valida il pack e mostra un'anteprima (titolo, numero di capitoli, minuti totali) prima di salvarlo. Se il libro è già presente (stesso `book.id`), chiede se aggiornarlo mantenendo il progresso. |
| `/book/[bookId]` | **Percorso**: header con titolo, overview comprimibile e idee portanti. Sotto, i capitoli come tappe verticali, ognuna con stato (da iniziare, in corso con "card 4/9", completato), `tldr` e minuti stimati. Il prossimo capitolo suggerito è evidenziato. Ci sono anche il link alla mindmap globale e al glossario, se presente. |
| `/book/[bookId]/ch/[chId]` | **Sessione capitolo** a schermo intero, in tre fasi: **card**, poi **mindmap**, poi **flashcard**. Barra di avanzamento in alto. Si passa da una card all'altra con swipe o con tap sui bordi. La posizione viene salvata a ogni card. Alla fine, una schermata di completamento con "prossimo capitolo" o "torna al percorso". |
| `/book/[bookId]/map` | Mindmap globale del libro, con zoom e pan. Toccare il nodo di un capitolo porta a quel capitolo. |
| `/settings` | Tema chiaro/scuro/sistema, dimensione del font delle card, export/import del progresso (JSON), eliminazione di un libro, azzeramento del progresso. |

### Dettagli UX
- **Card**: occupano quasi tutto lo schermo e hanno uno stile per tipo (colore o icona per concept, definition, example, quote e takeaway). La tipografia è ampia e leggibile. La pagina di origine è indicata discretamente ("p. 14").
- **Flashcard**: la domanda è sul fronte e un tap la gira. Due pulsanti, **"Lo sapevo"** e **"Da ripassare"**, registrano l'esito.
- **Mindmap su mobile**: si adatta allo schermo all'apertura, con pinch-zoom e pan. I nodi oltre il secondo livello sono comprimibili.
- La sessione si può interrompere in qualsiasi punto e riprende alla card esatta.
- Tutto funziona **offline** dopo il primo caricamento e l'import del libro.
- Navigazione da tastiera (frecce) per l'uso desktop.

### Modello dati locale (Dexie)
```ts
books:    { id, pack /* BookPack */, importedAt, updatedAt }
progress: {
  bookId,
  currentChapterId,
  lastOpenedAt,
  chapters: Record<chapterId, {
    phase: 'cards' | 'mindmap' | 'flashcards' | 'done',
    lastCardIndex: number,
    completedAt?: string,
    flashResults: Record<flashcardId, { known: boolean, at: string }>
  }>
}
settings: { key, value }
```
- L'export del progresso produce un unico JSON con `progress` e `settings` (i libri si reimportano dai pack). L'import fonde i dati o li sostituisce, a scelta.
- Il progresso è indicizzato per `id` di capitoli e card, che sono stabili. Se un pack aggiornato perde degli id, il loro progresso viene ignorato senza errori.

### Struttura suggerita
```
web/
├── nuxt.config.ts
├── app/
│   ├── pages/            # route sopra
│   ├── components/
│   │   ├── book/         # BookCard, ChapterStep, OverviewPanel
│   │   ├── session/      # CardDeck, ConceptCard, MindmapView, FlashcardDeck, SessionComplete
│   │   └── common/
│   ├── composables/      # useLibrary, useProgress, useSession, useImport
│   ├── db/               # schema Dexie
│   ├── types/            # tipi generati dallo schema
│   └── utils/validatePack.ts
└── public/samples/       # pack d'esempio
```

---

## 6. Milestone

### M0 — Setup monorepo
- Struttura delle cartelle, README con istruzioni per entrambi i progetti, `.gitignore`, `.env.example`.
- `generator/` con uv, ruff, pytest e una CLI Typer vuota.
- `web/` con Nuxt, Nuxt UI, Tailwind 4 e una pagina placeholder. `pnpm generate` funziona.
- **Accettazione**: entrambi i progetti si installano e si avviano con i comandi del README.

### M1 — Schema e modelli
- Modelli Pydantic completi in `models.py`, vincoli in `validate.py`, comandi `bookpack schema` e `bookpack validate`.
- Un pack d'esempio scritto a mano (2 capitoli) in `samples/`.
- Tipi TS generati in `web/` da `schema/bookpack.schema.json`, con uno script `pnpm gen:types`.
- **Accettazione**: il pack d'esempio passa `validate` e la validazione lato web. I test sui vincoli passano.

### M2 — Estrazione (senza LLM)
- Estrazione, rilevamento capitoli, pulizia, comandi `inspect` e `toc`, override con `--toc`.
- **Accettazione**: `inspect` su un PDF di Project Gutenberg mostra capitoli corretti. I test di estrazione e pulizia passano.

### M3 — Condensazione
- Provider LLM (Anthropic e OpenAI-compatible), prompt in file, pipeline map-reduce, retry con validazione, cache, stima dei costi con conferma, livello libro.
- **Accettazione**: `build --chapters 1-2` produce un pack valido. Rilanciare dopo un'interruzione usa la cache. Il test end-to-end con provider finto passa.

### M4 — Web: libreria, import, percorso
- Dexie, import da file e URL con validazione e anteprima, libreria, pagina del percorso con overview e capitoli.
- **Accettazione**: importando il pack d'esempio si vedono il libro in libreria e il percorso completo. Un pack non valido mostra un errore comprensibile.

### M5 — Web: sessione capitolo
- Card deck con swipe, mindmap del capitolo, flashcard con esito, schermata di completamento, mindmap globale.
- **Accettazione**: si completa un capitolo dall'inizio alla fine da un viewport mobile (390px), sia con swipe sia con i tap.

### M6 — Progresso, PWA, rifiniture
- Salvataggio della posizione a ogni card, "Riprendi" in home, stati dei capitoli nel percorso, export/import del progresso, impostazioni, PWA installabile e offline, deploy su GitHub Pages.
- **Accettazione**: chiudendo l'app a metà capitolo e riaprendola, si torna alla card esatta. L'app funziona offline in modalità aereo. Il Lighthouse PWA è soddisfatto.

### M7 — Esempio reale e documentazione
- Un pack generato da un libro di **pubblico dominio** (Project Gutenberg) incluso in `web/public/samples/`. README con workflow completo, screenshot e note sui costi.

---

## 7. Roadmap dopo l'MVP (non implementare ora)
- **Ripetizione spaziata** (FSRS) su tutte le flashcard dei libri, con una vista "Ripasso di oggi".
- **Card salvate** o evidenziate, raccolte in una vista unica per libro.
- **Generazione nel browser** con l'API key dell'utente (parsing PDF via pdf.js), per non usare la CLI.
- **Livelli di condensazione** (rapido o approfondito) nello stesso pack.
- Supporto **EPUB** nel generatore (ebooklib).
- Sintesi vocale delle card, streak e statistiche di lettura.

---

## 8. Vincoli e note per Claude Code
- Non committare mai API key. Usa `.env` (in gitignore) e `.env.example`.
- I prompt LLM stanno in file `.md` in `condense/prompts/`, non hardcoded nel codice.
- Lo schema JSON in `schema/` è **generato**: non modificarlo a mano. Si cambiano i modelli Pydantic e poi si rilancia `bookpack schema`.
- Nel repo vanno solo libri e pack di **pubblico dominio**. I pack generati da libri sotto copyright sono per uso personale e vanno in una cartella in gitignore (es. `generator/out/`).
- Se una scelta tecnica non è coperta da questo piano e ha impatto sul formato del pack o sull'UX principale, **chiedi prima di decidere**. Per il resto scegli il default più semplice e annotalo nel README.
- A fine milestone: lint e test verdi, README aggiornato e un breve riepilogo di cosa è stato fatto e cosa resta.
