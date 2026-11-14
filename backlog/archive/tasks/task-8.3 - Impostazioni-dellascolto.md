---
id: TASK-8.3
title: Impostazioni dell'ascolto
status: Done
assignee:
  - '@claude'
created_date: '2026-11-14T16:17:00Z'
updated_date: '2026-11-14T17:03:00Z'
labels:
  - lettore
dependencies:
  - TASK-8.1
documentation:
  - backlog/docs/doc-1 - PRD-modalità-ascolto.md
modified_files:
  - web/app/components/settings/ListenSettings.vue
  - web/app/pages/settings.vue
  - docs/web.md
  - docs/status.md
  - README.md
  - groma/systems/bookpack/containers/lettore/components/impostazioni.md
parent_task_id: TASK-8
priority: low
type: feature
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Chi legge soltanto deve poter togliere il pulsante; chi ascolta deve poter scegliere una voce migliore di quella automatica, che dipende molto dal dispositivo. Le voci di qualità vanno spesso installate dal sistema, e senza indicazioni pochi sanno dove trovarle.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 La sezione Ascolto compare solo dove la sintesi vocale esiste
- [x] #2 Mostra il pulsante Ascolta è attivo per default e, se disattivato, toglie il pulsante dalla sessione
- [x] #3 Velocità predefinita e voce per ciascuna lingua dei libri presenti si salvano nelle impostazioni ed entrano nell'export del progresso
- [x] #4 Prova legge una frase con la voce scelta; una voce non più disponibile torna alla scelta automatica senza errori
- [x] #5 Indicazioni per installare voci migliori su iPhone e Android
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Lint e test verdi: ruff e pytest in generator/, ESLint, nuxt typecheck e vitest in web/
- [x] #2 README e docs/ aggiornati, compreso docs/status.md
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. components/settings/ListenSettings.vue, mostrato solo dove esiste la sintesi vocale: interruttore Mostra il pulsante Ascolta, velocità predefinita, una voce per ciascuna lingua dei libri presenti (Automatica più le voci della lingua, in ordine di preferenza) con Prova, indicazioni per installare voci migliori su iPhone e Android.
2. Una voce salvata ma non più presente si mostra come Automatica; la lettura usa già la scelta automatica.
3. settings.vue: la sezione nella pagina e il ripristino delle preferenze dell'ascolto dopo l'import del progresso.
4. Prova nel browser integrato, con voci simulate per la select; lint, typecheck, test; docs.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verifiche nel browser integrato a 375 px: senza voci elencate la sezione lo dice; con voci simulate (Luca, Alice Enhanced, Elsa di rete, Daniel inglese) la select mostra Automatica (Alice), Alice, Luca, Elsa con 'serve la rete' e nessuna voce inglese; scelta salvata come {it: luca}; Prova legge la prima frase del libro con Luca a 1,2×; tolta Luca, la select torna su Automatica e la prova usa Alice senza errori; interruttore spento salvato e pulsante assente nella sessione dopo un caricamento completo; exportProgress contiene listenRate, listenShowButton, listenVoices. Senza sintesi vocale la sezione non compare (stessa condizione speech.supported verificata in TASK-8.2). Lettore: lint, typecheck e 86 test verdi; generatore: ruff e 161 test verdi.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Sezione Ascolto nelle impostazioni (components/settings/ListenSettings.vue), solo dove esiste la sintesi vocale: interruttore Mostra il pulsante Ascolta, velocità predefinita, una voce per ciascuna lingua dei libri presenti con Prova su una frase del libro, indicazioni per installare voci migliori su iPhone e Android. Una voce salvata che non c'è più si mostra e si usa come automatica. Le preferenze stanno nella tabella settings, quindi entrano nell'export, e si ripristinano anche dopo un import del progresso. Da verificare sul telefono le voci reali, in TASK-8.
<!-- SECTION:FINAL_SUMMARY:END -->
