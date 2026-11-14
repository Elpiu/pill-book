---
id: TASK-9
title: Tradurre i titoli di libro e capitoli nella lingua del pack
status: Done
assignee:
  - '@claude'
created_date: '2026-11-14T21:12:00Z'
updated_date: '2026-11-14T21:20:00Z'
labels:
  - generatore
dependencies: []
modified_files:
  - generator/src/bookpack/condense/prompts/chapter_wrap.md
  - generator/src/bookpack/condense/chapter.py
  - generator/src/bookpack/condense/prompts/book.md
  - generator/src/bookpack/condense/book.py
  - generator/src/bookpack/condense/pipeline.py
  - generator/src/bookpack/llm/fake.py
  - generator/tests/test_pipeline.py
  - docs/generator.md
  - docs/decisions.md
  - docs/status.md
  - web/public/samples/how-to-live-on-24-hours-a-day.bookpack.json
  - web/public/samples/how-to-live-on-24-hours-a-day.en.bookpack.json
priority: medium
type: bug
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Il generatore scrive card, riassunti e panoramica nella lingua del pack, ma prende titolo del libro e titoli dei capitoli dall'indice del PDF senza tradurli. Il libro d'esempio italiano mostra quindi 'How to Live on Twenty-Four Hours a Day' e 'The Daily Miracle' in libreria, nel percorso, nella sessione e nella mappa del libro; lo stesso vale per ogni libro generato in una lingua diversa da quella del PDF.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Titoli dei capitoli e titolo del libro escono nella lingua del pack; un titolo già in quella lingua resta invariato
- [x] #2 Id di libro e capitoli non cambiano, così il progresso dei libri già importati resta valido
- [x] #3 La mindmap del libro usa i titoli tradotti dei capitoli, come richiede il controllo esistente
- [x] #4 Un titolo vuoto o troppo lungo restituito dal modello non finisce nel pack
- [x] #5 I libri d'esempio sono rigenerati: quello italiano ha i titoli in italiano, quello inglese li mantiene
- [x] #6 Test per titoli tradotti, titolo di ripiego e titolo del libro
<!-- AC:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Lint e test verdi: ruff e pytest in generator/, ESLint, nuxt typecheck e vitest in web/
- [x] #2 README e docs/ aggiornati, compreso docs/status.md
<!-- DOD:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. chapter_wrap.md e ChapterWrap: campo title, il titolo del capitolo nella lingua del pack o invariato se già in quella lingua; _to_chapter lo usa, rifiuta titoli troppo lunghi con un ritentativo e ripiega sul titolo originale se vuoto.
2. book.md e BookDraft: campo title per il titolo del libro; condense_book lo restituisce e build_pack lo mette in book.title. Id invariati.
3. Provider finto: restituisce i titoli ricevuti, così i test esistenti restano validi.
4. Test: titolo tradotto usato, ripiego sul titolo vuoto, titolo troppo lungo rifiutato, titolo del libro, id stabili.
5. Rigenerare i due libri d'esempio (le parti restano in cache) e controllarli; docs e mappa.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Prima prova reale con il titolo chiesto per primo: 10 capitoli su 12 tradotti, 2 capitoli e il titolo del libro rimasti in inglese. Spostato il campo title in fondo a ChapterWrap e dopo keyIdeas in BookDraft, con l'istruzione 'nella stessa lingua del riassunto': rigenerati i due esempi, italiano interamente tradotto, inglese invariato, id invariati, pack validi. Costo totale delle rigenerazioni /usr/bin/bash,06 con le parti in cache. Generatore: ruff, formato e 164 test verdi; lettore: 87 test verdi sui pack rigenerati.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Titoli di libro e capitoli nella lingua del pack. La chiusura del capitolo e la panoramica restituiscono anche il titolo, tradotto se il PDF è in un'altra lingua e invariato altrimenti; vuoto si tiene l'originale, oltre 20 parole si ritenta. Gli id restano quelli dei titoli originali, quindi il progresso dei libri già importati regge. I due libri d'esempio sono rigenerati: l'italiano ha ora titolo e capitoli in italiano.
<!-- SECTION:FINAL_SUMMARY:END -->
