---
type: C4 Component
title: Minuti di lettura attiva
status: stable
groma:
  id: minuti-attivi
  parent: lettore
  code:
    - scanner: typescript
      file: web/app/composables/useReadingTimer.ts
    - scanner: vue
      file: web/app/composables/useReadingTimer.ts
  group: Routine
description: Conta il tempo di lettura con la pagina visibile e l'utente presente, e lo aggiunge al registro.
---

Usato nella sessione e nel ripasso. Presente vuol dire un'interazione negli ultimi 3 minuti oppure l'ascolto in corso. Salva ogni 30 secondi, quando la pagina si nasconde e all'uscita; i salti dei timer in background non contano. Quando il registro segnala l'obiettivo raggiunto, fa partire il festeggiamento.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/composables/useReadingTimer.ts](../../../../../../web/app/composables/useReadingTimer.ts) | [web/app/db/index.ts](../../../../../../web/app/db/index.ts) | Aggiunge al registro | chiamata TypeScript |
