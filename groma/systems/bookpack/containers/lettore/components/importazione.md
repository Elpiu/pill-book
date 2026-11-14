---
type: C4 Component
title: Importazione
status: stable
groma:
  id: importazione
  parent: lettore
  code:
    - scanner: vue
      file: web/app/pages/import.vue
    - scanner: typescript
      file: web/app/composables/useImport.ts
      symbol: useImport
    - scanner: vue
      file: web/app/composables/useImport.ts
  group: Schermate
description: Carica un pack da file o URL, lo valida, ne mostra l'anteprima e lo salva.
---

Gli errori di validazione sono spiegati in italiano; un pack già presente si aggiorna senza perdere il progresso dei capitoli che restano.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/composables/useImport.ts](../../../../../../web/app/composables/useImport.ts) | [web/app/utils/validatePack.ts](../../../../../../web/app/utils/validatePack.ts) | Valida il pack | chiamata TypeScript |
| [web/app/composables/useImport.ts](../../../../../../web/app/composables/useImport.ts) | [web/app/db/index.ts](../../../../../../web/app/db/index.ts) | Salva il libro | chiamata TypeScript |
