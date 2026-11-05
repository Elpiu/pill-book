# Formato book pack (v2)

Lo schema completo è in [../schema/bookpack.schema.json](../schema/bookpack.schema.json). Un esempio breve è in [../samples/sample.bookpack.json](../samples/sample.bookpack.json).

```jsonc
{
  "schemaVersion": 2,
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
    "estMinutes": 12,
    "tldr": "una frase",
    "summary": "Riassunto di fine capitolo.\n\nA paragrafi separati da una riga vuota.",
    "cards": [
      { "id": "ch-01-c01", "type": "section", "title": "Prima parte", "body": "Cosa si impara qui.", "page": 12 },
      { "id": "ch-01-c02", "type": "concept", "title": "…", "body": "L'idea.", "details": "Perché, come, esempio.", "page": 14 },
      { "id": "ch-01-c03", "type": "procedure", "title": "…", "body": "Lo scopo.", "steps": ["…", "…"], "code": "ls -la", "page": 15 },
      { "id": "ch-01-c04", "type": "check", "body": "Perché…?", "answer": "Perché…", "page": 15 },
      { "id": "ch-01-c05", "type": "takeaway", "body": "Cosa portare via." }
    ],
    "mindmap": "# Capitolo\n## Ramo\n- Foglia",
    "flashcards": [{ "id": "ch-01-f01", "q": "…", "a": "…", "page": 14 }]
  }],
  "glossary": [{ "term": "…", "definition": "…", "chapterId": "ch-03" }]   // opzionale
}
```

## Tipi di card

| Tipo | Cosa contiene | Campi specifici |
|---|---|---|
| `concept`, `definition` | Un'idea o un termine, con il perché e il come | `title`, `details` |
| `example` | Un caso concreto del libro | `title`, `details` |
| `procedure` | Come si fa qualcosa: pensata per i manuali tecnici | `steps`, e `code` con comandi letterali |
| `quote` | Una frase del libro, nella lingua originale | |
| `check` | Domanda durante la lettura: `body` è la domanda | `answer` |
| `section` | Apre una parte di un capitolo lungo: un punto dove fermarsi | `title` |
| `takeaway` | Cosa portare via. È sempre l'ultima | |

La forma non dipende da una classificazione del libro: il modello sceglie i tipi in base a ciò che ogni parte contiene.

## Vincoli

| Regola | Limite | Dove |
|---|---|---|
| Card per capitolo | da 3 a 200, circa una ogni 500 parole del libro | schema e generatore |
| Flashcard per capitolo | da 3 a 20, circa una ogni 4 card | schema e generatore |
| Idee portanti | 3-7 | schema |
| Ultima card | `takeaway` | generatore |
| `body` | avviso oltre 60 parole, errore oltre 80 | generatore |
| `details` | avviso oltre 130 parole, errore oltre 180 | generatore |
| `title` | avviso oltre 8 parole, errore oltre 12 | generatore |
| `quote` | massimo 25 parole; massimo una ogni 4 card | generatore |
| `check` | deve avere `answer`, massimo 90 parole | generatore |
| `procedure` | da 2 a 12 passi, ognuno di massimo 40 parole | generatore |
| `code` | massimo 30 righe | generatore |
| `summary` | da 40 a 900 parole, circa un sesto delle parole delle card | generatore |
| `page` | obbligatoria tranne che per `takeaway` e `section`, dentro `pageStart`-`pageEnd` | generatore |
| Mindmap | profondità massima 4; avviso oltre 40 nodi, errore oltre 90 | generatore |
| Mindmap del libro | un `##` per capitolo con il titolo esatto | generatore |
| Id univoci | tutti | generatore e lettore |

Una citazione non presente nel testo del libro viene scartata e segnalata.

## Id e numeri di pagina

- `chapter.id` nasce dalla posizione nell'elenco completo dei capitoli (`ch-01`, `ch-02`, …). Con `--chapters 2-3` gli id restano `ch-02` e `ch-03`. Cambiare l'ordine in un file `--toc`, o escludere una sezione che prima era inclusa, cambia gli id.
- Una sezione troppo breve (meno di 150 parole) viene saltata ma conserva il suo numero, quindi `index` può avere buchi.
- `page` è il numero fisico nel PDF, a partire da 1, non il numero stampato sulla pagina.
- La mindmap del libro usa il titolo del capitolo come chiave: toccandolo nell'app si apre quel capitolo.

## Versioni

L'app importa solo pack v2. Un pack v1 viene rifiutato con l'invito a rigenerarlo, ma i pack v1 già importati restano leggibili: non hanno riassunti né domande durante la lettura.
