---
type: C4 Component
title: Stima dei costi
status: stable
groma:
  id: stima
  parent: generatore
  code:
    - scanner: python
      file: generator/src/bookpack/condense/estimate.py
description: Prevede chiamate, token e costo di una generazione prima di spendere.
---

Usa caratteri/4 per l'input e valori misurati su generazioni reali per l'output. La CLI e la finestra la mostrano prima di chiedere conferma.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [generator/src/bookpack/condense/estimate.py](../../../../../../generator/src/bookpack/condense/estimate.py) | [generator/src/bookpack/condense/chunking.py](../../../../../../generator/src/bookpack/condense/chunking.py) | Divide in parti | chiamata Python |
