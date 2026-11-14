---
type: C4 Component
title: Percorso del libro
status: stable
groma:
  id: percorso
  parent: lettore
  code:
    - scanner: vue
      file: web/app/pages/book/[bookId]/index.vue
    - scanner: vue
      file: web/app/components/book/ChapterStep.vue
    - scanner: vue
      file: web/app/components/book/OverviewPanel.vue
  group: Schermate
description: Panoramica, idee portanti, tappe dei capitoli con il loro stato e glossario.
---

Le tappe mostrano se un capitolo è da fare, in corso o completato, e quanto dura la sessione.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/pages/book/[bookId]/index.vue](../../../../../../web/app/pages/book/%5BbookId%5D/index.vue) | [web/app/db/index.ts](../../../../../../web/app/db/index.ts) | Legge libro e progresso | chiamata TypeScript |
| [web/app/pages/book/[bookId]/index.vue](../../../../../../web/app/pages/book/%5BbookId%5D/index.vue) | [web/app/utils/progress.ts](../../../../../../web/app/utils/progress.ts) | Calcola lo stato delle tappe | chiamata TypeScript |
