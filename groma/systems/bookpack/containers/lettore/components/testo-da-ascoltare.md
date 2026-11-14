---
type: C4 Component
title: Testo da ascoltare
status: stable
groma:
  id: testo-da-ascoltare
  parent: lettore
  code:
    - scanner: typescript
      file: web/app/utils/listening.ts
    - scanner: vue
      file: web/app/utils/listening.ts
  group: Ascolto
description: Trasforma card e riassunto in frasi e pause da leggere in modalità ascolto.
---

Segue la tabella del PRD della modalità ascolto: solo testo del libro, nessuna parola dell'interfaccia, codice escluso, passi separati da pause, 7 secondi per pensare dopo una domanda e risposta marcata, così la sessione può mostrarla sulla card.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/utils/listening.ts](../../../../../../web/app/utils/listening.ts) | [web/app/utils/speech.ts](../../../../../../web/app/utils/speech.ts) | Divide in frasi | chiamata TypeScript |
