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
- **Genera**: mostra la stima e chiede conferma. **Interrompi** si ferma alla fine della chiamata in corso; rilanciando, ciò che è già pronto non si ripaga. Correggere le pagine o il titolo di un capitolo già generato ne cambia il prompt, quindi si ripaga solo quel capitolo. Mentre genera si può continuare a sfogliare e correggere: la generazione in corso usa i capitoli com'erano al via.

Tkinter è compreso nel Python installato da uv. Con un altro Python su Linux può servire il pacchetto `python3-tk`.

## Comandi

| Comando | Cosa fa | Usa l'LLM |
|---|---|---|
| `uv run bookpack gui [libro.pdf]` | Apre la finestra | solo con Genera |
| `uv run bookpack models [ricerca] [--refresh]` | Elenca i modelli con prezzi e limiti | no |
| `uv run bookpack inspect libro.pdf [--toc f] [--include-all] [--model m]` | Metadati, capitoli, stima di token e costo | no |
| `uv run bookpack toc libro.pdf -o libro.toc.yaml` | Esporta la divisione in YAML da correggere a mano | no |
| `uv run bookpack build libro.pdf [opzioni]` | Genera il pack, dopo aver mostrato la stima | sì |
| `uv run bookpack validate out.bookpack.json` | Valida contro schema e vincoli | no |
| `uv run bookpack schema [-o file]` | Rigenera lo schema JSON | no |

Opzioni di `build`: `-o`, `--toc`, `--chapters 1-3,7`, `--lang it`, `--model`, `--fake`, `--include-all`, `--no-cache`, `--yes`. Senza `-o` il pack va in `generator/out/<id>.bookpack.json`, che è in gitignore.

## Configurazione

Copia `.env.example` in `.env`, che è in gitignore.

| Variabile | Default | Note |
|---|---|---|
| `OPENROUTER_API_KEY` | | da [openrouter.ai/keys](https://openrouter.ai/keys) |
| `BOOKPACK_MODEL` | `anthropic/claude-sonnet-5.5` | qualsiasi id del catalogo; `--model` ha la precedenza |
| `BOOKPACK_CONTEXT_TOKENS` | `40000` | sopra questa soglia un capitolo passa dal map-reduce; per i modelli piccoli vale al massimo il 60% del loro contesto |
| `BOOKPACK_CACHE_DIR` | `generator/.bookpack-cache` | contiene risposte e catalogo |

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
4. **Capitolo** (`condense/chapter.py`): una chiamata se entra nel budget, altrimenti note per chunk da circa 3.500 token con overlap e una chiamata finale sulle note.
5. **Retry** (`llm/structured.py`): se l'output viola schema o vincoli si ritenta fino a 2 volte, passando gli errori al modello. Le risposte vuote e gli errori del provider con stato 200 si ritentano a parte (`llm/openrouter.py`).
6. **Libro** (`condense/book.py`): panoramica, idee, mindmap e glossario, ricavati solo dalle sintesi dei capitoli.
7. **Validazione finale**: se fallisce il file non viene scritto.

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

## Cache e ripresa

Ogni risposta viene salvata appena arriva, con chiave `sha256(provider, modello, prompt, schema)`. Se `build` si interrompe, rilanciarlo riparte da dove era senza ripagare. Cambiare un prompt o il modello invalida solo le chiamate interessate.

## Costi

La stima usa caratteri/4 per l'input e un valore forfettario per l'output, ragionamento del modello incluso: è un ordine di grandezza. I prezzi arrivano dal catalogo pubblico di OpenRouter, tenuto in cache per 24 ore (`--refresh` per riscaricarlo). Senza rete si usa l'ultima copia; se non c'è, il costo appare come `n/d`. Alla fine di ogni generazione viene mostrato il costo effettivo comunicato da OpenRouter.

Stime di novembre 2026:

| Modello | Prezzo per milione di token | *How to Live on 24 Hours a Day* (48 pagine, 12 capitoli) | `AgenticSE_Book.pdf` (417 pagine, 16 capitoli) |
|---|---|---|---|
| `anthropic/claude-opus-5.5` | $4 / $20 | $1,14 | $1,96 |
| `anthropic/claude-sonnet-5.5` | $2 / $10 | $0,57 | $0,98 |
| `openai/gpt-5.6-luna` | $0,20 / $1,20 | $0,07 | $0,11 |
| `anthropic/claude-haiku-5.5` | $0,10 / $0,50 | $0,03 | $0,05 |

La qualità della condensazione con i diversi modelli non è stata misurata.

## Test

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

`tests/test_providers.py` esercita il client vero con un trasporto HTTP simulato: controlla le richieste e la gestione degli errori, ma non sostituisce una prova contro l'API reale. `tests/test_gui.py` apre la finestra vera; dove non c'è un display viene saltato. I test non leggono il tuo `.env` e non escono su internet.
