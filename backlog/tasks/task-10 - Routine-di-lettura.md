---
id: TASK-10
title: Routine di lettura
status: In Progress
assignee:
  - '@claude'
created_date: '2026-11-14T21:45:00Z'
updated_date: '2026-11-14T22:06:00Z'
labels:
  - lettore
dependencies: []
documentation:
  - backlog/docs/doc-2 - PRD-routine-di-lettura.md
priority: medium
type: feature
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Bookpack funziona se si torna a leggere un po' ogni giorno, ma oggi niente aiuta a tornare: l'app non sa quanto si è letto, non propone un obiettivo e non ricorda di aprirla. Il PRD in doc-2, approvato, sceglie minuti di lettura attiva come obiettivo, una streak con un giorno libero a settimana, un promemoria a scadenza nel calendario del telefono e una gamification leggera, tutto senza backend.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Su un telefono vero, leggere fa crescere i minuti di oggi e raggiungere l'obiettivo fa salire la streak con il messaggio di festeggiamento
- [ ] #2 Il promemoria si aggiunge al calendario su iPhone con il file .ics e su Android con Google Calendar, all'orario scelto
- [ ] #3 Dopo alcuni giorni d'uso scheda Oggi, calendario e streak riflettono le giornate lette, giorno libero compreso
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Lint e test verdi: ruff e pytest in generator/, ESLint, nuxt typecheck e vitest in web/
- [ ] #2 README e docs/ aggiornati, compreso docs/status.md
<!-- DOD:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Sottoattività chiuse: 10.1 registro, minuti attivi e streak; 10.2 routine e promemoria; 10.3 scheda Oggi, calendario e festeggiamenti. Tutto verificato nel browser integrato con giornate simulate. Restano da provare su telefono i tre criteri: minuti e festeggiamento leggendo davvero, promemoria con il file .ics su iPhone (anche dall'app installata) e con Google Calendar su Android, e più giorni reali d'uso con il giorno libero.
<!-- SECTION:NOTES:END -->
