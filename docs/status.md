# Stato del progetto

Aggiornato al 14 novembre 2026. Il formato attuale è la v2: vedi [decisions.md](decisions.md).

| Milestone | Stato | Note |
|---|---|---|
| M0 Setup | Fatta | Entrambi i progetti si installano e si avviano |
| M1 Schema e modelli | Fatta | Il pack d'esempio passa `validate` e la validazione lato web |
| M2 Estrazione | Fatta | 12 capitoli corretti più prefazione sul libro Gutenberg, 17 sezioni sul libro di 417 pagine |
| M3 Condensazione | Fatta | Provata con generazioni reali su `~deepseek/deepseek-flash-latest` |
| M4 Libreria e percorso | Fatta | |
| M5 Sessione | Fatta | Interazioni a 375 px, vedi sotto |
| M6 Progresso e PWA | Fatta | Pubblicata su GitHub Pages e provata su un telefono vero |
| M7 Esempio e documentazione | Fatta | Il pack d'esempio è generato dalla pipeline da un libro di pubblico dominio, in italiano e in inglese |
| Formato v2 | Fatto | Spazio proporzionale, card dense, domande, riassunto, ripasso |
| Generazione parallela e ripresa | Fatta | Chiamate insieme, errori che non fermano tutto, file di stato, `bookpack resume`, **Riprendi** |
| Modalità ascolto | Fatta | Modulo vocale, sessione e impostazioni (TASK-8.1, 8.2, 8.3), provati anche su telefono (TASK-8) |
| Routine di lettura | **Quasi** | Registro, minuti attivi, streak, routine, promemoria, scheda Oggi e calendario (TASK-10.1, 10.2, 10.3), sul branch `feature/routine-lettura`; manca la prova su telefono (TASK-10) |

## Cosa è stato verificato

**Controlli automatici**: 164 test del generatore, 127 del lettore, ruff, ESLint e `nuxt typecheck` verdi.

**Modulo vocale** (TASK-8.1): con il sintetizzatore vero di Chromium, a volume zero, una coda di frasi e pause arriva alla fine; la pausa ferma davvero la voce e la ripresa riparte dalla frase interrotta. Una card vera del libro d'esempio, 8 frasi e pause, si legge fino in fondo in 56 secondi senza blocchi.

**Ascolto nella sessione** (TASK-8.2), nel browser integrato a 375 px con il sintetizzatore vero a volume zero: avvio dal pulsante, barra con avanti, indietro, velocità salvata e pausa; freccia che fa ripartire la voce dalla card raggiunta; domanda con conto alla rovescia di 7 secondi, **Mostra ora**, risposta mostrata e nessun esito registrato; passaggio da solo dall'ultima card al riassunto; fine sulla mindmap con il messaggio; pausa quando la pagina va in secondo piano (simulata); voce fermata cambiando fase a mano o uscendo dalla sessione. Casi limite simulati: con la sola voce inglese su un libro italiano il pulsante è attenuato e spiega perché; senza sintesi vocale il pulsante non c'è.

**Ascolto su telefono e su Chrome** (prova manuale, TASK-8): capitolo ascoltato fino al riassunto senza toccare lo schermo, libro italiano e inglese ciascuno con la voce della sua lingua, posizione mantenuta tra ascolto e lettura, modalità aereo con voce locale, pausa con lo schermo bloccato e ripresa con un tocco.

**Routine di lettura** (TASK-10.1, 10.2, 10.3), nel browser integrato a 375 px con giornate simulate: minuti, card, risposte e capitoli scritti nel registro; giornata riuscita al superamento dell'obiettivo con un solo festeggiamento ("5 giorni di fila"); scheda Oggi, pagina Routine e calendario coerenti con il registro, giorno libero compreso; routine salvata, promemoria con Google Calendar e file `.ics`, cambio di orario e rinnovo che parte dopo la scadenza; export in versione 3 con fusione per giorno. Le icone nuove sono nella build di produzione.

**Impostazioni dell'ascolto** (TASK-8.3), con voci simulate: elenco delle voci italiane nell'ordine previsto, voce di rete segnalata, scelta salvata, **Prova** con la voce e la velocità scelte, ritorno alla voce automatica quando quella scelta sparisce, pulsante tolto dalla sessione con l'interruttore spento, preferenze presenti nell'export. Il browser di prova non espone voci, quindi la scelta tra voci reali è coperta solo dai test.

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

**Su un telefono vero** (prova manuale, TASK-1): swipe e tap sulle card, anche lunghe, pinch-zoom e pan nelle mindmap, installazione su Android e iPhone, sessione completa in modalità aereo.

**Generatore**:

- generazione reale di un capitolo di 76 pagine: pack valido, 8 chiamate, 5 parti, copertura di tutte le sottosezioni;
- generazione reale del libro d'esempio: pack valido, 29 chiamate, citazioni trovate nel testo;
- titoli tradotti (TASK-9): rigenerando il libro d'esempio, quello italiano ha titolo e dodici capitoli in italiano, quello inglese li mantiene; id invariati. Con la prima versione dell'istruzione due titoli su dodici e quello del libro restavano in inglese, quindi il titolo ora si chiede dopo il riassunto e nella sua stessa lingua;
- generazione reale della versione inglese, con 4 chiamate insieme: pack valido, 27 chiamate con 2 ritentativi, 1 minuto e 40 secondi, $0,03; importata accanto a quella italiana come libro distinto;
- generazione reale di 4 capitoli del libro d'esempio, con 1 e con 4 chiamate insieme: 125 e 66 secondi, pack validi, $0,02 ciascuna;
- generazione di un libro intero in parallelo, Ctrl+C in un terminale vero e ripresa con `bookpack resume` (prova manuale, TASK-3, senza numeri registrati qui);
- pack generati prima della v2 rigenerati e importati nell'app pubblicata (TASK-2);
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
| Routine su telefono | Il file `.ics` su iPhone, soprattutto dall'app installata, e il link a Google Calendar su Android non sono provati; più giorni reali d'uso nemmeno | Le prove di TASK-10 |
| Quanto resta davvero al lettore | Le misure dicono quanto testo c'è, non cosa si ricorda | Uso reale per qualche settimana |
| Altri modelli oltre a `~deepseek/deepseek-flash-latest` | Ogni prova ha un costo | Fuori scopo, per scelta (TASK-4 archiviata) |
| Modelli senza output strutturato | Il ripiego con lo schema nel prompt è provato solo in simulazione | Fuori scopo, per scelta (TASK-5 archiviata) |
| Finestra su macOS e Linux | Provata solo su Windows. Dipende da Python e Tkinter | Fuori scopo, per scelta (TASK-6 archiviata) |

## Scostamenti dal piano

- **Formato v2.** Il piano prevedeva sessioni da 5 minuti, 5-12 card e 3-5 flashcard per capitolo. Le misure sui primi pack hanno mostrato che i capitoli lunghi perdevano troppo: vedi [decisions.md](decisions.md).
- **Solo OpenRouter**, al posto dei provider Anthropic e OpenAI-compatibili.
- **Il PDF "di Project Gutenberg" è impaginato da noi** a partire dal testo di Gutenberg, che di rado offre PDF.

## Cosa resta

Nel backlog non ci sono attività aperte. Le idee non ancora decise stanno tra le bozze, in `backlog/drafts/`: sincronizzazione con Google Drive, prompt per la narrativa e le voci della roadmap del piano. Si consultano con `backlog board`, `backlog draft list` o `backlog browser`.
