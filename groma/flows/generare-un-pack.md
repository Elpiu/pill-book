---
type: Groma Flow
title: Generare un pack
groma:
  id: generare-un-pack
---

Da un PDF a `generator/out/<id>.bookpack.json`, da terminale. La finestra segue gli stessi passi. Ogni risposta valida finisce in cache, quindi un'interruzione si riprende con `bookpack resume` senza ripagare.

## Steps

| From | To | Action |
| --- | --- | --- |
| [Chi genera i pack](../actors/chi-genera-i-pack.md) | [CLI](../systems/bookpack/containers/generatore/components/cli.md) | Lancia `bookpack build` sul PDF |
| [CLI](../systems/bookpack/containers/generatore/components/cli.md) | [Rilevamento dei capitoli](../systems/bookpack/containers/generatore/components/capitoli.md) | Divide il libro in capitoli |
| [CLI](../systems/bookpack/containers/generatore/components/cli.md) | [Stima dei costi](../systems/bookpack/containers/generatore/components/stima.md) | Mostra il costo stimato e chiede conferma |
| [CLI](../systems/bookpack/containers/generatore/components/cli.md) | [Generazione del pack](../systems/bookpack/containers/generatore/components/generazione.md) | Avvia le fasi: parti, chiusura dei capitoli, panoramica |
| [Generazione del pack](../systems/bookpack/containers/generatore/components/generazione.md) | [Condensazione](../systems/bookpack/containers/generatore/components/condensazione.md) | Condensa ogni parte, poi chiude ogni capitolo |
| [Condensazione](../systems/bookpack/containers/generatore/components/condensazione.md) | [Chiamate LLM validate](../systems/bookpack/containers/generatore/components/chiamate-llm.md) | Chiede un output conforme allo schema |
| [Chiamate LLM validate](../systems/bookpack/containers/generatore/components/chiamate-llm.md) | [Client OpenRouter](../systems/bookpack/containers/generatore/components/openrouter-client.md) | Invia la richiesta, salvo risposta in cache |
| [Client OpenRouter](../systems/bookpack/containers/generatore/components/openrouter-client.md) | [OpenRouter](../externals/openrouter.md) | Ottiene la risposta del modello |
| [Generazione del pack](../systems/bookpack/containers/generatore/components/generazione.md) | [Formato del pack](../systems/bookpack/containers/generatore/components/formato.md) | Assembla il pack e lo valida prima di scriverlo |
