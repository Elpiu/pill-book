---
id: TASK-8.1
title: Modulo vocale e testo da leggere
status: Done
assignee:
  - '@claude'
created_date: '2026-11-14T16:17:00Z'
updated_date: '2026-11-14T16:41:00Z'
labels:
  - lettore
dependencies: []
documentation:
  - backlog/docs/doc-1 - PRD-modalità-ascolto.md
modified_files:
  - web/app/utils/speech.ts
  - web/app/utils/listening.ts
  - web/app/composables/useSpeech.ts
  - web/tests/speech.test.ts
  - web/tests/listening.test.ts
  - web/tests/useSpeech.test.ts
  - docs/web.md
  - docs/status.md
  - docs/decisions.md
  - groma/systems/bookpack/containers/lettore/components/sintesi-vocale.md
  - groma/systems/bookpack/containers/lettore/components/testo-da-ascoltare.md
parent_task_id: TASK-8
priority: medium
type: feature
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
La sintesi vocale del browser ha comportamenti diversi tra Chrome, Android e iPhone: voci che arrivano in ritardo, codici di lingua scritti in modi diversi, letture lunghe interrotte, pausa che su Android non riprende. Tenerli in un modulo che non sa nulla di card e libri lo rende riusabile e verificabile. Separare la trasformazione delle card in testo permette di controllare con i test cosa viene letto.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Il modulo vocale non dipende da card né libri ed espone voci, scelta della voce per lingua, coda di frasi, pausa, ripresa, stop, velocità e stato
- [x] #2 La voce automatica rispetta l'ordine del PRD: lingua e regione, voci locali, voci di qualità migliore, voce predefinita; it_IT e it-IT sono equivalenti
- [x] #3 Ogni tipo di card e il riassunto diventano frasi e pause come nella tabella del PRD: codice non letto, nessuna parola dell'interfaccia, 7 secondi dopo una domanda
- [x] #4 Le frasi lunghe vengono divise; pausa e ripresa ripartono dall'inizio della frase corrente
- [x] #5 Le voci si caricano anche quando l'elenco iniziale è vuoto o l'evento voiceschanged non arriva
- [x] #6 Test per trasformazione del testo, divisione delle frasi e scelta della voce
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Lint e test verdi: ruff e pytest in generator/, ESLint, nuxt typecheck e vitest in web/
- [x] #2 README e docs/ aggiornati, compreso docs/status.md
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. utils/speech.ts, generico: normalizzazione delle lingue (it_IT = it-IT), divisione in frasi con Intl.Segmenter e ripiego a regex, frasi lunghe spezzate alle pause della punteggiatura, classifica delle voci nell'ordine del PRD.
2. utils/listening.ts, specifico di Bookpack: card e riassunto diventano frasi e pause secondo la tabella del PRD; codice escluso, nessuna parola dell'interfaccia, attesa di 7 secondi dopo le domande, risposta marcata per la UI.
3. composables/useSpeech.ts: incapsula speechSynthesis senza sapere nulla di libri; coda di frasi, pausa e ripresa dalla frase corrente con cancel e nuovo avvio, stop, velocità, stato, conto alla rovescia delle attese, caricamento delle voci con voiceschanged e ripiego a polling. speechSynthesis e il costruttore dell'utterance si possono iniettare, per testarlo senza browser.
4. Test Vitest per divisione delle frasi, scelta della voce, script delle card e coda del modulo con un sintetizzatore finto.
5. Prova nel browser integrato con le voci reali di Chromium; lint, typecheck, test; documentazione e mappa di Groma.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verifiche: 37 test nuovi (speech, listening, useSpeech con sintetizzatore finto); prova nel browser integrato con il sintetizzatore vero di Chromium a volume zero: coda con pausa, ripresa, attesa per pensare e cambio di velocità arrivata a 'done', card vera del libro d'esempio letta fino in fondo in 56 secondi. Il browser integrato non espone voci (getVoices vuoto anche dopo 3 secondi): ha esercitato il ripiego a polling, ma la scelta tra voci reali è provata solo dai test. Lettore: lint, typecheck e 73 test verdi; generatore: ruff e 161 test verdi.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Base della modalità ascolto, non ancora visibile nell'app. composables/useSpeech.ts incapsula speechSynthesis senza sapere nulla di libri: coda di frasi e pause, una frase alla volta (Chrome interrompe le letture lunghe), pausa e ripresa con cancel e nuovo avvio (pause() su Android non riprende), velocità, stato, conto alla rovescia delle attese da saltare, caricamento delle voci con voiceschanged e ripiego a polling; play non aspetta nulla, così parte dal tocco anche su iPhone. utils/speech.ts normalizza le lingue, divide in frasi con Intl.Segmenter e sceglie la voce nell'ordine del PRD. utils/listening.ts trasforma card e riassunto secondo la tabella del PRD, con 7 secondi dopo le domande e la risposta marcata. Documentazione e mappa di Groma aggiornate. Da verificare su telefono vero: qualità e scelta delle voci reali, comportamento di iOS e Android; se ne occupa TASK-8 con le sue prove.
<!-- SECTION:FINAL_SUMMARY:END -->
