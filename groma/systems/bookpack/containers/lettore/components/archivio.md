---
type: C4 Component
title: Archivio locale
status: stable
groma:
  id: archivio
  parent: lettore
  code:
    - scanner: typescript
      file: web/app/db/index.ts
    - scanner: vue
      file: web/app/db/index.ts
    - scanner: typescript
      file: web/app/composables/useLiveQuery.ts
      symbol: useLiveQuery
    - scanner: vue
      file: web/app/composables/useLiveQuery.ts
  technology: Dexie, IndexedDB
  group: Dati locali
description: Database del browser con libri, progresso, impostazioni e ripassi, più export e import.
---

Tutte le scritture passano da qui. L'import fonde i dati: vince il punto più avanzato di ogni capitolo e l'esito più recente di ogni domanda. Le query si aggiornano da sole quando i dati cambiano.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/db/index.ts](../../../../../../web/app/db/index.ts) | [web/app/utils/progress.ts](../../../../../../web/app/utils/progress.ts) | Fonde i progressi | chiamata TypeScript |
| [web/app/db/index.ts](../../../../../../web/app/db/index.ts) | [web/app/utils/review.ts](../../../../../../web/app/utils/review.ts) | Fissa il prossimo ripasso | chiamata TypeScript |
| [web/app/db/index.ts](../../../../../../web/app/db/index.ts) | [web/app/utils/routine.ts](../../../../../../web/app/utils/routine.ts) | Aggiorna la giornata | chiamata TypeScript |
