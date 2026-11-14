---
id: TASK-4
title: Confrontare più modelli sullo stesso capitolo
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
type: spike
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Tutte le generazioni reali sono state fatte con ~deepseek/deepseek-flash-latest. I costi degli altri modelli sono solo stimati e la qualità della condensazione non è mai stata confrontata, quindi la scelta del modello di default non ha basi misurate.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Lo stesso capitolo è generato con almeno tre modelli, tra cui il default anthropic/claude-sonnet-5.5
- [ ] #2 Per ogni modello sono annotati costo effettivo, ritentativi e un giudizio su fedeltà e chiarezza delle card
- [ ] #3 La tabella dei costi in docs/generator.md riporta i costi reali accanto alle stime
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Esiti riportati in docs/status.md, nella tabella di ciò che è verificato o non verificato
<!-- DOD:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-11-13T23:22:00Z

---

Annullata: il confronto tra modelli non interessa per questo progetto.

---
<!-- COMMENTS:END -->
