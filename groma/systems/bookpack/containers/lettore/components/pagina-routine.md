---
type: C4 Component
title: Pagina Routine
status: stable
groma:
  id: pagina-routine
  parent: lettore
  code:
    - scanner: vue
      file: web/app/pages/routine.vue
    - scanner: vue
      file: web/app/components/routine/RoutineForm.vue
    - scanner: vue
      file: web/app/components/routine/RoutineStats.vue
    - scanner: vue
      file: web/app/components/routine/ReadingCalendar.vue
  group: Routine
description: Oggi, record, calendario delle ultime 12 settimane, obiettivo, orario, appiglio e promemoria.
---

Toccando un giorno del calendario si leggono minuti, card, risposte e capitoli. Si raggiunge dalla scheda Oggi, dalla fine di un capitolo e dalle impostazioni.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/pages/routine.vue](../../../../../../web/app/pages/routine.vue) | [web/app/composables/useRoutine.ts](../../../../../../web/app/composables/useRoutine.ts) | Legge e salva la routine | chiamata TypeScript |
