---
type: C4 Component
title: Chiamate LLM validate
status: stable
groma:
  id: chiamate-llm
  parent: generatore
  code:
    - scanner: python
      file: generator/src/bookpack/llm/structured.py
    - scanner: python
      file: generator/src/bookpack/cache.py
    - scanner: python
      file: generator/src/bookpack/llm/base.py
    - scanner: python
      file: generator/src/bookpack/llm/__init__.py
      symbol: get_provider
  group: Accesso all'LLM
description: Chiede output JSON con schema, lo valida, ritenta passando gli errori e tiene la cache.
---

Astrazione comune ai provider. Ogni risposta valida si conserva in cache sotto il prompt iniziale; quelle scartate vengono tolte, così un rilancio chiede davvero una risposta nuova. Sceglie il provider, OpenRouter o finto, in base alla configurazione. Si usa da più thread.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [generator/src/bookpack/llm/structured.py](../../../../../../generator/src/bookpack/llm/structured.py) | [generator/src/bookpack/llm/openrouter.py](../../../../../../generator/src/bookpack/llm/openrouter.py) | Invia le richieste | chiamata Python |
| [generator/src/bookpack/llm/structured.py](../../../../../../generator/src/bookpack/llm/structured.py) | [generator/src/bookpack/llm/fake.py](../../../../../../generator/src/bookpack/llm/fake.py) | Invia le richieste di prova | chiamata Python |
