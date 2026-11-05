# Web

Lettore statico: Nuxt 4 con `ssr: false`, Nuxt UI 4, Tailwind 4, Dexie, markmap, Ajv, @vite-pwa/nuxt. Tutti i comandi si lanciano da `web/`.

```bash
pnpm install
pnpm dev          # http://localhost:3000
pnpm generate     # build statica in .output/public
pnpm dlx serve .output/public -s -l 4173
```

Controlli: `pnpm lint`, `pnpm typecheck`, `pnpm test`. Dopo un cambio di schema: `pnpm gen:types`.

## Pagine

| Route | Contenuto |
|---|---|
| `/` | Libreria, "Riprendi", stato vuoto con il libro d'esempio |
| `/import` | Da file o da URL (`?url=` lo precompila), con validazione e anteprima |
| `/book/[bookId]` | Percorso: panoramica, idee, tappe con stato, glossario |
| `/book/[bookId]/ch/[chId]` | Sessione: card, mindmap, flashcard, completamento |
| `/book/[bookId]/map` | Mindmap del libro; toccando un titolo si apre il capitolo |
| `/settings` | Tema, dimensione del testo, export e import, eliminazione, azzeramento |

## Sessione

- **Card**: swipe, tap sul terzo sinistro o destro dello schermo, frecce da tastiera. Il tap al centro non fa nulla, così si può selezionare il testo.
- **Mindmap**: cerchi per aprire e chiudere i rami, pinch-zoom e pan.
- **Flashcard**: tap o spazio per girarle; dopo la risposta, "Lo sapevo" o "Da ripassare" (frecce destra e sinistra).
- Riaprendo un capitolo completato si entra in **rilettura**: la posizione salvata e il completamento non cambiano, gli esiti delle flashcard si aggiornano.

## Dati locali

Database IndexedDB `bookpack`, definito in `app/db/index.ts`:

```ts
books:    { id, pack, importedAt, updatedAt }
progress: { bookId, currentChapterId, lastOpenedAt, chapters: Record<chapterId, ChapterProgress> }
settings: { key, value }   // fontScale, theme
```

La logica pura sta in `app/utils/progress.ts` ed è coperta da test. Se un pack aggiornato perde capitoli, card o flashcard, il progresso relativo viene ignorato senza errori.

**Export e import**: un JSON con `progress` e `settings`; i libri si reimportano dai pack. Fondendo vince il punto più avanzato di ogni capitolo, l'esito di flashcard più recente e il completamento di una qualsiasi delle due parti. Sostituendo si cancella il progresso attuale.

I dati restano solo nel browser: svuotando i dati del sito si perdono. Per conservarli conviene l'export.

## PWA e offline

Il service worker precarica JS, CSS, `index.html`, font latini, icone e il pack d'esempio. Tutte le route ripiegano su `index.html`. Font e icone sono nel bundle, quindi l'app non chiede nulla a server esterni. L'aggiornamento è automatico.

## Deploy su GitHub Pages

Il workflow `.github/workflows/deploy.yml` lancia test e build a ogni push su `main` o `master`, con `NUXT_APP_BASE_URL=/<nome-repo>/`. Sul repository va attivato *Settings → Pages → Source: GitHub Actions*.

Per riprodurre la build in locale:

```bash
NUXT_APP_BASE_URL=/nome-repo/ pnpm generate
```

Da Git Bash su Windows serve anche `MSYS_NO_PATHCONV=1`, altrimenti il percorso viene riscritto in `C:/Program Files/Git/nome-repo/`.
