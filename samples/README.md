# Campioni

Solo materiale di pubblico dominio.

| File | Cosa è |
|---|---|
| `how-to-live-on-24-hours-a-day.pdf` | *How to Live on 24 Hours a Day* di Arnold Bennett (1908), impaginato da [Project Gutenberg #2274](https://www.gutenberg.org/ebooks/2274) senza outline, con header e numeri di pagina |
| `how-to-live-on-24-hours-a-day.toc.yaml` | Divisione in capitoli: esclude la prefazione, che dice di sé di andare letta alla fine |
| `how-to-live-on-24-hours-a-day.en.toc.yaml` | La stessa divisione per la versione inglese, con id `how-to-live-on-24-hours-a-day-en` e titolo "(English)", così le due versioni stanno insieme in libreria |
| `sample.bookpack.json` | Pack ridotto a 2 capitoli, usato dai test di entrambi i progetti |
| `make_sample_pdf.py` | Rigenera il PDF dal testo di Gutenberg |

I pack completi da 12 capitoli sono in `web/public/samples/`, generati dalla pipeline con `~deepseek/deepseek-flash-latest`: in italiano per $0,05, in inglese per $0,03. L'app li propone entrambi, anche per provare le voci dell'ascolto in due lingue. Quello ridotto contiene i primi due capitoli della versione italiana. Per rigenerarli, da `generator/`:

```bash
uv run bookpack build ../samples/how-to-live-on-24-hours-a-day.pdf --toc ../samples/how-to-live-on-24-hours-a-day.toc.yaml --lang it -o ../web/public/samples/how-to-live-on-24-hours-a-day.bookpack.json
```

```bash
uv run bookpack build ../samples/how-to-live-on-24-hours-a-day.pdf --toc ../samples/how-to-live-on-24-hours-a-day.en.toc.yaml --lang en -o ../web/public/samples/how-to-live-on-24-hours-a-day.en.bookpack.json
```

L'elenco dei libri d'esempio mostrati dall'app è in `web/app/utils/samples.ts`.
