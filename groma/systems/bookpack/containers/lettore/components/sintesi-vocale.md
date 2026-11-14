---
type: C4 Component
title: Sintesi vocale
status: stable
groma:
  id: sintesi-vocale
  parent: lettore
  code:
    - scanner: typescript
      file: web/app/composables/useSpeech.ts
    - scanner: vue
      file: web/app/composables/useSpeech.ts
    - scanner: typescript
      file: web/app/utils/speech.ts
    - scanner: vue
      file: web/app/utils/speech.ts
  technology: Web Speech API
  group: Ascolto
description: Legge una coda di frasi e pause con le voci del dispositivo, senza sapere nulla di libri.
---

Incapsula speechSynthesis del browser: carica le voci anche quando arrivano in ritardo, sceglie la migliore per una lingua (stessa regione, voci locali, voci migliorate, predefinita) e legge una frase alla volta, perché Chrome interrompe le letture lunghe. Pausa e ripresa ripartono dall'inizio della frase con cancel e un nuovo avvio, perché pause() su Android non riprende. Gestisce velocità, stato e il conto alla rovescia delle attese da saltare. Pensato per essere riusato in altre app.
