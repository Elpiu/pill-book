---
type: C4 Component
title: PWA e build
status: stable
groma:
  id: pwa
  parent: lettore
  code:
    - scanner: typescript
      file: web/nuxt.config.ts
    - scanner: vue
      file: web/nuxt.config.ts
    - scanner: vue
      file: web/app/components/common/InstallBanner.vue
  technology: '@vite-pwa/nuxt, Workbox'
description: Configurazione di Nuxt, manifest, service worker per l'offline e invito a installare.
---

Il service worker precarica app, font latini, icone e pack d'esempio; tutte le route ripiegano su `index.html`. La base URL arriva da `NUXT_APP_BASE_URL`, così la stessa build funziona sotto `/nome-repo/` su GitHub Pages. Sulla home, l'invito a installare compare se il browser lo consente.
