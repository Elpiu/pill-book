---
type: C4 Component
title: CLI
status: stable
groma:
  id: cli
  parent: generatore
  code:
    - scanner: python
      file: generator/src/bookpack/cli.py
    - scanner: python
      file: generator/src/bookpack/__init__.py
  technology: Typer, Rich
  group: Interfacce
description: 'Il comando bookpack: inspect, build, resume, toc, models, validate e schema.'
---

Punto d'ingresso da terminale. Prima di spendere mostra capitoli e costo stimato e chiede conferma; durante la generazione stampa l'avanzamento e, se qualcosa manca, il comando `bookpack resume` per riprendere. Contiene anche la versione del pacchetto, scritta in ogni pack.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [generator/src/bookpack/cli.py](../../../../../../generator/src/bookpack/cli.py) | [generator/src/bookpack/extract/pdf.py](../../../../../../generator/src/bookpack/extract/pdf.py) | Legge il PDF | chiamata Python |
| [generator/src/bookpack/cli.py](../../../../../../generator/src/bookpack/cli.py) | [generator/src/bookpack/extract/toc.py](../../../../../../generator/src/bookpack/extract/toc.py) | Rileva i capitoli | chiamata Python |
| [generator/src/bookpack/cli.py](../../../../../../generator/src/bookpack/cli.py) | [generator/src/bookpack/condense/estimate.py](../../../../../../generator/src/bookpack/condense/estimate.py) | Stima il costo | chiamata Python |
| [generator/src/bookpack/cli.py](../../../../../../generator/src/bookpack/cli.py) | [generator/src/bookpack/condense/pipeline.py](../../../../../../generator/src/bookpack/condense/pipeline.py) | Avvia la generazione | chiamata Python |
| [generator/src/bookpack/cli.py](../../../../../../generator/src/bookpack/cli.py) | [generator/src/bookpack/config.py](../../../../../../generator/src/bookpack/config.py) | Legge le impostazioni | chiamata Python |
| [generator/src/bookpack/cli.py](../../../../../../generator/src/bookpack/cli.py) | [generator/src/bookpack/llm/__init__.py](../../../../../../generator/src/bookpack/llm/__init__.py) | Sceglie il provider | chiamata Python |
| [generator/src/bookpack/cli.py](../../../../../../generator/src/bookpack/cli.py) | [generator/src/bookpack/llm/catalog.py](../../../../../../generator/src/bookpack/llm/catalog.py) | Cerca i modelli | chiamata Python |
| [generator/src/bookpack/cli.py](../../../../../../generator/src/bookpack/cli.py) | [generator/src/bookpack/models.py](../../../../../../generator/src/bookpack/models.py) | Esporta lo schema | chiamata Python |
| [generator/src/bookpack/cli.py](../../../../../../generator/src/bookpack/cli.py) | [generator/src/bookpack/validate.py](../../../../../../generator/src/bookpack/validate.py) | Valida un pack | chiamata Python |
