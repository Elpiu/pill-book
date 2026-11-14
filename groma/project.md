---
type: Groma Project
title: Bookpack
groma:
  profile: architecture
description: 'Libri condensati in pillole: card, mindmap e flashcard sul telefono.'
---

Bookpack trasforma un libro in PDF in un percorso di lettura a capitoli. Un generatore in Python, usato sul computer, condensa il libro con un LLM e scrive un file `*.bookpack.json`. Un lettore web statico, installabile come PWA, importa quel file e lo fa leggere a sessioni brevi. Non c'è backend: il pack passa da un dispositivo all'altro come file, e i dati di lettura restano nel browser.
