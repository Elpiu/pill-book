---
type: C4 Component
title: Mazzo di card
status: stable
groma:
  id: mazzo-card
  parent: lettore
  code:
    - scanner: vue
      file: web/app/components/session/CardDeck.vue
    - scanner: vue
      file: web/app/components/session/ConceptCard.vue
    - scanner: vue
      file: web/app/components/session/CheckCard.vue
  group: Sessione di lettura
description: Mostra le card con swipe, tap e tastiera, comprese le domande durante la lettura.
---

Il tap al centro non fa nulla, così si può selezionare il testo. Le card troppo lunghe scorrono.

## Derived relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [web/app/components/session/CardDeck.vue](../../../../../../web/app/components/session/CardDeck.vue) | [web/app/pages/book/[bookId]/ch/[chId].vue](../../../../../../web/app/pages/book/%5BbookId%5D/ch/%5BchId%5D.vue) | Invokes supplied callback: change | vue |
