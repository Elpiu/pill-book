---
id: DRAFT-1
title: Sincronizzare i dati tra dispositivi tramite Google Drive
status: Draft
assignee: []
created_date: '2026-11-13T21:35:00Z'
labels:
  - lettore
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Proposta discussa e non ancora decisa: sincronizzare progressi, ripassi, impostazioni e libri tra i dispositivi collegati allo stesso account Google, senza backend, usando la cartella appDataFolder di Drive con lo scope drive.appdata. Serve un ID client OAuth creato dall'utente su Google Cloud. Limiti noti: il token dura circa un'ora e il rinnovo richiede un tocco dell'utente; cancellazioni e azzeramenti richiedono marcatori con data, altrimenti la fusione li annulla. Idea: un modulo riusabile senza dipendenze in web/app/lib/drive-sync/.
<!-- SECTION:DESCRIPTION:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Lint e test verdi: ruff e pytest in generator/, ESLint, nuxt typecheck e vitest in web/
- [ ] #2 README e docs/ aggiornati, compreso docs/status.md
<!-- DOD:END -->
