# Stato del progetto

Aggiornato al 5 novembre 2026. Il formato attuale è la v2: vedi [decisions.md](decisions.md).

| Milestone | Stato | Note |
|---|---|---|
| M0 Setup | Fatta | Entrambi i progetti si installano e si avviano |
| M1 Schema e modelli | Fatta | Il pack d'esempio passa `validate` e la validazione lato web |
| M2 Estrazione | Fatta | 12 capitoli corretti più prefazione sul libro Gutenberg, 17 sezioni sul libro di 417 pagine |
| M3 Condensazione | Fatta | Provata con generazioni reali su `~deepseek/deepseek-flash-latest` |
| M4 Libreria e percorso | Fatta | |
| M5 Sessione | Fatta | Interazioni a 375 px, vedi sotto |
| M6 Progresso e PWA | **Quasi** | Pubblicata su GitHub Pages, manca la prova su telefono |
| M7 Esempio e documentazione | Fatta | Il pack d'esempio è generato dalla pipeline da un libro di pubblico dominio |
| Formato v2 | Fatto | Spazio proporzionale, card dense, domande, riassunto, ripasso |
| Generazione parallela e ripresa | Fatta | Chiamate insieme, errori che non fermano tutto, file di stato, `bookpack resume`, **Riprendi** |

## Cosa è stato verificato

**Controlli automatici**: 161 test del generatore, 36 del lettore, ruff, ESLint e `nuxt typecheck` verdi.

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

**Deploy**: il workflow è riuscito su GitHub e il sito è online su <https://elpiu.github.io/pill-book/>. Pagina, manifest e service worker rispondono correttamente.

**Generatore**:

- generazione reale di un capitolo di 76 pagine: pack valido, 8 chiamate, 5 parti, copertura di tutte le sottosezioni;
- generazione reale del libro d'esempio: pack valido, 29 chiamate, citazioni trovate nel testo;
- generazione reale di 4 capitoli del libro d'esempio, con 1 e con 4 chiamate insieme: 125 e 66 secondi, pack validi, $0,02 ciascuna;
- pack generato in parallelo identico a quello in sequenza, con le risposte in ordine sparso (test);
- errore su un capitolo, interruzione e Ctrl+C simulato: nessuna chiamata già fatta viene ripetuta, e la ripresa fa solo ciò che manca (test);
- `resume` da riga di comando e **Riprendi** nella finestra, con pagine corrette a mano, spunte e lingua ripristinate (test);
- ritentativi con l'errore passato al modello, e risposta scartata richiesta di nuovo al rilancio (test);
- richieste verso OpenRouter e gestione degli errori, anche quelli con stato 200, controllate con un trasporto HTTP simulato (test);
- catalogo reale di OpenRouter letto dalla CLI e dalla finestra: prezzi, ricerca, suggerimenti per gli id sbagliati;
- finestra Tkinter vera: caricamento del PDF, caselle dei capitoli, anteprima, correzione di titolo e pagine, stima, generazione con `fake`, interruzione e ripresa dalla cache, salvataggio nel `.env` (test, compresi clic veri su caselle e righe). I test si saltano dove non c'è un display, come in CI;
- anteprima sul libro di 417 pagine: caricamento sotto il secondo, una pagina disegnata in circa 12 ms;
- tutte le 12 citazioni del pack d'esempio confrontate parola per parola con il PDF.

## Cosa non è stato verificato

| Cosa | Perché | Come chiuderlo |
|---|---|---|
| Altri modelli oltre a `~deepseek/deepseek-flash-latest` | Ogni prova ha un costo | Un confronto sullo stesso capitolo |
| Parallelismo su un libro lungo | Misurato solo su 4 capitoli brevi, con un lancio per configurazione. Limiti di richieste mai incontrati | La prossima generazione di un libro intero |
| Ctrl+C in un terminale vero | Provato in simulazione: nel test l'interruzione arriva dentro l'attesa | Premerlo durante una generazione |
| Quanto resta davvero al lettore | Le misure dicono quanto testo c'è, non cosa si ricorda | Uso reale per qualche settimana |
| Modelli senza output strutturato | Il ripiego con lo schema nel prompt è provato solo in simulazione | Una prova con un modello senza "Schema" in `bookpack models` |
| Finestra su macOS e Linux | Provata solo su Windows | Un avvio su quei sistemi |
| Telefono vero | Solo emulazione: gesti simulati col mouse, pinch-zoom e installazione non provati | Aprire l'app pubblicata su un telefono |
| Viewport esatto di 390 px | A 390 il pannello del browser sfalsava i clic. Le interazioni sono state fatte a 375 px; a 390 è stato controllato solo il layout, senza overflow | Coperto dalla prova su telefono |
| Lighthouse PWA | Dalla versione 12 Lighthouse non ha più la categoria PWA. Controllati a mano manifest, icone, service worker e offline | Installazione dal telefono |

## Scostamenti dal piano

- **Formato v2.** Il piano prevedeva sessioni da 5 minuti, 5-12 card e 3-5 flashcard per capitolo. Le misure sui primi pack hanno mostrato che i capitoli lunghi perdevano troppo: vedi [decisions.md](decisions.md).
- **Solo OpenRouter**, al posto dei provider Anthropic e OpenAI-compatibili.
- **Il PDF "di Project Gutenberg" è impaginato da noi** a partire dal testo di Gutenberg, che di rado offre PDF.

## Cosa resta

1. Prova su telefono: gesti, scorrimento delle card lunghe, pinch-zoom, installazione, modalità aereo.
2. Rigenerare con il formato v2 i libri già generati: i vecchi pack non si importano più.

Per i lavori futuri vedi [roadmap.md](roadmap.md).
