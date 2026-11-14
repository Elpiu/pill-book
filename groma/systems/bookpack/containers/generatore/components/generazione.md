---
type: C4 Component
title: Generazione del pack
status: stable
groma:
  id: generazione
  parent: generatore
  code:
    - scanner: python
      file: generator/src/bookpack/condense/pipeline.py
    - scanner: python
      file: generator/src/bookpack/condense/tasks.py
    - scanner: python
      file: generator/src/bookpack/condense/state.py
    - scanner: python
      file: generator/src/bookpack/condense/__init__.py
  group: Pipeline del pack
description: Coordina le chiamate per fasi, in parallelo, e tiene il file di stato per riprendere.
---

Esegue prima tutte le parti, poi la chiusura dei capitoli, infine la panoramica, con più chiamate insieme in thread separati. Una chiamata fallita non ferma le altre; un errore che le riguarda tutte, come chiave o credito, ferma i nuovi avvii. Dopo ogni attività aggiorna `<id>.state.json`; alla fine assembla il pack e lo valida.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [generator/src/bookpack/condense/pipeline.py](../../../../../../generator/src/bookpack/condense/pipeline.py) | [generator/src/bookpack/condense/chapter.py](../../../../../../generator/src/bookpack/condense/chapter.py) | Condensa le parti | chiamata Python |
| [generator/src/bookpack/condense/pipeline.py](../../../../../../generator/src/bookpack/condense/pipeline.py) | [generator/src/bookpack/extract/lang.py](../../../../../../generator/src/bookpack/extract/lang.py) | Riconosce la lingua | chiamata Python |
| [generator/src/bookpack/condense/pipeline.py](../../../../../../generator/src/bookpack/condense/pipeline.py) | [generator/src/bookpack/models.py](../../../../../../generator/src/bookpack/models.py) | Assembla il pack | chiamata Python |
| [generator/src/bookpack/condense/pipeline.py](../../../../../../generator/src/bookpack/condense/pipeline.py) | [generator/src/bookpack/validate.py](../../../../../../generator/src/bookpack/validate.py) | Valida il pack | chiamata Python |
