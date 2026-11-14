---
id: TASK-2
title: Rigenerare con il formato v2 i pack ancora in v1
status: Done
assignee: []
created_date: '2026-11-13T21:34:00Z'
updated_date: '2026-11-13T23:22:00Z'
labels:
  - generatore
dependencies: []
documentation:
  - docs/decisions.md
priority: medium
type: chore
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
L'import rifiuta i pack v1. I libri già importati restano leggibili, ma senza domande durante la lettura, riassunto e card dense. In generator/out/ ci sono ancora pack v1 di libri personali, che restano fuori dal repository.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Ogni pack in generator/out/ ha schemaVersion 2 e passa bookpack validate
- [x] #2 I pack rigenerati si importano nell'app pubblicata
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Nessun pack di libri sotto copyright aggiunto al repository
<!-- DOD:END -->
