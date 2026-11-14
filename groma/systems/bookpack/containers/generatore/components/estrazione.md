---
type: C4 Component
title: Estrazione del testo
status: stable
groma:
  id: estrazione
  parent: generatore
  code:
    - scanner: python
      file: generator/src/bookpack/extract/pdf.py
    - scanner: python
      file: generator/src/bookpack/extract/clean.py
    - scanner: python
      file: generator/src/bookpack/extract/lang.py
      symbol: detect_lang
    - scanner: python
      file: generator/src/bookpack/extract/__init__.py
  technology: PyMuPDF
  group: Pipeline del pack
description: Legge il PDF pagina per pagina, lo ripulisce e ne riconosce la lingua.
---

Estrae testo, font e posizione di ogni riga, e rifiuta i PDF senza testo, che richiedono l'OCR. La pulizia toglie intestazioni e piè di pagina ripetuti, numeri di pagina e sillabazione, anche a cavallo di due pagine.
