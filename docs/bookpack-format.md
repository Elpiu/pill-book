# Formato book pack (v1)

Lo schema completo è in [../schema/bookpack.schema.json](../schema/bookpack.schema.json). Un esempio breve è in [../samples/sample.bookpack.json](../samples/sample.bookpack.json).

```jsonc
{
  "schemaVersion": 1,
  "generator": { "version": "0.1.0", "model": "anthropic/claude-sonnet-5.5", "generatedAt": "ISO-8601" },
  "book": {
    "id": "slug-stabile",
    "title": "…",
    "author": "…",            // opzionale
    "lang": "it",
    "sourcePages": 312,
    "coverColor": "#1f6feb"   // opzionale
  },
  "overview": {
    "summary": "5-8 frasi",
    "keyIdeas": ["…"],        // da 3 a 7
    "mindmap": "# Titolo\n## Titolo del capitolo\n- …"
  },
  "chapters": [{
    "id": "ch-01",
    "index": 1,
    "title": "…",
    "pageStart": 12,
    "pageEnd": 34,
    "estMinutes": 5,
    "tldr": "una frase",
    "cards": [{ "id": "ch-01-c01", "type": "concept", "title": "…", "body": "…", "page": 14 }],
    "mindmap": "# Capitolo\n## Ramo\n- Foglia",
    "flashcards": [{ "id": "ch-01-f01", "q": "…", "a": "…", "page": 14 }]
  }],
  "glossary": [{ "term": "…", "definition": "…", "chapterId": "ch-03" }]   // opzionale
}
```

## Vincoli

| Regola | Limite | Dove |
|---|---|---|
| Card per capitolo | 5-12 | schema |
| Flashcard per capitolo | 3-5 | schema |
| Idee portanti | 3-7 | schema |
| Ultima card | `takeaway` | generatore |
| `body` | avviso oltre 60 parole, errore oltre 75 | generatore |
| `title` | avviso oltre 8 parole, errore oltre 12 | generatore |
| `quote` | massimo 25 parole, massimo una per capitolo | generatore |
| `page` | obbligatoria tranne che per `takeaway`, dentro `pageStart`-`pageEnd` | generatore |
| Mindmap | profondità massima 4; avviso oltre 25 nodi, errore oltre 45 | generatore |
| Mindmap del libro | un `##` per capitolo con il titolo esatto | generatore |
| Id univoci | tutti | generatore e lettore |

Il piano indica alcuni limiti come "circa": per questo c'è una soglia di avviso e una di errore.

## Id e numeri di pagina

- `chapter.id` nasce dalla posizione nell'elenco completo dei capitoli (`ch-01`, `ch-02`, …). Con `--chapters 2-3` gli id restano `ch-02` e `ch-03`. Cambiare l'ordine in un file `--toc`, o escludere una sezione che prima era inclusa, cambia gli id.
- Una sezione troppo breve (meno di 150 parole) viene saltata ma conserva il suo numero, quindi `index` può avere buchi.
- `page` è il numero fisico nel PDF, a partire da 1, non il numero stampato sulla pagina.
- La mindmap del libro usa il titolo del capitolo come chiave: toccandolo nell'app si apre quel capitolo.
