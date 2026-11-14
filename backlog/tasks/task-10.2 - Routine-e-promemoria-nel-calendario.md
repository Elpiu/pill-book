---
id: TASK-10.2
title: Routine e promemoria nel calendario
status: Done
assignee:
  - '@claude'
created_date: '2026-11-14T21:45:00Z'
updated_date: '2026-11-14T21:57:00Z'
labels:
  - lettore
dependencies:
  - TASK-10.1
documentation:
  - backlog/docs/doc-2 - PRD-routine-di-lettura.md
modified_files:
  - web/app/utils/calendar.ts
  - web/app/utils/routine.ts
  - web/app/composables/useRoutine.ts
  - web/app/components/routine/RoutineForm.vue
  - web/app/components/routine/ReminderCard.vue
  - web/app/pages/routine.vue
  - web/tests/calendar.test.ts
  - docs/web.md
parent_task_id: TASK-10
priority: medium
type: feature
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Le abitudini si agganciano a un momento preciso della giornata, e senza un promemoria è facile dimenticarsene. Senza backend l'unico promemoria affidabile su iPhone e Android è un evento nel calendario, che però l'app non può più cancellare: per questo la serie scade da sola.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Nella pagina Routine si scelgono obiettivo (5, 10, 15 o 20 minuti), orario e appiglio, salvati nell'impostazione routine
- [x] #2 Aggiungi al calendario produce un file .ics conforme (CRLF, righe ripiegate, testo con escape, ora locale, RRULE giornaliera per 30 giorni, avviso) su iPhone e un link a Google Calendar con il fuso del dispositivo altrove, con l'altra strada come alternativa
- [x] #3 L'app ricorda la scadenza; nell'ultima settimana, se l'utente ha letto negli ultimi 3 giorni, propone il rinnovo con una serie che parte dal giorno dopo la scadenza
- [x] #4 Cambiando orario ricorda di cancellare il vecchio evento; istruzioni per togliere il promemoria
- [x] #5 Test per file .ics, link di Google Calendar, scadenza e rinnovo
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Lint e test verdi: ruff e pytest in generator/, ESLint, nuxt typecheck e vitest in web/
- [x] #2 README e docs/ aggiornati, compreso docs/status.md
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. utils/calendar.ts, puro: file .ics conforme (CRLF, righe ripiegate a 75 byte UTF-8, testo con escape, DTSTART in ora locale senza fuso, DURATION dall'obiettivo, RRULE:FREQ=DAILY;COUNT=30, avviso all'inizio) e link a Google Calendar con date, ricorrenza e fuso del dispositivo.
2. utils/routine.ts: inizio di un nuovo promemoria (oggi se l'orario non è passato, altrimenti domani; dopo la scadenza per un rinnovo), ultimo giorno, stato del promemoria (assente, attivo, in scadenza, scaduto), proposta di rinnovo solo con attività negli ultimi 3 giorni, avviso se l'orario è cambiato.
3. composables/useRoutine.ts: impostazione routine e registro dal database, streak, setter.
4. pages/routine.vue: sezioni La tua routine (obiettivo, orario, appiglio con suggerimenti) e Promemoria (iPhone file .ics, altrove Google Calendar, alternativa sempre disponibile, scadenza, rinnovo, cambio orario, come toglierlo).
5. Test e prova nel browser.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verifiche nel browser integrato a 375 px: obiettivo 15, orario 07:30 e appiglio salvati; trovato e corretto un bug di salvataggi ravvicinati che si cancellavano (ora lettura e scrittura in una transazione). Google Calendar riceve titolo, date 07:30-07:45 dal giorno dopo (orario già passato), RRULE giornaliera per 30 giorni e fuso Europe/Rome; scadenza salvata al 14 dicembre. Cambio orario: avviso con nuovo evento che parte subito e aggiorna l'orario del promemoria. Scadenza simulata a 3 giorni: compare il rinnovo; il file .ics del rinnovo parte il 18 novembre, dopo la scadenza, con la durata dell'obiettivo e l'appiglio nella descrizione, e viene scaricato. Test: calendar.test (ics, ripiegatura in byte, escape, link, mezzanotte, dispositivo, scadenza e rinnovo). Lettore: 122 test, lint e typecheck verdi. Da provare su telefono: apertura del file .ics su iPhone, anche dall'app installata.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Routine e promemoria: pagina /routine con obiettivo, orario e appiglio; promemoria come evento ricorrente per 30 giorni, file .ics su iPhone e iPad e link a Google Calendar altrove, con l'alternativa sempre disponibile; scadenza ricordata, rinnovo nell'ultima settimana con serie che parte dopo la scadenza, avviso al cambio di orario, istruzioni per toglierlo. Logica pura in utils/calendar.ts e utils/routine.ts, stato in composables/useRoutine.ts.
<!-- SECTION:FINAL_SUMMARY:END -->
