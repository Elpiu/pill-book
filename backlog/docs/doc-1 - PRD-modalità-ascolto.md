---
id: doc-1
title: 'PRD: modalità ascolto'
type: specification
created_date: '2026-11-14T16:10:00Z'
updated_date: '2026-11-14T16:16:00Z'
---
# PRD: modalità ascolto

| | |
|---|---|
| Stato | Approvato il 14 novembre 2026 |
| Data | 14 novembre 2026 |
| Parte | Lettore (`web/`) |
| Formato del pack | Invariato |

## Problema

Oggi le pillole si possono solo leggere. Ci sono momenti in cui guardare lo schermo con attenzione costa, ma ascoltare no: in piedi sul tram, mentre si cammina, con gli occhi stanchi a fine giornata. Chi preferisce leggere, invece, non deve trovarsi davanti niente di nuovo da capire o da disattivare.

## Obiettivi

1. **Ascoltare un capitolo dall'inizio al riassunto**, con le card che avanzano da sole al ritmo della voce, senza dover toccare lo schermo.
2. **Voce nella lingua del libro**, presa da `book.lang` del pack, scelta in automatico tra quelle del dispositivo e modificabile.
3. **Passare tra lettura e ascolto in qualsiasi momento** senza perdere il punto: lettura e ascolto condividono la posizione salvata.
4. **Nessuna complessità per chi legge**: un solo pulsante nella sessione, nascondibile del tutto dalle impostazioni.
5. **Nessuna dipendenza, nessun costo, funziona offline** con le voci installate sul dispositivo.

## Non obiettivi

- Audio pre-generato dal generatore o voci cloud a pagamento.
- Ascolto garantito a schermo bloccato o con l'app in secondo piano: l'API del browser non lo permette in modo affidabile, soprattutto su iPhone.
- Evidenziazione parola per parola del testo letto.
- Flashcard e ripasso in ascolto: richiedono di ricordare attivamente, che è il loro scopo.
- Lettura della mindmap, della libreria, del percorso o della panoramica del libro.
- Modifiche al formato del pack, allo schema o al generatore.

## Scelta tecnica

Sintesi vocale del browser, con la [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis), che usa le voci del sistema operativo. Alternativa scartata per ora: file audio generati per ogni card, perché richiedono un servizio esterno o un motore locale, cambiano il formato e portano un libro lungo a decine o centinaia di MB nel browser. Si potrà valutare in seguito, costruendo sopra questa versione.

## Esperienza

### Chi vuole solo leggere

Vede un pulsante con le cuffie nell'intestazione della sessione, a destra del titolo, dove oggi c'è uno spazio vuoto. Se non lo tocca, l'app si comporta esattamente come oggi. Nelle impostazioni, l'opzione **Mostra il pulsante Ascolta** lo toglie del tutto.

Il pulsante non compare quando il dispositivo non ha la sintesi vocale, e appare disattivato quando non ha una voce nella lingua del libro, con la spiegazione al tocco: "Nessuna voce in inglese su questo dispositivo. Puoi aggiungerla dalle impostazioni del telefono."

### Avvio

Un tocco sulle cuffie avvia l'ascolto dalla card corrente. Il tocco serve anche a iPhone, che permette di far partire la voce solo da un gesto dell'utente. L'ascolto non parte mai da solo all'apertura di un capitolo.

### Durante l'ascolto

In basso compare una barra di controllo compatta:

| Controllo | Effetto |
|---|---|
| Pausa / Riprendi | Ferma e riprende dalla frase interrotta |
| Indietro / Avanti | Card precedente o successiva, e la voce riparte da lì |
| Velocità | 0,8×, 1×, 1,2×, 1,5×; la scelta resta salvata |
| Chiudi | Esce dall'ascolto e torna alla lettura normale, sulla card raggiunta |

Le card restano visibili e scorrono da sole a fine lettura. Swipe, tap e frecce funzionano come sempre: spostarsi a mano su un'altra card fa ripartire la voce da quella. La card in lettura è segnalata con discrezione, per esempio con l'icona delle cuffie accanto all'etichetta del tipo.

### Cosa viene letto

Solo il testo del libro, nella sua lingua. Nessuna parola dell'interfaccia viene pronunciata, così una voce inglese non legge "Risposta" in italiano: i passaggi si segnano con pause.

| Card | Lettura |
|---|---|
| Concetto, definizione, esempio | Titolo, idea, spiegazione |
| Come si fa | Titolo, idea, poi i passi uno per volta con una breve pausa tra l'uno e l'altro |
| Codice | Non letto: resta sullo schermo, la voce prosegue con il resto |
| Citazione | Il testo citato |
| Nuova parte | Titolo e introduzione, seguiti da una pausa più lunga |
| Da portare via | Il testo |
| Domanda | La domanda, poi 7 secondi per pensare con un conto alla rovescia visibile, poi la risposta, che si mostra anche sulla card. Un tocco salta l'attesa |

Le domande ascoltate **non registrano** alcun esito: "Lo sapevo" e "Da ripassare" restano disponibili sulla card, come in lettura, e toccarli non interrompe l'ascolto.

### Fine dell'ascolto

Dopo l'ultima card l'ascolto passa al riassunto e lo legge. Poi si ferma con il messaggio "Fine dell'ascolto: continua con mindmap e flashcard", sulla fase della mindmap. Il capitolo si completa come oggi, alla fine delle flashcard.

### Interruzioni

- Uscire dalla sessione, cambiare fase o chiudere l'app ferma la voce.
- Quando l'app va in secondo piano o lo schermo si blocca, l'ascolto passa in pausa. Al ritorno la barra mostra "In pausa" e un tocco riprende dalla frase interrotta, invece di ritrovarsi a metà card senza saperlo.
- Una telefonata o un altro audio interrompono la voce come qualsiasi altro suono del sistema.

### Posizione e progresso

Ogni avanzamento dovuto all'ascolto salva la posizione come uno spostamento a mano. Riaprendo il capitolo si riprende dalla card raggiunta, in lettura; l'ascolto si riattiva con un tocco.

## Lingua e voci

- La lingua è quella di `book.lang`, per esempio `it` o `en`. I codici del dispositivo si confrontano normalizzati: `it_IT`, usato da alcuni Android, vale come `it-IT`.
- **Voce automatica**, in quest'ordine di preferenza:
  1. stessa lingua e stessa regione della lingua del browser, se coincide (`it-IT` per un browser in italiano);
  2. voci locali, che funzionano offline, prima di quelle di rete;
  3. voci con nomi che indicano la qualità migliore, come "Enhanced", "Premium", "Natural", "Neural";
  4. la voce predefinita del sistema.
- **Voce scelta a mano**: nelle impostazioni, una voce per ogni lingua dei libri presenti nella libreria, con un pulsante **Prova** che legge una frase del libro. La scelta si salva per lingua, quindi libri in lingue diverse usano ciascuno la propria voce.
- **Voce non più disponibile**, per esempio dopo un cambio di telefono: si torna alla scelta automatica senza errori.

## Impostazioni

Una sezione **Ascolto**, visibile solo dove la sintesi vocale esiste:

- **Mostra il pulsante Ascolta**, attivo per default;
- **Velocità predefinita**;
- **Voce** per ciascuna lingua dei libri presenti, con **Prova**;
- un suggerimento per installare voci migliori: su iPhone da Impostazioni → Accessibilità → Contenuto letto ad alta voce → Voci; su Android dalle impostazioni della sintesi vocale di Google.

Le impostazioni seguono il percorso di quelle esistenti: tabella `settings` di IndexedDB, quindi entrano anche nell'export del progresso.

## Requisiti tecnici

1. **Modulo riusabile senza dipendenze**: un composable che incapsula `speechSynthesis` e non sa nulla di card e libri. Espone voci disponibili, scelta della voce per lingua, coda di frasi, pausa, ripresa, stop, velocità e stato.
2. **Testo da leggere separato dalla voce**: una funzione pura trasforma una card, o il riassunto, in una sequenza di frasi e pause, seguendo la tabella sopra. È coperta da test, come `utils/progress.ts`.
3. **Una frase alla volta**: il testo si divide in frasi, e le frasi molto lunghe alle virgole, così nessuna lettura supera la durata oltre la quale Chrome la interrompe. Pausa e ripresa ripartono dall'inizio della frase corrente invece di usare `pause()` del browser, che su Android non riprende in modo affidabile.
4. **Caricamento delle voci**: l'elenco può arrivare vuoto e popolarsi dopo. Si legge subito, si ascolta `voiceschanged` e, dove l'evento non arriva come su alcuni Safari, si riprova per qualche secondo.
5. **Nessun cambiamento** al formato del pack, allo schema, al generatore e alla navigazione esistente di card e fasi.
6. **Offline**: con una voce locale l'ascolto funziona senza rete. Con una voce di rete l'eventuale errore si mostra come pausa con un messaggio, non come blocco.
7. **Accessibilità**: tutti i controlli hanno un'etichetta leggibile dagli screen reader; l'ascolto non si avvia mai da solo, per non sovrapporsi a VoiceOver o TalkBack.

## Criteri di accettazione

- Su un telefono vero, un capitolo si ascolta dalla prima card alla fine del riassunto senza toccare lo schermo.
- Un libro in italiano e uno in inglese vengono letti ciascuno con una voce della propria lingua; per una lingua senza voci il pulsante è disattivato e lo spiega.
- Passando da ascolto a lettura e ritorno, e riaprendo il capitolo, la posizione è sempre quella dell'ultima card raggiunta.
- Le domande in ascolto lasciano il tempo di pensare, si possono saltare e non registrano esiti da sole.
- Il codice non viene letto; nessuna parola dell'interfaccia viene pronunciata.
- Con il pulsante nascosto dalle impostazioni, la sessione è identica a quella di oggi.
- In modalità aereo, con una voce locale, l'ascolto funziona.
- Bloccando lo schermo l'ascolto va in pausa e riprende con un tocco dalla frase interrotta.
- Test per la trasformazione delle card in frasi e pause e per la scelta automatica della voce; lint, typecheck e test verdi; documentazione aggiornata.

## Rischi e limiti noti

| Rischio | Effetto | Come lo gestiamo |
|---|---|---|
| Schermo bloccato o app in secondo piano | Su iPhone la voce si ferma, specie nell'app installata | Pausa esplicita e ripresa con un tocco; dichiarato nei non obiettivi |
| Qualità diversa da dispositivo a dispositivo | Alcune voci suonano robotiche | Preferenza per voci migliorate e suggerimento per installarle |
| Su iPhone, una sola voce selezionabile per lingua | La scelta a mano può non avere effetto | Si mostrano le voci elencate e si verifica sul telefono quale suona |
| Voci di rete | Senza connessione non parlano | Preferenza per voci locali; errore mostrato come pausa |
| Chrome interrompe le letture lunghe | Frasi tagliate | Una frase alla volta |

## Decisioni

Prese all'approvazione, al posto delle domande aperte della proposta:

1. **Attesa dopo una domanda**: 7 secondi prima della risposta, saltabili con un tocco.
2. **Domande in ascolto**: si leggono sempre; nessuna impostazione per escluderle nella prima versione.
3. **Capitolo successivo**: l'ascolto non continua da solo, si ferma dopo il riassunto, perché mindmap e flashcard chiedono di guardare lo schermo.

## Riferimenti

- [MDN: SpeechSynthesis](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis)
- [Readium: SpeechSynthesis in browsers and OSes](https://readium.org/speech/docs/WebSpeech.html)
- [WebKit bug 198277: audio delle web app installate fermato uscendo dall'app](https://bugs.webkit.org/show_bug.cgi?id=198277)
- [PhET: interruzione delle letture lunghe in Chrome](https://github.com/phetsims/utterance-queue/issues/60)
