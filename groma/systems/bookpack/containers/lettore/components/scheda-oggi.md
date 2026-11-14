---
type: C4 Component
title: Scheda Oggi
status: stable
groma:
  id: scheda-oggi
  parent: lettore
  code:
    - scanner: vue
      file: web/app/components/routine/TodayCard.vue
  group: Routine
description: 'In home, sopra Riprendi: minuti di oggi sull''obiettivo, streak e frase del giorno.'
---

La frase cambia con la situazione e dopo una pausa invita a ricominciare, senza parlare di serie perse. Senza routine scelta invita a sceglierla; con il promemoria in scadenza e letture recenti propone il rinnovo.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/components/routine/TodayCard.vue](../../../../../../web/app/components/routine/TodayCard.vue) | [web/app/composables/useRoutine.ts](../../../../../../web/app/composables/useRoutine.ts) | Legge streak e minuti | chiamata TypeScript |
