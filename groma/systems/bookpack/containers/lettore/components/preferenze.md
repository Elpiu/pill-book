---
type: C4 Component
title: Preferenze
status: stable
groma:
  id: preferenze
  parent: lettore
  code:
    - scanner: typescript
      file: web/app/composables/useSettings.ts
    - scanner: vue
      file: web/app/composables/useSettings.ts
    - scanner: typescript
      file: web/app/plugins/settings.client.ts
    - scanner: vue
      file: web/app/plugins/settings.client.ts
  group: Dati locali
description: Tema e dimensione del testo, salvati nel browser e ripristinati all'avvio.
---

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/composables/useSettings.ts](../../../../../../web/app/composables/useSettings.ts) | [web/app/db/index.ts](../../../../../../web/app/db/index.ts) | Salva le preferenze | chiamata TypeScript |
