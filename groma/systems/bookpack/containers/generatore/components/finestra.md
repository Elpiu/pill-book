---
type: C4 Component
title: Finestra
status: stable
groma:
  id: finestra
  parent: generatore
  code:
    - scanner: python
      file: generator/src/bookpack/gui.py
    - scanner: python
      file: generator/src/bookpack/gui_viewer.py
  technology: Tkinter, PyMuPDF
  group: Interfacce
description: Interfaccia per scegliere il PDF, controllare e correggere i capitoli, generare e riprendere.
---

Mostra le pagine del PDF accanto all'elenco dei capitoli, così si verificano e si correggono i confini prima di generare. La generazione gira in un thread e comunica con l'interfaccia tramite una coda. **Riprendi** ritrova una generazione incompleta dello stesso PDF e ne ripristina capitoli, spunte, modello e lingua.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [generator/src/bookpack/gui.py](../../../../../../generator/src/bookpack/gui.py) | [generator/src/bookpack/extract/pdf.py](../../../../../../generator/src/bookpack/extract/pdf.py) | Legge il PDF | chiamata Python |
| [generator/src/bookpack/gui.py](../../../../../../generator/src/bookpack/gui.py) | [generator/src/bookpack/extract/toc.py](../../../../../../generator/src/bookpack/extract/toc.py) | Rileva i capitoli | chiamata Python |
| [generator/src/bookpack/gui.py](../../../../../../generator/src/bookpack/gui.py) | [generator/src/bookpack/condense/estimate.py](../../../../../../generator/src/bookpack/condense/estimate.py) | Stima il costo | chiamata Python |
| [generator/src/bookpack/gui.py](../../../../../../generator/src/bookpack/gui.py) | [generator/src/bookpack/condense/pipeline.py](../../../../../../generator/src/bookpack/condense/pipeline.py) | Avvia la generazione | chiamata Python |
| [generator/src/bookpack/gui.py](../../../../../../generator/src/bookpack/gui.py) | [generator/src/bookpack/config.py](../../../../../../generator/src/bookpack/config.py) | Legge le impostazioni | chiamata Python |
| [generator/src/bookpack/gui.py](../../../../../../generator/src/bookpack/gui.py) | [generator/src/bookpack/llm/__init__.py](../../../../../../generator/src/bookpack/llm/__init__.py) | Sceglie il provider | chiamata Python |
| [generator/src/bookpack/gui.py](../../../../../../generator/src/bookpack/gui.py) | [generator/src/bookpack/llm/catalog.py](../../../../../../generator/src/bookpack/llm/catalog.py) | Cerca i modelli | chiamata Python |
