---
type: Groma Flow
title: Importare e leggere un capitolo
groma:
  id: importare-e-leggere-un-capitolo
---

Chi legge importa sul telefono il pack ricevuto come file, poi lo legge a sessioni. Tutto resta nel browser e funziona anche offline.

## Steps

| From | To | Action |
| --- | --- | --- |
| [Chi legge](../actors/chi-legge.md) | [Importazione](../systems/bookpack/containers/lettore/components/importazione.md) | Importa il file del pack |
| [Importazione](../systems/bookpack/containers/lettore/components/importazione.md) | [Validazione dei pack](../systems/bookpack/containers/lettore/components/validazione.md) | Controlla schema e vincoli |
| [Importazione](../systems/bookpack/containers/lettore/components/importazione.md) | [Archivio locale](../systems/bookpack/containers/lettore/components/archivio.md) | Salva il libro |
| [Chi legge](../actors/chi-legge.md) | [Sessione di capitolo](../systems/bookpack/containers/lettore/components/sessione.md) | Apre un capitolo |
| [Sessione di capitolo](../systems/bookpack/containers/lettore/components/sessione.md) | [Mazzo di card](../systems/bookpack/containers/lettore/components/mazzo-card.md) | Scorre card e domande durante la lettura |
| [Sessione di capitolo](../systems/bookpack/containers/lettore/components/sessione.md) | [Flashcard](../systems/bookpack/containers/lettore/components/flashcard.md) | Propone le flashcard di fine capitolo |
| [Sessione di capitolo](../systems/bookpack/containers/lettore/components/sessione.md) | [Archivio locale](../systems/bookpack/containers/lettore/components/archivio.md) | Salva posizione ed esiti a ogni passo |
| [Archivio locale](../systems/bookpack/containers/lettore/components/archivio.md) | [Scatole di Leitner](../systems/bookpack/containers/lettore/components/leitner.md) | Fissa quando ogni domanda tornerà |
