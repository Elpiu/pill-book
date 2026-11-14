---
type: C4 Container
title: Lettore
status: draft
groma:
  id: lettore
  parent: bookpack
  technology: Nuxt 4, Vue 3, Nuxt UI, Dexie, PWA statica
description: Fa leggere i pack a card, mindmap e flashcard, anche offline, senza backend.
---

Sito statico generato con Nuxt e pubblicato su GitHub Pages; si installa come PWA. Importa i pack da file o da URL, li valida e li salva in IndexedDB insieme a progresso, ripassi e impostazioni. Un service worker precarica l'app, quindi dopo la prima visita funziona senza rete. Nessun dato lascia il browser, salvo l'export del progresso fatto dall'utente.
