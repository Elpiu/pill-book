---
type: C4 Component
title: Rilevamento dei capitoli
status: stable
groma:
  id: capitoli
  parent: generatore
  code:
    - scanner: python
      file: generator/src/bookpack/extract/toc.py
    - scanner: python
      file: generator/src/bookpack/condense/detect.py
  group: Pipeline del pack
description: 'Divide il libro in capitoli: da file YAML, indice del PDF, titoli nel testo o LLM.'
---

Prova le fonti in quest'ordine e si ferma alla prima affidabile. L'LLM entra in gioco solo se le altre falliscono. Esclude copertina, indici e bibliografia, e permette di correggere a mano i confini; la divisione si esporta e si rilegge come YAML.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [generator/src/bookpack/condense/detect.py](../../../../../../generator/src/bookpack/condense/detect.py) | [generator/src/bookpack/llm/structured.py](../../../../../../generator/src/bookpack/llm/structured.py) | Chiede i capitoli | chiamata Python |
