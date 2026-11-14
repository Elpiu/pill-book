---
id: TASK-8
title: Modalità ascolto delle pillole
status: Done
assignee:
  - '@claude'
created_date: '2026-11-14T16:16:00Z'
updated_date: '2026-11-14T20:55:00Z'
labels:
  - lettore
dependencies: []
documentation:
  - backlog/docs/doc-1 - PRD-modalità-ascolto.md
modified_files:
  - docs/status.md
priority: medium
type: feature
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Le pillole oggi si possono solo leggere, ma ci sono momenti in cui ascoltare costa meno che guardare lo schermo: in movimento, con gli occhi stanchi. Il PRD in doc-1, approvato, sceglie la sintesi vocale del browser: nessuna dipendenza, nessun costo, funziona offline e non cambia il formato del pack. Chi vuole solo leggere non deve trovarsi niente di nuovo da gestire.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Su un telefono vero un capitolo si ascolta dalla prima card alla fine del riassunto senza toccare lo schermo
- [x] #2 Un libro in italiano e uno in inglese vengono letti ciascuno con una voce della propria lingua; per una lingua senza voci il pulsante è disattivato e lo spiega
- [x] #3 Passando tra ascolto e lettura, e riaprendo il capitolo, la posizione è sempre l'ultima card raggiunta
- [x] #4 In modalità aereo, con una voce locale, l'ascolto funziona
- [x] #5 Bloccando lo schermo l'ascolto va in pausa e riprende con un tocco dalla frase interrotta
- [x] #6 Con il pulsante nascosto dalle impostazioni la sessione è identica a quella di oggi
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Lint e test verdi: ruff e pytest in generator/, ESLint, nuxt typecheck e vitest in web/
- [x] #2 README e docs/ aggiornati, compreso docs/status.md
<!-- DOD:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Le tre sottoattività sono chiuse (8.1 modulo vocale, 8.2 ascolto nella sessione, 8.3 impostazioni). Verificato nel browser integrato il criterio 6: con il pulsante nascosto la sessione mostra lo spazio vuoto di prima. Restano da provare su un telefono vero i criteri 1-5: capitolo ascoltato fino al riassunto senza toccare lo schermo, voci italiana e inglese, posizione tra ascolto e lettura, modalità aereo con voce locale, pausa e ripresa con lo schermo bloccato. Il browser integrato non ha voci reali e lo schermo bloccato si è potuto solo simulare.

Per il criterio 2 c'è ora anche la versione inglese del libro d'esempio (how-to-live-on-24-hours-a-day-en), proposta dall'app accanto a quella italiana: in home a libreria vuota e nella scheda Da URL dell'importazione.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Modalità ascolto completa: modulo vocale riusabile e testo da leggere (TASK-8.1), ascolto nella sessione con pulsante, barra, avanzamento automatico, domande con 7 secondi e riassunto (TASK-8.2), impostazioni con visibilità del pulsante, velocità e voce per lingua (TASK-8.3). Aggiunta la versione inglese del libro d'esempio per provare due lingue. Criteri 1-5 verificati dall'utente su telefono e su Chrome, criterio 6 nel browser integrato. Lettore: lint, typecheck e 87 test verdi; generatore: ruff e 161 test verdi.
<!-- SECTION:FINAL_SUMMARY:END -->
