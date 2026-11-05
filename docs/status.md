# Stato del progetto

Aggiornato al 5 novembre 2026.

| Milestone | Stato | Note |
|---|---|---|
| M0 Setup | Fatta | Entrambi i progetti si installano e si avviano |
| M1 Schema e modelli | Fatta | Il pack d'esempio passa `validate` e la validazione lato web |
| M2 Estrazione | Fatta | 12 capitoli corretti più prefazione sul libro Gutenberg, 17 sezioni sul libro di 417 pagine |
| M3 Condensazione | **Da provare con un LLM vero** | Tutto verificato con il provider finto; nessuna chiamata reale |
| M4 Libreria e percorso | Fatta | |
| M5 Sessione | Fatta | Interazioni a 375 px, vedi sotto |
| M6 Progresso e PWA | **Quasi** | Mancano il primo deploy e la prova su telefono |
| M7 Esempio e documentazione | **Parziale** | Il pack d'esempio è scritto a mano, non generato dalla pipeline |

## Cosa è stato verificato

**Controlli automatici**: 120 test del generatore, 23 del lettore, ruff, ESLint e `nuxt typecheck` verdi.

**Nel browser** (build statica, viewport mobile):

- import da URL e da file, anteprima, aggiornamento di un libro già presente;
- errori comprensibili per JSON rotto, campi mancanti e versione futura;
- capitolo completato dall'inizio alla fine con tap e trascinamento, e di nuovo con la sola tastiera;
- ripresa alla card esatta dopo il ricaricamento, e alla fase esatta (mindmap);
- rilettura di un capitolo completato, che non altera il progresso;
- Riprendi, stati delle tappe, percentuale, panoramica, glossario;
- mappa del libro: toccando un titolo si apre il capitolo;
- tema e dimensione del testo persistenti, export e import con fusione;
- **offline a server spento**: home, Riprendi alla card esatta, link diretto a un capitolo, font, icone e mindmap;
- base URL `/pill-book/` con un server locale che imita GitHub Pages, compreso il link diretto tramite `404.html`.

**Generatore**:

- `build --fake --chapters 2-4` sul libro di 417 pagine con map-reduce: pack valido, 19 chiamate;
- ripresa dopo un'interruzione: nessuna chiamata già fatta viene ripetuta (test);
- ritentativi con l'errore passato al modello (test);
- richieste verso OpenRouter e gestione degli errori, anche quelli con stato 200, controllate con un trasporto HTTP simulato (test);
- catalogo reale di OpenRouter letto dalla CLI e dalla finestra: prezzi, ricerca, suggerimenti per gli id sbagliati;
- finestra Tkinter vera: caricamento del PDF, caselle dei capitoli, anteprima, correzione di titolo e pagine, stima, generazione con `fake`, interruzione e ripresa dalla cache, salvataggio nel `.env` (test, compresi clic veri su caselle e righe). I test si saltano dove non c'è un display, come in CI;
- anteprima sul libro di 417 pagine: caricamento sotto il secondo, una pagina disegnata in circa 12 ms;
- tutte le 12 citazioni del pack d'esempio confrontate parola per parola con il PDF.

## Cosa non è stato verificato

| Cosa | Perché | Come chiuderlo |
|---|---|---|
| Chiamate reali a un LLM e qualità dei prompt | In questo ambiente non c'è una chiave API e ogni prova ha un costo | `build --chapters 1-2` con una chiave OpenRouter: circa $0,12 sul libro d'esempio con il modello di default, stima |
| Modelli senza output strutturato | Il ripiego con lo schema nel prompt è provato solo in simulazione | Una prova con un modello senza "Schema" in `bookpack models` |
| Finestra su macOS e Linux | Provata solo su Windows | Un avvio su quei sistemi |
| Deploy su GitHub Pages | Il repo non ha ancora commit né remote, quindi il workflow non è mai stato eseguito | Push su GitHub e attivazione di Pages |
| Telefono vero | Solo emulazione: gesti simulati col mouse, pinch-zoom e installazione non provati | Aprire l'app pubblicata su un telefono |
| Viewport esatto di 390 px | A 390 il pannello del browser sfalsava i clic. Le interazioni sono state fatte a 375 px; a 390 è stato controllato solo il layout, senza overflow | Coperto dalla prova su telefono |
| Lighthouse PWA | Dalla versione 12 Lighthouse non ha più la categoria PWA. Controllati a mano manifest, icone, service worker e offline | Installazione dal telefono |

## Scostamenti dal piano

- **Il pack di M7 non viene dalla pipeline.** Senza chiave API è stato condensato a mano in una sessione di Claude Code, con gli stessi vincoli del generatore. Lo dichiara `generator.model`. Il comando per rigenerarlo è in [../samples/README.md](../samples/README.md).
- **Il PDF "di Project Gutenberg" è impaginato da noi** a partire dal testo di Gutenberg, che di rado offre PDF.

## Note su `books/AgenticSE_Book.pdf`

Il PDF è in gitignore e non ha metadati. Prima di spendere conviene esportare la divisione e correggerla:

```bash
uv run bookpack toc ../books/AgenticSE_Book.pdf -o out/agentic.toc.yaml
```

- `title` e `author` vanno inseriti a mano: oggi il titolo risulta "AgenticSE Book";
- "Reference Tables" e "Glossary Table" sono incluse come capitoli: probabilmente è meglio escluderle con `exclude: true`;
- "Leveraging the power of AI teammates" ha 76 pagine e riceverebbe comunque al massimo 12 card: si può dividere in più voci.

## Cosa resta

1. Prova di `build` con un LLM vero e revisione dei prompt in base al risultato.
2. Rigenerare il pack d'esempio con la pipeline e sostituire quello scritto a mano.
3. Primo commit, push, attivazione di GitHub Pages.
4. Prova su telefono: gesti, pinch-zoom, installazione, modalità aereo.
