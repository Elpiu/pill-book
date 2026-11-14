---
id: TASK-10.1
title: Registro dell'attività, minuti attivi e streak
status: Done
assignee:
  - '@claude'
created_date: '2026-11-14T21:45:00Z'
updated_date: '2026-11-14T21:51:00Z'
labels:
  - lettore
dependencies: []
documentation:
  - backlog/docs/doc-2 - PRD-routine-di-lettura.md
modified_files:
  - web/app/utils/routine.ts
  - web/app/composables/useReadingTimer.ts
  - web/app/db/index.ts
  - web/app/utils/progress.ts
  - web/app/composables/useSession.ts
  - web/app/pages/book/[bookId]/ch/[chId].vue
  - web/app/pages/review.vue
  - web/tests/routine.test.ts
  - web/tests/readingTimer.test.ts
  - web/tests/progress.test.ts
  - docs/web.md
parent_task_id: TASK-10
priority: medium
type: feature
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Oggi l'app tiene solo istantanee: ultima apertura, capitoli completati, esiti. Senza uno storico per giorno non si possono calcolare obiettivo, streak e calendario. È la base delle altre due parti della routine.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Tabella activity in IndexedDB con una riga per giorno locale: secondi, card, risposte, capitoli e giornata riuscita
- [x] #2 Sessioni di capitolo e ripasso contano i minuti solo con la pagina visibile e un'interazione negli ultimi 3 minuti, oppure con l'ascolto in corso; scrittura al massimo ogni 30 secondi, quando la pagina si nasconde e all'uscita
- [x] #3 Card in avanti, risposte e capitoli completati incrementano il registro del giorno
- [x] #4 La giornata diventa riuscita quando i minuti raggiungono l'obiettivo del momento, e resta tale se l'obiettivo cambia
- [x] #5 Streak con un giorno libero per settimana da lunedì a domenica, oggi che non la interrompe mai, e record con la stessa regola
- [x] #6 Export del progresso versione 3 con il registro e fusione per giorno; gli export delle versioni 1 e 2 si importano ancora
- [x] #7 Test per giorni locali, streak, record, contatore dei minuti e fusione del registro
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Lint e test verdi: ruff e pytest in generator/, ESLint, nuxt typecheck e vitest in web/
- [x] #2 README e docs/ aggiornati, compreso docs/status.md
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. utils/routine.ts, puro: giorni locali (chiave YYYY-MM-DD, somma di giorni, lunedì della settimana), applyActivity con soglia dell'obiettivo e met che resta vero, mergeActivity, streak corrente con un giorno libero per settimana e oggi in sospeso, record come massimo delle streak che finiscono in ogni giornata riuscita.
2. composables/useReadingTimer.ts con createActiveTimer puro e orologio iniettabile: conta i secondi con pagina visibile e interazione negli ultimi 3 minuti o ascolto in corso, limita i salti dopo un periodo in background, scrive ogni 30 secondi, quando la pagina si nasconde e all'uscita.
3. db: versione 3 con la tabella activity; addActivity che legge l'obiettivo dall'impostazione routine e segnala quando l'obiettivo viene raggiunto; card in avanti in useSession.setCard, capitoli in complete, risposte in recordReview; Azzera tutto svuota anche il registro.
4. Export versione 3 con il registro, fusione per giorno, import delle versioni 1 e 2.
5. Contatore nella sessione (ascolto compreso) e nel ripasso. Test di tutto il puro e del contatore.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verifiche nel browser integrato: database passato alla versione 3; in una sessione tre frecce e interazioni periodiche hanno scritto 3 card e 30 secondi al primo salvataggio; una risposta 'Lo sapevo' ha portato answers a 1; exportProgress in versione 3 con activity; addActivity a 590 secondi non riuscita, a 620 riuscita con reachedGoal vero una sola volta; importProgress in fusione ha tenuto il massimo per campo e aggiunto il giorno mancante. Test: routine.test (giorni, registro, streak con giorno libero, record), readingTimer.test (visibilità, 3 minuti, ascolto, salti in background, secondi interi), progress.test (export versione 3). Lettore: 111 test e typecheck verdi; generatore non toccato (ruff e 164 test verdi all'ultimo giro).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Base della routine: tabella activity (Dexie versione 3) con una riga per giorno locale; contatore dei minuti attivi nella sessione, ascolto compreso, e nel ripasso; card in avanti, risposte e capitoli completati nel registro; giornata riuscita al raggiungimento dell'obiettivo (10 minuti per default) con segnale per il festeggiamento; streak con un giorno libero per settimana e record in utils/routine.ts; export del progresso versione 3 con fusione per giorno; Azzera tutto svuota anche il registro.
<!-- SECTION:FINAL_SUMMARY:END -->
