---
type: C4 Component
title: Provider finto
status: stable
groma:
  id: provider-finto
  parent: generatore
  code:
    - scanner: python
      file: generator/src/bookpack/llm/fake.py
  group: Accesso all'LLM
description: 'Compone risposte meccaniche dal testo, senza rete né chiave: per test e prove gratis.'
---

Usato con `--fake` o **Prova gratis**. Il risultato è valido ma non è una condensazione: serve a provare pipeline e divisione in capitoli.
