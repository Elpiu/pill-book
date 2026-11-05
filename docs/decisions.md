# Decisioni

Scelte non coperte dal piano, o che lo adattano.

## Formato e generatore

| Scelta | Motivo |
|---|---|
| I conteggi di card e flashcard stanno nello schema, non solo in `validate.py` | Così valgono anche nel lettore senza duplicare logica |
| `page` è il numero fisico nel PDF | È sempre disponibile. Il numero stampato può mancare o non essere affidabile |
| Limiti "circa" con doppia soglia, avviso ed errore | Il piano li indica come approssimativi: un errore a 61 parole costerebbe un retry inutile |
| Token stimati con caratteri/4 invece di tiktoken | Il piano ammette l'euristica. Una dipendenza in meno, e serve solo una stima |
| Sezioni sotto le 150 parole saltate, mantenendo la numerazione | Non reggono 5 card senza inventare (es. le pagine di apertura di una parte) |
| Provider `fake` dentro il pacchetto | Permette di provare la pipeline su un PDF vero senza chiave. Il piano lo chiedeva per i test |
| Lingua riconosciuta dalle parole frequenti | `--lang` resta l'override; basta una stima per il default |
| File YAML con `book: {id, title, author, lang}` | Molti PDF hanno metadati vuoti, come il libro di prova |
| Prompt in inglese, output nella lingua richiesta | Le istruzioni restano le stesse per ogni lingua di output |
| **OpenRouter come unico provider**, in deroga al piano (che prevedeva Anthropic e OpenAI-compatible) | Decisione del progetto: una sola chiave e qualsiasi modello, senza legarsi a un fornitore |
| Client OpenRouter costruito sull'SDK `openai` | OpenRouter espone un'API compatibile: SDK, retry e tipi sono già pronti |
| Default `anthropic/claude-sonnet-5.5` | Compromesso tra qualità e prezzo. Si cambia con `BOOKPACK_MODEL` o `--model` |
| Prezzi e limiti letti dal catalogo di OpenRouter, in cache per 24 ore | Una tabella nel codice non potrebbe coprire centinaia di modelli. Senza rete il costo è `n/d`, il resto funziona |
| Output strutturato con `require_parameters`; se nessun provider lo supporta, schema nel prompt | Funziona con qualsiasi modello. In ogni caso la validazione locale e i ritentativi garantiscono il risultato |
| Schema inviato senza `$ref` | Non tutti i modelli li gestiscono |
| Budget per capitolo limitato al 60% del contesto del modello | I modelli piccoli passano da soli al map-reduce |
| Ragionamento `low` sui modelli che lo dichiarano nel catalogo | Il testo di un capitolo sta in circa 2.000 token, ma con il livello `high` un modello ne ha spesi fino a 7.000 e in un caso ha esaurito il limite di 16.000. Il ragionamento si paga come output. Dove `low` non c'è resta il default: `none` spegnerebbe tutto e il suo effetto sulla qualità non è stato misurato |
| Limite di 32.000 token di output per chiamata, e un nuovo tentativo a 64.000 se la risposta viene troncata | Il ragionamento conta nello stesso limite. Entrambi i valori si riducono se il modello ha un limite più basso. Il tentativo troncato si paga e viene sommato al costo effettivo |
| Livello di ragionamento e limiti fuori dalla chiave della cache | Cambiarli non deve far ripagare le risposte già valide. Per rigenerare con le nuove impostazioni c'è `--no-cache` |
| Provider `fake` esposto come `--fake` | Resta per test e prove gratuite: è l'unica alternativa a OpenRouter |
| Finestra in Tkinter, nel pacchetto del generatore | Nessuna dipendenza in più. Usa la stessa pipeline della CLI |
| Anteprima PDF disegnata da PyMuPDF in un `Canvas`, restando in Tkinter | Una pagina si disegna in circa 12 ms anche su un libro di 417 pagine. Un'interfaccia web con pdf.js aggiungerebbe un server e un secondo frontend. Da rivedere se serviranno evidenziare il testo o trascinare i confini sulla pagina |
| Casella tolta: il capitolo resta numerato. Sezione esclusa spuntata: diventa capitolo e rinumera | Come `--chapters`, scegliere cosa generare non deve cambiare gli id, altrimenti rigenerando si perderebbe il progresso. Includere una sezione è invece un cambio della divisione |
| Il capitolo vicino segue un confine spostato, se era contiguo o se si sovrapporrebbe | È quasi sempre ciò che si vuole quando si corregge un confine, e un vuoto voluto tra due capitoli resta. Due capitoli sovrapposti nati da un file o da uno spostamento estremo vengono segnalati nella colonna Note |
| Spunte non salvate nel file dei capitoli | Il file descrive la divisione del libro, le spunte sono una scelta del momento |
| Il documento dell'anteprima si chiude prima di leggere un altro PDF | PyMuPDF non regge più thread: durante la lettura in background non ci sono altre chiamate attive |
| Chiave salvata in chiaro nel `.env`, solo su richiesta | Il `.env` è già il posto previsto ed è in gitignore |
| Interrompere ferma la generazione tra un capitolo e l'altro | La chiamata in corso non si può annullare senza perderla; tutto ciò che è pronto resta in cache |
| Chiamate in sequenza | Più semplice, e la cache rende la ripresa sicura. Da rivedere solo se i tempi sui libri lunghi pesano |

## Lettore

| Scelta | Motivo |
|---|---|
| Rilettura che non sposta il progresso | Riaprire un capitolo finito non deve farlo tornare "in corso" |
| Slide vuota in coda al deck | Rende uguali swipe e tap per passare alla mindmap |
| Mappa del libro aperta solo sui capitoli | Con tutti i rami aperti il testo su telefono diventa illeggibile |
| Mindmap caricate solo quando servono | Le librerie sono pesanti e non servono nelle card |
| Solo gli alfabeti latini nella cache offline | Riduce il precaricamento. Altri alfabeti usano i font di sistema se offline |
| Primario `teal-700` in tema chiaro | Il default dava poco contrasto con il testo bianco |
| Solo `index.html` nel precaricamento delle pagine | Precaricare `/404` o `/import` fa fallire l'installazione sugli host che non li servono |

## Repo

| Scelta | Motivo |
|---|---|
| `books/` in gitignore | Il piano ammette nel repo solo materiale di pubblico dominio, e il copyright di `AgenticSE_Book.pdf` non è verificato |
| PDF d'esempio impaginato da noi | Project Gutenberg offre di rado PDF. Lo script è in `samples/make_sample_pdf.py` |
