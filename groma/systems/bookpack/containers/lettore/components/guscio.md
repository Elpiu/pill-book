---
type: C4 Component
title: Guscio dell'app
status: stable
groma:
  id: guscio
  parent: lettore
  code:
    - scanner: vue
      file: web/app/app.vue
    - scanner: vue
      file: web/app/components/common/AppHeader.vue
    - scanner: vue
      file: web/app/components/common/NotFound.vue
    - scanner: typescript
      file: web/app/app.config.ts
    - scanner: vue
      file: web/app/app.config.ts
    - scanner: vue
      file: web/app/components/book/BookCover.vue
  technology: Vue, Nuxt UI
description: Radice dell'app, intestazione, pagina non trovata, copertine e colori del tema.
---

Parti comuni a tutte le schermate.
