---
type: C4 Component
title: Validazione dei pack
status: stable
groma:
  id: validazione
  parent: lettore
  code:
    - scanner: typescript
      file: web/app/utils/validatePack.ts
    - scanner: vue
      file: web/app/utils/validatePack.ts
  technology: Ajv
  group: Dati locali
description: Controlla un pack contro lo schema JSON e i vincoli prima di importarlo.
---

Usa lo schema generato dal generatore; i tipi TypeScript in `app/types/bookpack.ts` sono generati dallo stesso schema con `pnpm gen:types`. Rifiuta i pack v1 e le versioni future.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/utils/validatePack.ts](../../../../../../web/app/utils/validatePack.ts) | [generator/src/bookpack/models.py](../../../../../../generator/src/bookpack/models.py) | Usa lo schema | schema/bookpack.schema.json, generato |
