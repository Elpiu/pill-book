---
type: C4 Component
title: Impostazioni
status: stable
groma:
  id: impostazioni
  parent: lettore
  code:
    - scanner: vue
      file: web/app/pages/settings.vue
    - scanner: vue
      file: web/app/components/settings/ListenSettings.vue
  group: Schermate
description: Tema, testo, ascolto, installazione, export e import del progresso, eliminazione.
---

L'export del progresso è l'unico modo di conservare i dati fuori dal browser o di spostarli su un altro dispositivo.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/pages/settings.vue](../../../../../../web/app/pages/settings.vue) | [web/app/db/index.ts](../../../../../../web/app/db/index.ts) | Esporta, importa, elimina | chiamata TypeScript |
| [web/app/pages/settings.vue](../../../../../../web/app/pages/settings.vue) | [web/app/composables/useSettings.ts](../../../../../../web/app/composables/useSettings.ts) | Cambia le preferenze | chiamata TypeScript |
| [web/app/components/settings/ListenSettings.vue](../../../../../../web/app/components/settings/ListenSettings.vue) | [web/app/composables/useListenSettings.ts](../../../../../../web/app/composables/useListenSettings.ts) | Salva le scelte dell'ascolto | chiamata TypeScript |
| [web/app/components/settings/ListenSettings.vue](../../../../../../web/app/components/settings/ListenSettings.vue) | [web/app/composables/useSpeech.ts](../../../../../../web/app/composables/useSpeech.ts) | Elenca e prova le voci | chiamata TypeScript |
