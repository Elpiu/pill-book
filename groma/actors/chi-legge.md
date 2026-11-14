---
type: C4 Actor
title: Chi legge
status: stable
groma:
  id: chi-legge
---

Legge i pack sul telefono a sessioni brevi, risponde alle domande e ripassa nei giorni seguenti.

## Relationships

| Source | Target | Description | Technology |
| --- | --- | --- | --- |
| [chi-legge](chi-legge.md) | [web/app/pages/index.vue](../../web/app/pages/index.vue) | Sceglie un libro | browser o PWA |
| [chi-legge](chi-legge.md) | [web/app/pages/import.vue](../../web/app/pages/import.vue) | Importa un pack | file o URL |
| [chi-legge](chi-legge.md) | [web/app/pages/book/[bookId]/ch/[chId].vue](../../web/app/pages/book/%5BbookId%5D/ch/%5BchId%5D.vue) | Legge un capitolo | browser o PWA |
| [chi-legge](chi-legge.md) | [web/app/pages/review.vue](../../web/app/pages/review.vue) | Ripassa le domande | browser o PWA |
| [chi-legge](chi-legge.md) | [web/app/pages/settings.vue](../../web/app/pages/settings.vue) | Esporta il progresso | browser o PWA |
