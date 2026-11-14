---
type: C4 Component
title: Scatole di Leitner
status: stable
groma:
  id: leitner
  parent: lettore
  code:
    - scanner: typescript
      file: web/app/utils/review.ts
    - scanner: vue
      file: web/app/utils/review.ts
  group: Dati locali
description: 'Decide quando una domanda torna: dopo 1, 3, 7, 16 o 35 giorni.'
---

Una risposta giusta fa salire di scatola, una sbagliata riporta alla prima. Si ragiona a giorni, non a ore.
