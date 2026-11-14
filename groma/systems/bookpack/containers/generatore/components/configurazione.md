---
type: C4 Component
title: Configurazione
status: stable
groma:
  id: configurazione
  parent: generatore
  code:
    - scanner: python
      file: generator/src/bookpack/config.py
description: Legge modello, chiave, cartella della cache, contesto e chiamate insieme da .env e ambiente.
---

Le variabili sono `OPENROUTER_API_KEY`, `BOOKPACK_MODEL`, `BOOKPACK_CONTEXT_TOKENS`, `BOOKPACK_CACHE_DIR` e `BOOKPACK_WORKERS`; le opzioni della CLI hanno la precedenza.
