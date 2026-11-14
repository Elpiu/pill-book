---
type: C4 Component
title: Mappa del libro
status: stable
groma:
  id: mappa-libro
  parent: lettore
  code:
    - scanner: vue
      file: web/app/pages/book/[bookId]/map.vue
  group: Schermate
description: Mindmap del libro intero; toccando un capitolo lo si apre.
---

Parte con i soli capitoli aperti, perché con tutti i rami il testo sul telefono diventa illeggibile.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/pages/book/[bookId]/map.vue](../../../../../../web/app/pages/book/%5BbookId%5D/map.vue) | [web/app/db/index.ts](../../../../../../web/app/db/index.ts) | Legge il libro | chiamata TypeScript |
| [web/app/pages/book/[bookId]/map.vue](../../../../../../web/app/pages/book/%5BbookId%5D/map.vue) | [web/app/components/session/MindmapView.vue](../../../../../../web/app/components/session/MindmapView.vue) | Disegna la mappa | componente Vue |
