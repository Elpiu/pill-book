---
type: C4 System
title: Bookpack
status: stable
groma:
  id: bookpack
description: Trasforma libri in PDF in percorsi di lettura a pillole e li fa leggere sul telefono.
---

Due applicazioni indipendenti, collegate solo dal formato del pack. Il **generatore** gira sul computer di chi prepara i libri e chiama un LLM tramite OpenRouter. Il **lettore** è un sito statico pubblicato su GitHub Pages, che funziona anche offline. Il contratto tra i due è lo schema JSON in `schema/bookpack.schema.json`, generato dai modelli del generatore.
