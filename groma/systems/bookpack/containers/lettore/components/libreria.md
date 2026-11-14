---
type: C4 Component
title: Libreria
status: stable
groma:
  id: libreria
  parent: lettore
  code:
    - scanner: vue
      file: web/app/pages/index.vue
    - scanner: vue
      file: web/app/components/book/BookCard.vue
    - scanner: typescript
      file: web/app/composables/useLibrary.ts
    - scanner: vue
      file: web/app/composables/useLibrary.ts
  group: Schermate
description: 'Home: libri importati, Riprendi, Ripasso di oggi e libro d''esempio.'
---

Mostra ogni libro con la sua percentuale di avanzamento e propone di riprendere l'ultimo capitolo aperto.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/composables/useLibrary.ts](../../../../../../web/app/composables/useLibrary.ts) | [web/app/db/index.ts](../../../../../../web/app/db/index.ts) | Legge libri e progresso | Dexie liveQuery |
| [web/app/composables/useLibrary.ts](../../../../../../web/app/composables/useLibrary.ts) | [web/app/utils/progress.ts](../../../../../../web/app/utils/progress.ts) | Calcola l'avanzamento | chiamata TypeScript |
| [web/app/composables/useLibrary.ts](../../../../../../web/app/composables/useLibrary.ts) | [web/app/utils/review.ts](../../../../../../web/app/utils/review.ts) | Conta i ripassi dovuti | chiamata TypeScript |
