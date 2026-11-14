---
id: TASK-8.2
title: Ascolto nella sessione di capitolo
status: Done
assignee:
  - '@claude'
created_date: '2026-11-14T16:17:00Z'
updated_date: '2026-11-14T16:57:00Z'
labels:
  - lettore
dependencies:
  - TASK-8.1
documentation:
  - backlog/docs/doc-1 - PRD-modalità-ascolto.md
modified_files:
  - web/app/utils/speech.ts
  - web/app/composables/useListening.ts
  - web/app/composables/useListenSettings.ts
  - web/app/plugins/settings.client.ts
  - web/tests/support/fakeSynth.ts
  - web/tests/useSpeech.test.ts
  - web/tests/useListening.test.ts
  - web/tests/speech.test.ts
  - web/app/components/session/ListenBar.vue
  - web/app/components/session/CardDeck.vue
  - web/app/components/session/ConceptCard.vue
  - web/app/components/session/CheckCard.vue
  - web/app/pages/book/[bookId]/ch/[chId].vue
  - docs/web.md
  - docs/status.md
  - groma/systems/bookpack/containers/lettore/components/mazzo-card.md
  - groma/systems/bookpack/containers/lettore/components/preferenze.md
  - groma/systems/bookpack/containers/lettore/components/sessione.md
  - groma/systems/bookpack/containers/lettore/components/regia-ascolto.md
  - groma/systems/bookpack/containers/lettore/components/sintesi-vocale.md
  - groma/systems/bookpack/containers/lettore/components/testo-da-ascoltare.md
parent_task_id: TASK-8
priority: medium
type: feature
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
È la parte che chi ascolta usa davvero: l'avvio dalla sessione, le card che scorrono al ritmo della voce, le domande con il tempo per pensare. Deve convivere con la navigazione esistente, cioè swipe, tap, frecce e posizione salvata, senza cambiarla per chi legge.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Un pulsante con le cuffie nell'intestazione avvia l'ascolto dalla card corrente; non compare senza sintesi vocale ed è disattivato, con spiegazione, senza voci nella lingua del libro
- [x] #2 La barra di controllo offre pausa e ripresa, card precedente e successiva, velocità e chiusura; la velocità resta salvata
- [x] #3 Le card avanzano da sole a fine lettura e la posizione si salva come negli spostamenti a mano; swipe, tap e frecce fanno ripartire la voce dalla card raggiunta
- [x] #4 Le domande mostrano un conto alla rovescia di 7 secondi saltabile, poi la risposta; non registrano esiti da sole e i pulsanti di risposta restano usabili
- [x] #5 Dopo l'ultima card viene letto il riassunto, poi l'ascolto si ferma sulla mindmap con un messaggio
- [x] #6 Uscire dalla sessione o cambiare fase ferma la voce; app in secondo piano o schermo bloccato mettono in pausa con stato visibile al ritorno
- [x] #7 I controlli hanno etichette per gli screen reader e l'ascolto non parte mai da solo
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Lint e test verdi: ruff e pytest in generator/, ESLint, nuxt typecheck e vitest in web/
- [x] #2 README e docs/ aggiornati, compreso docs/status.md
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. composables/useListening.ts: regia senza Nuxt, testabile con il sintetizzatore finto. Legge una card alla volta con useSpeech, avanza da sola, passa al riassunto e alla fine chiama onFinished; prev, next, pausa, ripresa, chiusura; riparte dalla card raggiunta a mano; espone la card la cui risposta va mostrata.
2. composables/useListenSettings.ts: velocità salvata, voce per lingua e mostra pulsante, nella tabella settings (ripristinati dal plugin all'avvio). Serve anche a TASK-8.3.
3. utils/speech.ts e listening.ts: disponibilità di una voce per la lingua, nome della lingua in italiano, velocità ammesse.
4. Componenti: SessionListenBar (pausa, prev, next, velocità, chiudi, stato, conto alla rovescia saltabile); CardDeck espone scrollTo e passa alle card l'indicatore di ascolto e la risposta da mostrare; ConceptCard e CheckCard mostrano l'icona delle cuffie, CheckCard rivela la risposta quando la voce la legge.
5. Pagina [chId].vue: pulsante nell'intestazione con spiegazione se manca la voce, cambi di fase della regia distinti da quelli dell'utente (che chiudono l'ascolto), pausa quando la pagina va in secondo piano, messaggio di fine sulla mindmap.
6. Test della regia; prova nel browser integrato con il sintetizzatore vero; lint, typecheck, test.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verifiche nel browser integrato a 375 px, sintetizzatore vero a volume zero: pulsante e barra; Avanti con posizione salvata (lastCardIndex); velocità 1,2× salvata in listenRate; pausa che ferma davvero la voce e ripresa; freccia destra che fa ripartire la voce dalla card raggiunta; domanda con 'Pensa alla risposta · 7', Mostra ora, risposta rivelata durante la lettura, nessun esito né ripasso registrati; passaggio da solo dall'ultima card al riassunto in 19 secondi; Avanti dal riassunto: mindmap e messaggio 'Fine dell'ascolto'; visibilitychange simulato: 'In pausa' al ritorno; Torna alle card dal riassunto e uscita dalla sessione fermano la voce. Casi limite simulati: solo voce inglese su libro italiano, pulsante attenuato con messaggio; senza speechSynthesis il pulsante non compare. Test: 11 per la regia (useListening) e 3 nuovi in speech.test; lettore 86 test, lint e typecheck verdi; generatore ruff e 161 test verdi.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Ascolto nella sessione di capitolo. Pulsante con le cuffie nell'intestazione, solo dove c'è la sintesi vocale, attenuato con spiegazione se manca una voce nella lingua del libro; parte solo da un tocco. Barra in basso con velocità salvata, card precedente e successiva, pausa e chiusura, stato e conto alla rovescia. composables/useListening.ts fa da regia senza Nuxt: card una dopo l'altra, riassunto, fine sulla mindmap con messaggio; riparte dalla card raggiunta con swipe, tap e frecce; rivela la risposta delle domande dopo 7 secondi, saltabili, senza registrare esiti. La pagina distingue i cambi di fase della regia da quelli dell'utente, che chiudono l'ascolto, e mette in pausa quando va in secondo piano. Preferenze in composables/useListenSettings.ts, ripristinate all'avvio, pronte per TASK-8.3. Limiti: il browser integrato non espone voci reali e lo schermo bloccato è solo simulato; le prove vere stanno in TASK-8.
<!-- SECTION:FINAL_SUMMARY:END -->
