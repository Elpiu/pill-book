---
id: TASK-10.3
title: Scheda Oggi, calendario e festeggiamenti
status: Done
assignee:
  - '@claude'
created_date: '2026-11-14T21:46:00Z'
updated_date: '2026-11-14T22:06:00Z'
labels:
  - lettore
dependencies:
  - TASK-10.1
documentation:
  - backlog/docs/doc-2 - PRD-routine-di-lettura.md
modified_files:
  - web/app/utils/routine.ts
  - web/app/composables/useRoutine.ts
  - web/app/components/routine/TodayCard.vue
  - web/app/components/routine/RoutineStats.vue
  - web/app/components/routine/ReadingCalendar.vue
  - web/app/pages/routine.vue
  - web/app/pages/index.vue
  - web/app/pages/settings.vue
  - web/app/components/session/SessionComplete.vue
  - web/app/pages/book/[bookId]/ch/[chId].vue
  - web/app/pages/review.vue
  - web/tests/routine.test.ts
  - docs/web.md
  - docs/decisions.md
  - docs/status.md
  - README.md
  - groma/systems/bookpack/containers/lettore/components/archivio.md
  - groma/systems/bookpack/containers/lettore/components/libreria.md
  - groma/systems/bookpack/containers/lettore/components/ripasso.md
  - groma/systems/bookpack/containers/lettore/components/sessione.md
  - groma/systems/bookpack/containers/lettore/components/logica-routine.md
  - groma/systems/bookpack/containers/lettore/components/minuti-attivi.md
  - groma/systems/bookpack/containers/lettore/components/pagina-routine.md
  - groma/systems/bookpack/containers/lettore/components/promemoria.md
  - groma/systems/bookpack/containers/lettore/components/scheda-oggi.md
parent_task_id: TASK-10
priority: medium
type: feature
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Il registro serve solo se si vede: la scheda Oggi dà un motivo per aprire una sessione, il calendario mostra la costanza, il festeggiamento rinforza il gesto appena fatto. Le frasi non devono mai far sentire in colpa dopo una pausa.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 In home, sopra Riprendi, la scheda Oggi mostra minuti sull'obiettivo, streak e la frase giusta tra obiettivo raggiunto, minuti mancanti, ricomincia oggi e promemoria in scadenza; senza routine scelta invita a sceglierla
- [x] #2 La pagina Routine mostra oggi, record, giorno libero della settimana e il calendario delle ultime 12 settimane, con il dettaglio di un giorno al tocco
- [x] #3 Raggiunto l'obiettivo durante la lettura compare il messaggio di festeggiamento, una volta al giorno
- [x] #4 La schermata di capitolo completato riporta minuti di oggi e streak
- [x] #5 Dalle impostazioni si arriva alla pagina Routine
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Lint e test verdi: ruff e pytest in generator/, ESLint, nuxt typecheck e vitest in web/
- [x] #2 README e docs/ aggiornati, compreso docs/status.md
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. utils/routine.ts: frase della scheda Oggi (obiettivo raggiunto, minuti mancanti al giorno successivo della serie, ricomincia oggi dopo una pausa, primo giorno), minuti mancanti, settimane del calendario da lunedì con livello di intensità rispetto all'obiettivo e giorni futuri.
2. Componenti: TodayCard in home sopra Riprendi (anello dei minuti, streak, frase, invito a scegliere l'obiettivo, rinnovo del promemoria), RoutineStats e ReadingCalendar in cima a /routine (dettaglio di un giorno al tocco).
3. Festeggiamento: messaggio quando il registro segnala l'obiettivo raggiunto, in sessione e nel ripasso; minuti di oggi e streak nella schermata di capitolo completato.
4. Impostazioni: collegamento alla pagina Routine.
5. Test e prova nel browser con giornate simulate.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verifiche nel browser integrato a 375 px con giornate simulate (quattro riuscite, giovedì saltato, oggi 4 min 40 s su 5): scheda Oggi '4 / 5 min', serie 4, 'Manca 1 minuto per arrivare a 5 giorni', invito al rinnovo del promemoria; pagina Routine con 4 giorni di fila, record 4, giorno libero già usato, calendario con intensità corrette e dettaglio di mercoledì 11; in sessione, superato l'obiettivo, messaggio 'Obiettivo di oggi raggiunto, 5 giorni di fila' una volta; schermata di capitolo completato con 'Oggi 5 minuti, obiettivo raggiunto · 5 giorni di fila'; impostazioni con il collegamento /routine. Corretto 'Mancano 1 minuto' in 'Manca 1 minuto'. L'icona della fiamma non compariva nel server di sviluppo avviato prima dei file nuovi: la build di produzione contiene tutte le icone nuove. Lettore: 127 test, lint e typecheck verdi; generatore non toccato.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Scheda Oggi in home con anello dei minuti, streak e frase senza colpa; pagina Routine con riepilogo, record, giorno libero e calendario delle ultime 12 settimane con dettaglio al tocco; festeggiamento all'obiettivo raggiunto in sessione e nel ripasso; minuti e streak nella schermata di capitolo completato; collegamento dalle impostazioni. Frase e calendario sono funzioni pure testate in utils/routine.ts.
<!-- SECTION:FINAL_SUMMARY:END -->
