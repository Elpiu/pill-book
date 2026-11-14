---
type: C4 Component
title: Logica del progresso
status: stable
groma:
  id: progresso
  parent: lettore
  code:
    - scanner: typescript
      file: web/app/utils/progress.ts
    - scanner: vue
      file: web/app/utils/progress.ts
  group: Dati locali
description: Calcola avanzamento, stato delle tappe e completamento, e fonde progressi diversi.
---

Funzioni pure, coperte da test. Se un pack aggiornato perde capitoli o card, il progresso relativo viene ignorato senza errori.
