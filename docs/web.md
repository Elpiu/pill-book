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
| `/book/[bookId]/ch/[chId]` | Sessione: card con domande, riassunto, mindmap, flashcard, completamento |
| `/review` | Ripasso di oggi: le domande dovute di tutti i libri |
| `/book/[bookId]/map` | Mindmap del libro; toccando un titolo si apre il capitolo |
| `/settings` | Tema, dimensione del testo, export e import, eliminazione, azzeramento |

## Sessione

- **Card**: swipe, tap sul terzo sinistro o destro dello schermo, frecce da tastiera. Il tap al centro non fa nulla, così si può selezionare il testo. L'idea e la sua spiegazione sono visibili insieme; se non stanno nello schermo, la card scorre.
- **Parti**: i capitoli lunghi sono divisi in parti, con una card di apertura che è anche un buon punto per fermarsi. In alto si legge "Card 12 di 34 · Parte 2 di 5", e riaprendo si riprende dalla card esatta.
- **Domande durante la lettura**: una ogni 3-4 card. Si prova a rispondere, si guarda la risposta e si indica se la si sapeva. Si possono saltare con uno swipe.
- **Riassunto**: dopo le card, il capitolo ripetuto con parole diverse.
- **Mindmap**: cerchi per aprire e chiudere i rami, pinch-zoom e pan.
- **Flashcard**: tap o spazio per girarle; dopo la risposta, "Lo sapevo" o "Da ripassare" (frecce destra e sinistra).
- Riaprendo un capitolo completato si entra in **rilettura**: la posizione salvata e il completamento non cambiano, gli esiti delle flashcard si aggiornano.

## Ripasso

Ogni risposta, data a una flashcard o a una domanda durante la lettura, fissa quando la domanda dovrà tornare. Si usano le scatole di Leitner (`app/utils/review.ts`): se la sapevi, sale di scatola e torna dopo 3, 7, 16 e poi 35 giorni; se non la sapevi, riparte dalla prima e torna domani. Si ragiona a giorni, quindi una domanda dovuta domani è pronta dal mattino.

In home compare **Ripasso di oggi** quando c'è qualcosa da fare. L'elenco si fissa all'apertura: una domanda sbagliata torna domani, non durante lo stesso giro.

## Dati locali

Database IndexedDB `bookpack`, definito in `app/db/index.ts`:

```ts
books:    { id, pack, importedAt, updatedAt }
progress: { bookId, currentChapterId, lastOpenedAt, chapters: Record<chapterId, ChapterProgress> }
settings: { key, value }   // fontScale, theme
reviews:  { key, bookId, itemId, box, dueAt, lastAt, lapses }
```

La logica pura sta in `app/utils/progress.ts` ed è coperta da test. Se un pack aggiornato perde capitoli, card o flashcard, il progresso relativo viene ignorato senza errori.

**Export e import**: un JSON con `progress`, `settings` e `reviews`; i libri si reimportano dai pack. Fondendo vince il punto più avanzato di ogni capitolo, l'esito più recente di flashcard e ripassi e il completamento di una qualsiasi delle due parti. Sostituendo si cancella il progresso attuale. Gli export precedenti, senza ripassi, si importano ancora.

I dati restano solo nel browser: svuotando i dati del sito si perdono. Per conservarli conviene l'export.

## PWA e offline

Il service worker precarica JS, CSS, `index.html`, font latini, icone e il pack d'esempio. Tutte le route ripiegano su `index.html`. Font e icone sono nel bundle, quindi l'app non chiede nulla a server esterni. L'aggiornamento è automatico: alla pubblicazione di una nuova versione la pagina si ricarica da sola, e la lettura riprende dalla card esatta.

**Installazione**: su Android e su Chrome da computer la home propone **Installa**, se il browser lo consente. Su iPhone si passa da Safari: Condividi, poi Aggiungi alla schermata Home. Le istruzioni sono anche nelle impostazioni. L'installazione richiede HTTPS, che GitHub Pages fornisce.

**Dati**: al primo libro importato l'app chiede al browser di non cancellare i dati locali per mancanza di spazio. Il browser può comunque rifiutare, e i dati restano solo su quel dispositivo: per sicurezza c'è l'export del progresso.

## Deploy su GitHub Pages

A ogni push su `main` o `master`, il workflow `.github/workflows/deploy.yml` esegue test e lint di entrambi i progetti, compila l'app e la pubblica. Se un test fallisce, non pubblica nulla. Si può anche lanciare a mano dalla scheda Actions.

Per la prima pubblicazione:

1. Crea il repository su GitHub, pubblico, e fai il push:

```bash
git remote add origin https://github.com/UTENTE/NOME-REPO.git
```

```bash
git push -u origin master
```

2. Su GitHub: **Settings → Pages → Source: GitHub Actions**. Va fatto una volta sola.
3. Se il primo workflow è partito prima di questo passaggio ed è fallito, rilancialo: **Actions → Deploy web → Run workflow**.

L'app sarà su `https://UTENTE.github.io/NOME-REPO/`. La base URL viene ricavata dal nome del repository; per un repository `UTENTE.github.io` è `/`.

**Cosa non finisce nella repo**: `books/`, `generator/out/`, `.bookpack-cache/` e `.env` sono in gitignore. I pack dei libri personali non si pubblicano: si importano nell'app come file, e restano sul dispositivo.

Per riprodurre la build in locale:

```bash
NUXT_APP_BASE_URL=/nome-repo/ pnpm generate
```

Da Git Bash su Windows serve anche `MSYS_NO_PATHCONV=1`, altrimenti il percorso viene riscritto in `C:/Program Files/Git/nome-repo/`.

## Passare un libro al telefono

1. Genera il pack: finisce in `generator/out/<id>.bookpack.json`.
2. Mandalo al telefono nel modo che preferisci: cavo, cloud, chat con te stesso.
3. Apri l'app, **Importa → Da file** e scegli il file.

Il pack resta salvato nel browser e da quel momento funziona offline.
