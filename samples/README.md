# Campioni

Solo materiale di pubblico dominio.

| File | Cosa è |
|---|---|
| `how-to-live-on-24-hours-a-day.pdf` | *How to Live on 24 Hours a Day* di Arnold Bennett (1908), impaginato da [Project Gutenberg #2274](https://www.gutenberg.org/ebooks/2274) senza outline, con header e numeri di pagina |
| `how-to-live-on-24-hours-a-day.toc.yaml` | Divisione in capitoli: esclude la prefazione, che dice di sé di andare letta alla fine |
| `sample.bookpack.json` | Pack ridotto a 2 capitoli, usato dai test di entrambi i progetti |
| `make_sample_pdf.py` | Rigenera il PDF dal testo di Gutenberg |

Il pack completo da 12 capitoli è in `web/public/samples/`. Sia questo sia quello ridotto sono stati **scritti a mano in una sessione di Claude Code, senza chiamate API**: lo dichiara il campo `generator.model`. Per un pack generato davvero dalla pipeline:

```bash
cd generator
uv run bookpack build ../samples/how-to-live-on-24-hours-a-day.pdf --toc ../samples/how-to-live-on-24-hours-a-day.toc.yaml --lang it
```
