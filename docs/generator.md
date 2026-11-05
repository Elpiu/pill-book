# Generator

CLI e finestra in Python (uv, PyMuPDF, Pydantic, Typer, Rich, Tkinter), con i modelli di [OpenRouter](https://openrouter.ai/models). Tutti i comandi si lanciano da `generator/`.

```bash
uv sync
```

## Finestra

```bash
uv run bookpack gui
uv run bookpack gui ../books/libro.pdf
```

- **Libro**: scegli il PDF. **Salva…** e **Apri…** scrivono e rileggono la divisione in capitoli come file YAML, lo stesso formato di `--toc`.
- **Caselle**: la casella `☑` di una riga decide se quel capitolo entra nel pack, e quella in testa alla colonna spunta o toglie tutto. Una casella tolta non cambia il numero dei capitoli, quindi gli id restano stabili. Spuntare una sezione esclusa, come una bibliografia, la rende un capitolo e rinumera i successivi. Le spunte non vengono salvate nel file: si scelgono a ogni generazione.
- **Anteprima**: cliccando una riga, a destra si apre la sua prima pagina. **Prima pagina** e **Ultima pagina** saltano ai suoi confini, e la riga sotto l'anteprima dice a quale capitolo appartiene la pagina mostrata. Si sfoglia con le frecce, la rotella o il numero di pagina; `−`, `+` e **Adatta** regolano lo zoom.
- **Correzioni**: titolo e pagine si cambiano sotto l'elenco. I pulsanti **Il capitolo inizia qui** e **finisce qui** usano la pagina mostrata. Il capitolo vicino segue il nuovo confine se era contiguo o se si sovrapporrebbe; un vuoto voluto tra due capitoli resta. Le modifiche valgono subito per la generazione, ma per ritrovarle in seguito vanno salvate con **Salva…**: chiudendo senza salvare, la finestra chiede conferma.
- **Parametri**: il modello si cerca scrivendone una parte e sotto compaiono prezzo e limiti. **Salva in .env** rende modello e chiave quelli di default.
- **Genera**: mostra la stima e chiede conferma. Correggere le pagine o il titolo di un capitolo già generato ne cambia il prompt, quindi si ripaga solo quel capitolo. Mentre genera si può continuare a sfogliare e correggere: la generazione in corso usa i capitoli com'erano al via.
- **Interrompi e Riprendi**: **Interrompi** non fa partire niente di nuovo e aspetta le chiamate già in corso. **Riprendi** si attiva quando c'è una generazione incompleta del PDF aperto: rimette capitoli corretti, spunte, modello, lingua e destinazione, poi continua. La finestra cerca in `generator/out/` e nella cartella di **Salva in**. Chiudendo la finestra durante una generazione, il programma termina solo dopo le chiamate in corso.

Tkinter è compreso nel Python installato da uv. Con un altro Python su Linux può servire il pacchetto `python3-tk`.

## Comandi

| Comando | Cosa fa | Usa l'LLM |
|---|---|---|
| `uv run bookpack gui [libro.pdf]` | Apre la finestra | solo con Genera |
| `uv run bookpack models [ricerca] [--refresh]` | Elenca i modelli con prezzi e limiti | no |
| `uv run bookpack inspect libro.pdf [--toc f] [--include-all] [--model m]` | Metadati, capitoli, stima di token e costo | no |
| `uv run bookpack toc libro.pdf -o libro.toc.yaml` | Esporta la divisione in YAML da correggere a mano | no |
| `uv run bookpack build libro.pdf [opzioni]` | Genera il pack, dopo aver mostrato la stima | sì |
| `uv run bookpack resume out/<id>.state.json [--pdf f] [--workers n] [--yes]` | Riprende una generazione incompleta, con gli stessi parametri | sì |
| `uv run bookpack validate out.bookpack.json` | Valida contro schema e vincoli | no |
| `uv run bookpack schema [-o file]` | Rigenera lo schema JSON | no |

Opzioni di `build`: `-o`, `--toc`, `--chapters 1-3,7`, `--lang it`, `--model`, `--fake`, `--include-all`, `--no-cache`, `--workers 4`, `--yes`. Senza `-o` il pack va in `generator/out/<id>.bookpack.json`, che è in gitignore.

## Configurazione

Copia `.env.example` in `.env`, che è in gitignore.

| Variabile | Default | Note |
|---|---|---|
| `OPENROUTER_API_KEY` | | da [openrouter.ai/keys](https://openrouter.ai/keys) |
| `BOOKPACK_MODEL` | `anthropic/claude-sonnet-5.5` | qualsiasi id del catalogo; `--model` ha la precedenza |
| `BOOKPACK_CONTEXT_TOKENS` | `40000` | limite alla grandezza delle parti, oltre ai 5.000 token normali; per i modelli piccoli vale al massimo il 60% del loro contesto |
| `BOOKPACK_CACHE_DIR` | `generator/.bookpack-cache` | contiene risposte e catalogo |
| `BOOKPACK_WORKERS` | `4` | chiamate all'LLM insieme; `--workers` ha la precedenza |

Un id sconosciuto viene rifiutato prima di spendere, con i suggerimenti più vicini.

L'opzione `--fake` non usa né rete né chiave e compone l'output con frasi estratte dal testo. Serve a provare la pipeline e la divisione in capitoli gratis, non a leggere: il risultato non è una condensazione.

## Pipeline di `build`

1. **Estrazione** (`extract/pdf.py`): testo per pagina con font e posizione. Un PDF senza testo viene rifiutato: serve prima l'OCR.
2. **Capitoli** (`extract/toc.py`, `condense/detect.py`), in quest'ordine:
   1. file `--toc`;
   2. outline del PDF: il livello meno profondo con 3-60 capitoli e mediana fino a 60 pagine, così le "parti" non vengono scambiate per capitoli;
   3. titoli: prima le etichette ("Capitolo 3"), poi le righe più grandi del testo;
   4. solo in `build`, una chiamata all'LLM sulle prime pagine e su un campione delle altre.

   Copertina, copyright, indici, ringraziamenti e bibliografia sono esclusi, salvo `--include-all`.
3. **Pulizia** (`extract/clean.py`): header e footer ripetuti, numeri di pagina, sillabazione anche tra due pagine, spazi.
4. **Card, parte per parte** (`condense/chapter.py`): il capitolo viene diviso in parti da circa 5.000 token, e ognuna riceve le sue card in proporzione, circa una ogni 500 parole. Così nessuna sezione sparisce e i capitoli lunghi hanno più spazio di quelli brevi. Il modello sceglie la forma in base al contenuto: `procedure` con passi e comandi dove il testo insegna a fare qualcosa, `concept` ed `example` dove argomenta. Aggiunge una domanda ogni 3-4 card.
4b. **Chiusura del capitolo**: una chiamata separata scrive riassunto, takeaway, mindmap e flashcard **a partire dalle card**, non dal testo originale. Così le flashcard chiedono solo cose che il lettore ha visto.
5. **Retry** (`llm/structured.py`): se l'output viola schema o vincoli si ritenta fino a 2 volte, passando gli errori al modello. Le risposte vuote e gli errori del provider con stato 200 si ritentano a parte (`llm/openrouter.py`).
6. **Libro** (`condense/book.py`): panoramica, idee, mindmap e glossario, ricavati solo dalle sintesi dei capitoli.
7. **Validazione finale**: se fallisce il file non viene scritto.

Le fasi 4, 4b e 6 girano una dopo l'altra, e dentro ogni fase le chiamate partono insieme: vedi [Parallelismo](#parallelismo).

I prompt sono in `src/bookpack/condense/prompts/*.md`. Migliorarli e rigenerare non richiede modifiche all'app.

## Modelli e output strutturato

Ogni richiesta chiede a OpenRouter uno schema JSON e solo i provider che lo rispettano (`require_parameters`). Se nessuno lo supporta per quel modello, il client passa a mettere lo schema nel prompt. In entrambi i casi l'output viene validato in locale, quindi un modello impreciso costa qualche ritentativo ma non produce un pack invalido. In `bookpack models`, la colonna "Schema" dice quali modelli lo supportano: sono da preferire.

## Ragionamento e limite di output

Molti modelli ragionano prima di rispondere. Quei token si pagano come output e, sulla maggior parte dei provider, contano nello stesso limite della risposta. Per questo:

- si chiede il livello `low` ai modelli che lo dichiarano nel catalogo; gli altri usano il loro default;
- il limite è di 32.000 token per chiamata, ridotto se il modello ne ammette meno;
- se la risposta viene troncata si riprova una volta a 64.000. Il tentativo troncato si paga e viene sommato al costo effettivo;
- se viene troncata anche così, l'errore riporta i token spesi a ragionare. Rilanciando non si ripaga ciò che è già in cache.

Sui modelli senza `low`, come `deepseek/deepseek-v4-flash`, il ragionamento può crescere col limite e la spesa può superare la stima. Conviene preferire un modello che lo offre: nella finestra lo indica "ragionamento low" sotto il modello.

## Parallelismo

Le chiamate aspettano la rete, quindi bastano i thread (`condense/tasks.py`), al massimo 4 insieme per default. Le fasi sono tre, e ognuna finisce prima che parta la successiva:

1. tutte le parti di tutti i capitoli: il prompt di una parte dipende solo dal suo testo;
2. la chiusura dei capitoli con tutte le parti riuscite;
3. la panoramica del libro.

Il risultato non dipende dal numero di chiamate insieme: card e id si assegnano alla fine, nell'ordine del libro. Anche i prompt non cambiano, quindi le cache esistenti restano valide.

Misura reale su 4 capitoli brevi del libro d'esempio con `~deepseek/deepseek-flash-latest`, un lancio per configurazione e cache vuota:

| Chiamate insieme | Tempo | Chiamate | Costo effettivo |
|---|---|---|---|
| 1 | 125 secondi | 9 | $0,02 |
| 4 | 66 secondi | 11, di cui 2 ritentativi | $0,02 |

Non si arriva a 4 volte più veloce perché ogni fase aspetta la sua chiamata più lenta, e la panoramica è una sola. I ritentativi dipendono dalle risposte del modello, non dal parallelismo. Sui libri lunghi non è ancora stato misurato. Se il provider limita le richieste, la generazione si ferma con un errore chiaro: basta riprendere con `--workers` più basso.

## Errori, interruzioni e ripresa

**Cache** (`cache.py`, `llm/structured.py`): la chiave è `sha256(provider, modello, prompt, schema)`. Si conservano solo le risposte che superano la validazione, sotto il prompt iniziale anche se è servito un ritentativo. Una risposta scartata viene tolta, così rilanciando se ne chiede una nuova. Cambiare un prompt o il modello invalida solo le chiamate interessate.

**Errori**: se una chiamata fallisce, le altre proseguono, perché sono già pagate o lo saranno comunque. Alla fine si elenca cosa non è riuscito e il pack non viene scritto. Chiave non valida, modello inesistente, credito esaurito, limite di richieste e rete assente valgono per tutte le chiamate: in quei casi non parte più niente di nuovo.

**Interruzione**: **Interrompi** nella finestra o Ctrl+C nel terminale non fanno partire altre chiamate. Quelle in corso finiscono e restano in cache.

**File di stato** (`condense/state.py`): accanto al pack, in `out/<id>.state.json`, riscritto dopo ogni attività e cancellato quando il pack è pronto.

```json
{
  "version": 1,
  "input": {
    "pdf": "D:/libri/libro.pdf",
    "pdf_sha256": "...",
    "model": "...",
    "fake": false,
    "lang": "it",
    "selected": [1, 2, 3],
    "output": "out/libro.bookpack.json",
    "context_tokens": 40000,
    "detection": { "method": "outline", "sections": [], "book": {}, "note": null }
  },
  "tasks": {
    "ch-01/part-1": { "state": "done" },
    "ch-01/part-2": { "state": "failed", "error": "..." },
    "ch-01/wrap": { "state": "pending" },
    "book": { "state": "pending" }
  },
  "spent": { "calls": 12, "input_tokens": 60000, "output_tokens": 30000, "cost": 0.04 }
}
```

Non contiene testo del libro né chiavi, ed è in gitignore. Le risposte stanno solo nella cache, quindi riprendendo si rieseguono tutte le attività e quelle già pronte tornano subito. Il file serve a tre cose:

- **stessi parametri**: pagine corrette a mano comprese, altrimenti i prompt cambierebbero e quei capitoli si ripagherebbero;
- **costo totale**: `spent` si somma tra i lanci, se il lavoro è lo stesso;
- **a che punto si è**: `bookpack resume` mostra attività fatte, fallite e da fare, e il costo stimato di ciò che resta, prima di chiedere conferma.

Rilanciare `build` con gli stessi parametri funziona allo stesso modo. Con `resume`, il PDF viene riconosciuto dall'hash: se è stato spostato si indica con `--pdf`, se è cambiato viene rifiutato.

## Costi

La stima usa caratteri/4 per l'input e, per l'output, valori misurati su generazioni reali con `~deepseek/deepseek-flash-latest`, ragionamento compreso: è un ordine di grandezza, e con altri modelli può scostarsi. I prezzi arrivano dal catalogo pubblico di OpenRouter, tenuto in cache per 24 ore (`--refresh` per riscaricarlo). Senza rete si usa l'ultima copia; se non c'è, il costo appare come `n/d`. Alla fine di ogni generazione viene mostrato il costo effettivo comunicato da OpenRouter.

Stime di novembre 2026:

| Modello | Prezzo per milione di token | *How to Live on 24 Hours a Day* (48 pagine, 12 capitoli) | Manuale di 417 pagine, 16 capitoli |
|---|---|---|---|
| `anthropic/claude-opus-5.5` | $4 / $20 | $2,12 | $5,55 |
| `anthropic/claude-sonnet-5.5` | $2 / $10 | $1,06 | $2,78 |
| `openai/gpt-5.6-luna` | $0,20 / $1,20 | $0,13 | $0,32 |
| `anthropic/claude-haiku-5.5` | $0,10 / $0,50 | $0,05 | $0,14 |

Riscontri reali con `~deepseek/deepseek-flash-latest`:

| Generazione | Chiamate | Token di output | Costo effettivo |
|---|---|---|---|
| Capitolo di 76 pagine di un manuale | 8 | 40.854 | $0,03 |
| *How to Live on 24 Hours a Day*, intero | 29 | 65.716 (stimati 95.400) | $0,05 |

La qualità della condensazione con i diversi modelli non è stata confrontata.

## Densità e tempo di lettura

La quantità di card dipende da `WORDS_PER_CARD` in `condense/chunking.py`, oggi una card ogni 500 parole. Misure reali:

| Capitolo | Parole del libro | Parole prodotte, con il riassunto | Sessione | Lettura del libro |
|---|---|---|---|---|
| 76 pagine di un manuale | 15.114 | circa 6.000 | 39 minuti | circa 66 minuti |
| Capitolo di 3 pagine del saggio breve | 910 | circa 560 | 5 minuti | circa 4 minuti |

Sui capitoli lunghi si risparmia tempo. Su quelli molto brevi no: la sessione dura quanto la lettura, perché oltre al testo ci sono domande e flashcard. Alzare `WORDS_PER_CARD` accorcia le sessioni, a scapito della profondità.

## Test

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

`tests/test_providers.py` esercita il client vero con un trasporto HTTP simulato: controlla le richieste e la gestione degli errori, ma non sostituisce una prova contro l'API reale. `tests/test_gui.py` apre la finestra vera; dove non c'è un display viene saltato. I test non leggono il tuo `.env` e non escono su internet.
