---
type: C4 Component
title: Client OpenRouter
status: stable
groma:
  id: openrouter-client
  parent: generatore
  code:
    - scanner: python
      file: generator/src/bookpack/llm/openrouter.py
    - scanner: python
      file: generator/src/bookpack/llm/catalog.py
  technology: SDK openai, HTTPS
  group: Accesso all'LLM
description: Invia le richieste a OpenRouter e legge il catalogo di modelli, prezzi e limiti.
---

Chiede lo schema JSON ai soli provider che lo rispettano e, se nessuno lo supporta, lo mette nel prompt. Imposta il ragionamento `low` dove disponibile e ritenta a 64.000 token una risposta troncata. Traduce gli errori di OpenRouter in messaggi chiari. Il catalogo resta in cache per 24 ore.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [generator/src/bookpack/llm/openrouter.py](../../../../../../generator/src/bookpack/llm/openrouter.py) | [openrouter](../../../../../externals/openrouter.md) | Chiede le risposte | HTTPS, chat completions |
| [generator/src/bookpack/llm/catalog.py](../../../../../../generator/src/bookpack/llm/catalog.py) | [openrouter](../../../../../externals/openrouter.md) | Legge il catalogo | HTTPS, cache di 24 ore |
