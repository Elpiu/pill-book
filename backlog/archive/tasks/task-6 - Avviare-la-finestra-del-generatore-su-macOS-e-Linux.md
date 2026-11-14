---
id: TASK-6
title: Avviare la finestra del generatore su macOS e Linux
status: To Do
assignee: []
created_date: '2026-11-13T21:34:00Z'
updated_date: '2026-11-13T23:22:00Z'
labels:
  - verifica
  - generatore
dependencies: []
documentation:
  - docs/generator.md
priority: low
type: task
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
La finestra Tkinter e l'anteprima PDF sono state provate solo su Windows. Font, dialoghi e gestione dei thread possono comportarsi in modo diverso altrove.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Su macOS e su Linux la finestra si apre, carica un PDF, mostra l'anteprima e genera con Prova gratis
- [ ] #2 Eventuali pacchetti di sistema necessari, come python3-tk, sono indicati in docs/generator.md
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Esiti riportati in docs/status.md, nella tabella di ciò che è verificato o non verificato
<!-- DOD:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-11-13T23:22:00Z

---

Annullata: la finestra dipende da Python e Tkinter, la resa su macOS e Linux non è una priorità.

---
<!-- COMMENTS:END -->
