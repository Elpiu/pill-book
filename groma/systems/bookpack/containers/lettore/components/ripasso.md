---
type: C4 Component
title: Ripasso
status: stable
groma:
  id: ripasso
  parent: lettore
  code:
    - scanner: vue
      file: web/app/pages/review.vue
  group: Schermate
description: Le domande da ripassare oggi, da tutti i libri.
---

L'elenco si fissa all'apertura: una domanda sbagliata torna domani, non nello stesso giro.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/pages/review.vue](../../../../../../web/app/pages/review.vue) | [web/app/components/session/FlashcardDeck.vue](../../../../../../web/app/components/session/FlashcardDeck.vue) | Propone le domande | componente Vue |
| [web/app/pages/review.vue](../../../../../../web/app/pages/review.vue) | [web/app/db/index.ts](../../../../../../web/app/db/index.ts) | Registra i ripassi | chiamata TypeScript |
| [web/app/pages/review.vue](../../../../../../web/app/pages/review.vue) | [web/app/utils/review.ts](../../../../../../web/app/utils/review.ts) | Sceglie le domande dovute | chiamata TypeScript |
