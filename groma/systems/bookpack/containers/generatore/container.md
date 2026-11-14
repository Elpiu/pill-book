---
type: C4 Container
title: Generatore
status: stable
groma:
  id: generatore
  parent: bookpack
  technology: Python 3.12, PyMuPDF, Pydantic, Typer, Tkinter
description: Converte un PDF in un pack chiamando un LLM, da riga di comando o da una finestra.
---

Si usa sul computer di chi prepara i libri, con il comando `bookpack` o la finestra Tkinter. Estrae il testo dal PDF, divide il libro in capitoli, condensa ogni parte con un LLM e scrive `generator/out/<id>.bookpack.json`. Le risposte dell'LLM restano in una cache su disco e un file di stato accanto al pack permette di riprendere una generazione interrotta. Impostazioni e chiave arrivano da `generator/.env`.
