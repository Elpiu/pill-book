---
type: C4 Component
title: Sessione di capitolo
status: stable
groma:
  id: sessione
  parent: lettore
  code:
    - scanner: vue
      file: web/app/pages/book/[bookId]/ch/[chId].vue
    - scanner: typescript
      file: web/app/composables/useSession.ts
      symbol: useSession
    - scanner: vue
      file: web/app/composables/useSession.ts
    - scanner: vue
      file: web/app/components/session/SessionComplete.vue
  group: Sessione di lettura
description: Guida le fasi card, riassunto, mindmap e flashcard e salva la posizione a ogni passo.
---

Riaprendo un capitolo si riprende dalla card e dalla fase esatte; un capitolo completato si rilegge senza cambiare il progresso. Alla fine mostra il riepilogo della sessione.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/pages/book/[bookId]/ch/[chId].vue](../../../../../../web/app/pages/book/%5BbookId%5D/ch/%5BchId%5D.vue) | [web/app/components/session/CardDeck.vue](../../../../../../web/app/components/session/CardDeck.vue) | Mostra le card | componente Vue |
| [web/app/pages/book/[bookId]/ch/[chId].vue](../../../../../../web/app/pages/book/%5BbookId%5D/ch/%5BchId%5D.vue) | [web/app/components/session/SummaryView.vue](../../../../../../web/app/components/session/SummaryView.vue) | Mostra il riassunto | componente Vue |
| [web/app/pages/book/[bookId]/ch/[chId].vue](../../../../../../web/app/pages/book/%5BbookId%5D/ch/%5BchId%5D.vue) | [web/app/components/session/MindmapView.vue](../../../../../../web/app/components/session/MindmapView.vue) | Mostra la mindmap | componente Vue |
| [web/app/pages/book/[bookId]/ch/[chId].vue](../../../../../../web/app/pages/book/%5BbookId%5D/ch/%5BchId%5D.vue) | [web/app/components/session/FlashcardDeck.vue](../../../../../../web/app/components/session/FlashcardDeck.vue) | Propone le flashcard | componente Vue |
| [web/app/composables/useSession.ts](../../../../../../web/app/composables/useSession.ts) | [web/app/db/index.ts](../../../../../../web/app/db/index.ts) | Salva posizione ed esiti | chiamata TypeScript |
| [web/app/composables/useSession.ts](../../../../../../web/app/composables/useSession.ts) | [web/app/utils/progress.ts](../../../../../../web/app/utils/progress.ts) | Calcola l'avanzamento | chiamata TypeScript |
