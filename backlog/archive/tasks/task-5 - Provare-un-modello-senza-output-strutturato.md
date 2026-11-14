---
id: TASK-5
title: Provare un modello senza output strutturato
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
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Quando nessun provider supporta lo schema JSON, il client mette lo schema nel prompt e si affida alla validazione locale. Questo ripiego è provato solo con un trasporto HTTP simulato.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Un capitolo generato con un modello senza Schema in bookpack models produce un pack valido
- [ ] #2 Sono annotati quanti ritentativi sono serviti
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Esiti riportati in docs/status.md, nella tabella di ciò che è verificato o non verificato
<!-- DOD:END -->

## Comments

<!-- COMMENTS:BEGIN -->
created: 2026-11-13T23:22:00Z

---

Annullata: fuori scopo. Il ripiego con lo schema nel prompt resta provato solo in simulazione.

---
<!-- COMMENTS:END -->
