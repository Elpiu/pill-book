---
id: doc-2
title: 'PRD: routine di lettura'
type: specification
created_date: '2026-11-14T21:45:00Z'
updated_date: '2026-11-14T21:45:00Z'
---
# PRD: routine di lettura

| | |
|---|---|
| Stato | Approvato il 14 novembre 2026 |
| Parte | Lettore (`web/`) |
| Formato del pack | Invariato |
| Branch | `feature/routine-lettura` |

## Problema

Bookpack funziona quando si torna a leggere un po' ogni giorno: le card sono pensate per sessioni brevi e il ripasso richiama le domande nei giorni successivi. Oggi però niente aiuta a tornare. L'app non sa quanto si è letto ieri, non propone un obiettivo e non ricorda di aprirla.

## Obiettivi

1. **Un obiettivo quotidiano piccolo**, in minuti di lettura attiva, scelto dall'utente.
2. **Una routine agganciata a un momento della giornata**: orario e appiglio ("dopo il caffè").
3. **Una streak che premia la costanza senza punire**: un giorno saltato a settimana non la interrompe.
4. **Un promemoria nel calendario del telefono**, senza backend, che si spegne da solo se l'app non si usa più.
5. **Rinforzi leggeri**: la scheda Oggi, il calendario delle giornate, i festeggiamenti all'obiettivo raggiunto.
6. Tutto **locale e offline**, incluso nell'export del progresso.

## Non obiettivi

- Notifiche push o qualunque server.
- Punti, livelli, classifiche e traguardi: valutabili dopo questa versione.
- Statistiche avanzate per libro o per argomento.
- Sincronizzazione tra dispositivi: è la bozza della sincronizzazione con Google Drive.

## Definizioni

- **Minuti di lettura attiva**: tempo con una sessione di capitolo o il ripasso aperti, la pagina visibile e l'utente presente. Presente vuol dire un'interazione negli ultimi 3 minuti (le card dense si leggono anche a lungo senza toccare) oppure l'ascolto in corso. Libreria, percorso e impostazioni non contano.
- **Giorno**: la data locale del dispositivo, da mezzanotte a mezzanotte.
- **Giornata riuscita**: i minuti attivi del giorno hanno raggiunto l'obiettivo valido in quel momento. Una volta riuscita resta tale anche se poi l'obiettivo cambia.
- **Streak**: le giornate riuscite consecutive. In ogni settimana, da lunedì a domenica, un solo giorno non riuscito viene coperto come giorno libero e non interrompe la serie, senza aggiungersi al conteggio. Oggi, finché non è finito, non interrompe mai la serie.
- **Record**: la streak più lunga mai raggiunta, con la stessa regola.

## Esperienza

### Prima volta

Dopo il primo libro importato, in home compare la scheda **Oggi** con l'invito "Scegli il tuo obiettivo". Non è una finestra bloccante. Finché l'utente non sceglie, vale un obiettivo di 10 minuti.

### Pagina Routine (`/routine`)

- **Oggi**: minuti letti rispetto all'obiettivo, streak, giorno libero della settimana già usato o no, record.
- **Calendario**: le ultime 12 settimane, un quadrato per giorno, con intensità secondo i minuti e un segno sulle giornate riuscite. Toccando un giorno si leggono minuti, card, risposte e capitoli.
- **La tua routine**: obiettivo (5, 10, 15 o 20 minuti), orario, appiglio scelto da alcuni suggerimenti o scritto a mano.
- **Promemoria**: vedi sotto.

Dalle impostazioni e dalla scheda Oggi si arriva qui.

### Scheda Oggi in home

Sopra **Riprendi**: un anello con i minuti di oggi sull'obiettivo, la streak e una frase che cambia con la situazione:

| Situazione | Frase |
|---|---|
| Obiettivo raggiunto | "Obiettivo raggiunto: 12 giorni di fila" |
| Non ancora raggiunto, streak in corso | "Mancano 4 minuti per arrivare a 13 giorni" |
| Streak a zero dopo un periodo di pausa | "Ricomincia oggi: bastano 10 minuti", mai "hai perso la serie" |
| Promemoria in scadenza e utente attivo | "Il promemoria scade giovedì: rinnovalo" |

### Festeggiamenti

- Quando durante la lettura si raggiunge l'obiettivo del giorno, un messaggio breve: "Obiettivo di oggi raggiunto · 13 giorni di fila". Una volta al giorno.
- La schermata di capitolo completato riporta i minuti di oggi e la streak.

## Promemoria nel calendario

L'app non può creare notifiche senza server, né modificare o cancellare eventi già nel calendario: per questo il promemoria è un evento ricorrente **a scadenza**.

- **Evento**: ogni giorno all'orario della routine, lungo quanto l'obiettivo, con avviso all'inizio. Titolo "Bookpack: 10 minuti di lettura", descrizione con l'appiglio e il link che apre l'app.
- **Durata della serie**: 30 giorni, poi gli avvisi smettono da soli. Se l'utente abbandona l'app, entro un mese non riceve più nulla senza dover fare niente.
- **Rinnovo**: l'app ricorda la data di scadenza. Nell'ultima settimana, se l'utente ha letto negli ultimi 3 giorni, propone **Rinnova per altri 30 giorni**. La nuova serie parte dal giorno dopo la scadenza, così non si sovrappone.
- **Come si aggiunge**:
  - iPhone e iPad: file `.ics`, che Safari propone di aggiungere al calendario;
  - Android e computer: link a Google Calendar con la ricorrenza compilata;
  - in entrambi i casi l'altra strada resta disponibile come alternativa.
- **Cambiare orario**: si aggiunge un nuovo evento dal giorno dopo e l'app ricorda di cancellare il vecchio.
- **Toglierlo prima**: istruzioni nella pagina Routine. Si apre l'evento "Bookpack" nel calendario e si eliminano tutti gli eventi futuri.

## Dati

- **Tabella `activity`** in IndexedDB, una riga per giorno: `day`, `seconds`, `cards`, `answers`, `chapters`, `met`.
  - `cards` conta i passaggi in avanti tra le card;
  - `answers` conta le risposte a flashcard, domande e ripasso;
  - `chapters` conta i capitoli completati;
  - `met` diventa vero quando i minuti raggiungono l'obiettivo.
- **Impostazione `routine`**: obiettivo in minuti, orario, appiglio, scadenza del promemoria.
- **Export del progresso, versione 3**: include `activity`. Fondendo, per ogni giorno vince il valore più alto di ciascun campo e `met` è vero se lo è in una delle due parti. Gli export delle versioni 1 e 2 si importano ancora.
- Le giornate precedenti alla funzione non si ricostruiscono: la streak parte dal primo giorno con il registro.

## Requisiti tecnici

1. Logica pura e testata in `utils/routine.ts`: giorni locali, streak con giorno libero, record, calendario, frase della scheda Oggi, scadenza e rinnovo del promemoria.
2. Contatore dei minuti attivi come composable, con orologio iniettabile per i test. Scrive nel database al massimo ogni 30 secondi, quando la pagina si nasconde e all'uscita.
3. `utils/calendar.ts`: file `.ics` conforme a RFC 5545 (righe CRLF ripiegate a 75 caratteri, testo con escape, ora locale senza fuso, `RRULE:FREQ=DAILY;COUNT=30`, avviso) e link a Google Calendar con il fuso del dispositivo.
4. Nessuna dipendenza nuova e nessun cambio al formato del pack.

## Criteri di accettazione

- Leggere una sessione o fare il ripasso fa crescere i minuti di oggi; restare fermi oltre 3 minuti, o con la pagina nascosta, no; l'ascolto conta anche senza toccare lo schermo.
- Raggiunto l'obiettivo, la giornata è riuscita, compare il messaggio una sola volta e la streak sale.
- Un giorno saltato in una settimana non interrompe la streak, due sì; oggi non la interrompe mai.
- Scheda Oggi, pagina Routine e calendario mostrano dati coerenti con il registro.
- Il promemoria si aggiunge su iPhone con il file `.ics` e su Android con Google Calendar, scade dopo 30 giorni e si rinnova senza sovrapporsi.
- Export e import portano il registro; gli export vecchi si importano ancora.
- Test per streak, calendario, contatore, file `.ics` e link; lint, typecheck e test verdi; documentazione aggiornata.

## Rischi

| Rischio | Gestione |
|---|---|
| Il file `.ics` da un'app installata su iPhone potrebbe non aprire il calendario | Prova su telefono; il link a Google Calendar resta un'alternativa |
| Il link di Google Calendar non è documentato ufficialmente | Usato solo come comodità, il file `.ics` è lo standard |
| Minuti contati in modo impreciso, per esempio con un telefono appoggiato e la pagina accesa | Soglia di 3 minuti senza interazioni; la precisione non è l'obiettivo |
| Una streak che stressa | Giorno libero settimanale e frasi senza colpa |
