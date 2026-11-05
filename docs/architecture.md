# Architettura

Due progetti indipendenti che comunicano solo attraverso un file.

```
 PDF ──► generator (CLI Python) ──► libro.bookpack.json ──► web (PWA Nuxt) ──► IndexedDB
              ▲                            │
         provider LLM              validato da schema/bookpack.schema.json
```

| Cartella | Ruolo |
|---|---|
| `generator/` | CLI Python. Contiene tutta l'AI. `models.py` è la fonte di verità del formato |
| `schema/bookpack.schema.json` | Schema JSON **generato** da `bookpack schema`. Non si modifica a mano |
| `web/` | Lettore statico e offline. Nessun backend, nessuna chiamata LLM |
| `samples/` | PDF di pubblico dominio, divisione in capitoli e pack ridotto usato dai test |
| `web/public/samples/` | Pack completo d'esempio, importabile dall'app |

## Come resta allineato il contratto

1. Si cambiano i modelli Pydantic in `generator/src/bookpack/models.py`.
2. `uv run bookpack schema` riscrive `schema/bookpack.schema.json`.
3. `pnpm gen:types` riscrive `web/app/types/bookpack.ts`.
4. Se il cambio è incompatibile si incrementa `SCHEMA_VERSION` e si aggiorna `SUPPORTED_SCHEMA_VERSION` in `web/app/utils/validatePack.ts`.

Un test del generatore fallisce se lo schema nel repo non corrisponde ai modelli. L'app rifiuta con un messaggio chiaro le versioni che non supporta.

## Doppia validazione

- **Generatore**: schema più i vincoli di `validate.py` (lunghezze, una sola citazione, ultima card `takeaway`, pagine dentro il capitolo, profondità delle mindmap).
- **Lettore**: solo lo schema, con Ajv, più il controllo degli id duplicati. I conteggi di card e flashcard stanno nello schema, quindi valgono anche qui; le lunghezze in parole no, perché sono qualità editoriale e non impediscono all'app di funzionare.
