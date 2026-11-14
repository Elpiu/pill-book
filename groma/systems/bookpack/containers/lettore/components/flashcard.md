---
type: C4 Component
title: Flashcard
status: stable
groma:
  id: flashcard
  parent: lettore
  code:
    - scanner: vue
      file: web/app/components/session/FlashcardDeck.vue
  group: Sessione di lettura
description: Domande da girare, con Lo sapevo e Da ripassare.
---

Usate a fine capitolo e nel ripasso; ogni risposta fissa quando la domanda tornerà.

## Derived relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/components/session/FlashcardDeck.vue](../../../../../../web/app/components/session/FlashcardDeck.vue) | [web/app/pages/review.vue](../../../../../../web/app/pages/review.vue) | Invokes supplied callback: answer | vue |
