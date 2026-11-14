---
type: C4 Component
title: Condensazione
status: stable
groma:
  id: condensazione
  parent: generatore
  code:
    - scanner: python
      file: generator/src/bookpack/condense/chapter.py
    - scanner: python
      file: generator/src/bookpack/condense/chunking.py
    - scanner: python
      file: generator/src/bookpack/condense/book.py
    - scanner: python
      file: generator/src/bookpack/condense/prompts/__init__.py
      symbol: render
  group: Pipeline del pack
description: Scrive card, riassunto, flashcard e panoramica del libro a partire dal testo.
---

Divide ogni capitolo in parti di circa 5.000 token e chiede una card ogni 500 parole circa, nella forma adatta al contenuto. Riassunto, mindmap e flashcard si scrivono poi dalle card, non dal testo; la panoramica dalle sintesi dei capitoli. Le citazioni assenti dal testo vengono scartate. I prompt stanno in `condense/prompts/*.md`.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [generator/src/bookpack/condense/chapter.py](../../../../../../generator/src/bookpack/condense/chapter.py) | [generator/src/bookpack/llm/structured.py](../../../../../../generator/src/bookpack/llm/structured.py) | Genera output validato | chiamata Python |
| [generator/src/bookpack/condense/chapter.py](../../../../../../generator/src/bookpack/condense/chapter.py) | [generator/src/bookpack/validate.py](../../../../../../generator/src/bookpack/validate.py) | Controlla card e capitoli | chiamata Python |
