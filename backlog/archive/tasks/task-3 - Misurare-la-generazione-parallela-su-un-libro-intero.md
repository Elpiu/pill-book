---
id: TASK-3
title: Misurare la generazione parallela su un libro intero
status: Done
assignee: []
created_date: '2026-11-13T21:34:00Z'
updated_date: '2026-11-13T23:23:00Z'
labels:
  - verifica
  - generatore
dependencies: []
documentation:
  - docs/generator.md
  - docs/status.md
priority: medium
type: spike
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Il default di 4 chiamate insieme è stato misurato solo su 4 capitoli brevi: 125 secondi in sequenza contro 66 in parallelo, un lancio per configurazione. Su un libro lungo non si sa quanto si guadagna né se il provider limita le richieste. Anche Ctrl+C è stato provato solo in simulazione.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Tempi e costo di un libro intero confrontati con 1 e 4 chiamate insieme, stesso modello e cache vuota
- [x] #2 Si sa se il provider ha restituito limiti di richieste e con quale numero di chiamate insieme
- [x] #3 Ctrl+C in un terminale vero ferma i nuovi avvii, e bookpack resume completa il pack senza ripagare
- [x] #4 Il default di BOOKPACK_WORKERS è confermato o cambiato, con il motivo in docs/generator.md
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Esiti riportati in docs/status.md, nella tabella di ciò che è verificato o non verificato
<!-- DOD:END -->
