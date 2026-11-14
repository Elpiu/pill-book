---
type: C4 Component
title: Regia dell'ascolto
status: stable
groma:
  id: regia-ascolto
  parent: lettore
  code:
    - scanner: typescript
      file: web/app/composables/useListening.ts
    - scanner: vue
      file: web/app/composables/useListening.ts
    - scanner: vue
      file: web/app/components/session/ListenBar.vue
  technology: Vue
  group: Ascolto
description: Legge le card una dopo l'altra e il riassunto, con la barra di controllo.
---

Parte dal pulsante con le cuffie della sessione. Fa avanzare le card al ritmo della voce, riparte dalla card raggiunta a mano, rivela la risposta delle domande dopo i 7 secondi per pensare e alla fine si ferma sulla mindmap. Non tocca pagina né database: chiede alla sessione di spostarsi con delle callback. La barra offre velocità, card precedente e successiva, pausa e chiusura, e mostra stato e conto alla rovescia.

## Derived relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/components/session/ListenBar.vue](../../../../../../web/app/components/session/ListenBar.vue) | [web/app/pages/book/[bookId]/ch/[chId].vue](../../../../../../web/app/pages/book/%5BbookId%5D/ch/%5BchId%5D.vue) | Invokes supplied callback: rate | vue |

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/composables/useListening.ts](../../../../../../web/app/composables/useListening.ts) | [web/app/composables/useSpeech.ts](../../../../../../web/app/composables/useSpeech.ts) | Legge le frasi | chiamata TypeScript |
| [web/app/composables/useListening.ts](../../../../../../web/app/composables/useListening.ts) | [web/app/utils/listening.ts](../../../../../../web/app/utils/listening.ts) | Prepara il testo | chiamata TypeScript |
