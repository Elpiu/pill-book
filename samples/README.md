# Campioni

Solo materiale di pubblico dominio.

| File | Cosa è |
|---|---|
| `how-to-live-on-24-hours-a-day.pdf` | *How to Live on 24 Hours a Day* di Arnold Bennett (1908), impaginato da [Project Gutenberg #2274](https://www.gutenberg.org/ebooks/2274) senza outline, con header e numeri di pagina |
| `how-to-live-on-24-hours-a-day.toc.yaml` | Divisione in capitoli: esclude la prefazione, che dice di sé di andare letta alla fine |
| `sample.bookpack.json` | Pack ridotto a 2 capitoli, usato dai test di entrambi i progetti |
| `make_sample_pdf.py` | Rigenera il PDF dal testo di Gutenberg |

Il pack completo da 12 capitoli è in `web/public/samples/`, generato dalla pipeline con `~deepseek/deepseek-flash-latest` per $0,05. Quello ridotto ne contiene i primi due capitoli. Per rigenerarlo:

```bash
cd generator
uv run bookpack build ../samples/how-to-live-on-24-hours-a-day.pdf --toc ../samples/how-to-live-on-24-hours-a-day.toc.yaml --lang it -o ../web/public/samples/how-to-live-on-24-hours-a-day.bookpack.json
```
