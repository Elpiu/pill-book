---
type: C4 Component
title: Logica della routine
status: stable
groma:
  id: logica-routine
  parent: lettore
  code:
    - scanner: typescript
      file: web/app/utils/routine.ts
    - scanner: vue
      file: web/app/utils/routine.ts
    - scanner: typescript
      file: web/app/composables/useRoutine.ts
    - scanner: vue
      file: web/app/composables/useRoutine.ts
  group: Routine
description: Registro per giorno, obiettivo, streak con giorno libero, frase del giorno e calendario.
---

Funzioni pure su giorni locali: una giornata è riuscita quando i minuti raggiungono l'obiettivo e resta tale; in ogni settimana un giorno saltato non interrompe la serie; oggi non la interrompe mai. Calcola anche record, intensità del calendario, scadenza e rinnovo del promemoria. Il composable useRoutine le collega al database e salva l'impostazione routine in una transazione.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/composables/useRoutine.ts](../../../../../../web/app/composables/useRoutine.ts) | [web/app/db/index.ts](../../../../../../web/app/db/index.ts) | Legge il registro | chiamata TypeScript |
| [web/app/composables/useRoutine.ts](../../../../../../web/app/composables/useRoutine.ts) | [web/app/utils/calendar.ts](../../../../../../web/app/utils/calendar.ts) | Prepara il promemoria | chiamata TypeScript |
