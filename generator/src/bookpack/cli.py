"""CLI di bookpack."""

import json
import re
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from .cache import ResponseCache
from .condense.chunking import word_count
from .condense.detect import detect_with_llm
from .condense.estimate import estimate_build, estimate_section
from .condense.pipeline import (
    PackError,
    build_pack,
    is_too_short,
    numbered_chapters,
    target_sections,
    write_pack,
)
from .config import ConfigError, Settings, load_settings
from .extract.clean import clean_pages
from .extract.pdf import PdfDocument, PdfError, open_pdf
from .extract.toc import Detection, TocError, book_title, detect_chapters, write_toc_file
from .llm import get_provider
from .llm.base import LLMError
from .llm.catalog import (
    ModelInfo,
    context_budget,
    find_model,
    load_catalog,
    search_models,
    suggest_models,
)
from .llm.structured import StructuredLLM
from .models import export_schema
from .validate import validate_data

app = typer.Typer(help="Trasforma un PDF in un book pack.", no_args_is_help=True)
console = Console()
DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schema" / "bookpack.schema.json"
_RANGE = re.compile(r"^(\d+)(?:-(\d+))?$")


@app.callback()
def main() -> None:
    """Bookpack: libri condensati in pillole."""
    # Su Windows la console può non essere UTF-8: titoli e avvisi non devono far fallire il comando
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _fail(message: str) -> typer.Exit:
    console.print(f"[red]Errore:[/red] {message}", highlight=False)
    return typer.Exit(1)


def _load(pdf: Path, toc: Path | None, include_all: bool) -> tuple[PdfDocument, Detection]:
    try:
        doc = open_pdf(pdf)
        return doc, detect_chapters(doc, toc, include_all)
    except (PdfError, TocError) as exc:
        raise _fail(str(exc)) from exc


def _settings(model: str | None = None, fake: bool = False) -> Settings:
    try:
        return load_settings(model, fake)
    except ConfigError as exc:
        raise _fail(str(exc)) from exc


def _model_info(settings: Settings) -> ModelInfo | None:
    """Dati del modello dal catalogo. Senza catalogo si prosegue, con i costi non disponibili."""
    if settings.fake:
        return None
    models = load_catalog(settings.cache_dir)
    info = find_model(models, settings.model)
    if models and not info:
        hints = ", ".join(suggest_models(models, settings.model))
        hint = f" Forse: {hints}." if hints else ""
        raise _fail(
            f"Il modello '{settings.model}' non è nel catalogo di OpenRouter.{hint} "
            "L'elenco è in `bookpack models`."
        )
    return info


def _prices(settings: Settings, info: ModelInfo | None) -> tuple[float, float] | None:
    return (0.0, 0.0) if settings.fake else info.prices if info else None


def _parse_chapters(value: str | None) -> set[int] | None:
    if not value:
        return None
    selected: set[int] = set()
    for part in value.split(","):
        match = _RANGE.match(part.strip())
        if not match:
            raise _fail(f"--chapters non valido: '{part}'. Esempi: 3, 1-3, 1-3,7")
        start = int(match.group(1))
        end = int(match.group(2) or start)
        if end < start:
            raise _fail(f"--chapters non valido: '{part}'")
        selected.update(range(start, end + 1))
    return selected


def _format_cost(cost: float | None) -> str:
    return "n/d" if cost is None else f"${cost:.2f}"


def _print_metadata(doc: PdfDocument, detection: Detection) -> None:
    console.print(f"[bold]{book_title(doc, detection)}[/bold]", highlight=False)
    author = detection.book.get("author") or doc.author or "autore sconosciuto"
    labels = {
        "file": "file --toc",
        "outline": "outline del PDF",
        "headings": "euristiche sui titoli",
        "llm": "LLM",
        "none": "nessuno",
    }
    console.print(
        f"{author} | {doc.page_count} pagine | rilevamento: {labels[detection.method]}",
        highlight=False,
    )


@app.command()
def inspect(
    pdf: Path = typer.Argument(..., exists=True, dir_okay=False),
    toc: Path | None = typer.Option(None, "--toc", exists=True, dir_okay=False),
    include_all: bool = typer.Option(False, "--include-all", help="Includi le sezioni escluse."),
    model: str | None = typer.Option(None, "--model", help="Modello per la stima del costo."),
) -> None:
    """Mostra metadati, capitoli rilevati e stima del costo. Non usa l'LLM."""
    doc, detection = _load(pdf, toc, include_all)
    settings = _settings(model)
    info = _model_info(settings)
    budget = context_budget(settings.context_tokens, info)
    pages = clean_pages(doc.pages)

    _print_metadata(doc, detection)
    if not detection.chapters:
        console.print(
            "[yellow]Nessun capitolo rilevato.[/yellow] `build` chiederà la divisione all'LLM; "
            "in alternativa scrivi un file e passalo con --toc."
        )
        raise typer.Exit()

    table = Table(show_edge=False)
    for column, justify in [("#", "right"), ("Titolo", "left"), ("Pagine", "right")]:
        table.add_column(column, justify=justify)
    table.add_column("Parole", justify="right")
    table.add_column("Token", justify="right")
    table.add_column("Chiamate", justify="right")

    numbers = {id(section): index for index, section in numbered_chapters(detection)}
    usable = []
    for section in detection.sections:
        pages_label = f"{section.page_start}-{section.page_end}"
        if section.excluded:
            table.add_row("", f"[dim]{section.title} (esclusa)[/dim]", f"[dim]{pages_label}[/dim]")
            continue
        words = word_count(section, pages)
        if is_too_short(section, pages):
            table.add_row(
                str(numbers[id(section)]),
                f"[dim]{section.title} (troppo breve, saltata)[/dim]",
                f"[dim]{pages_label}[/dim]",
                f"[dim]{words:,}[/dim]",
            )
            continue
        usable.append(section)
        part = estimate_section(section, pages, budget)
        table.add_row(
            str(numbers[id(section)]),
            section.title,
            pages_label,
            f"{words:,}",
            f"{part.input_tokens:,}",
            str(part.calls),
        )
    console.print(table)

    total = estimate_build(usable, pages, _prices(settings, info), budget)
    console.print(
        f"Stima con {settings.model}: {total.calls} chiamate, {total.input_tokens:,} token in input, "
        f"{total.output_tokens:,} in output, costo {_format_cost(total.cost)}",
        highlight=False,
    )


@app.command()
def models(
    query: str = typer.Argument("", help="Parole da cercare, es. 'claude sonnet'."),
    refresh: bool = typer.Option(False, "--refresh", help="Riscarica il catalogo."),
) -> None:
    """Elenca i modelli di OpenRouter con i prezzi per milione di token."""
    settings = _settings()
    catalog = load_catalog(settings.cache_dir, refresh)
    if not catalog:
        raise _fail("Catalogo non disponibile: controlla la connessione.")
    found = search_models(catalog, query)
    table = Table(show_edge=False)
    table.add_column("Modello")
    table.add_column("Input", justify="right")
    table.add_column("Output", justify="right")
    table.add_column("Contesto", justify="right")
    table.add_column("Schema", justify="center")
    for model in found:
        table.add_row(
            model.id,
            "n/d" if model.input_price is None else f"${model.input_price:.2f}",
            "n/d" if model.output_price is None else f"${model.output_price:.2f}",
            f"{model.context_length:,}" if model.context_length else "n/d",
            "sì" if model.structured else "no",
        )
    console.print(table)
    console.print(f"{len(found)} modelli. Si sceglie con --model o BOOKPACK_MODEL.")


@app.command()
def gui(
    pdf: Path | None = typer.Argument(None, exists=True, dir_okay=False),
) -> None:
    """Apre la finestra per scegliere il PDF e i parametri."""
    try:
        from .gui import run
    except ImportError as exc:
        raise _fail(f"Tkinter non è disponibile in questo Python: {exc}") from exc
    run(pdf)


@app.command()
def toc(
    pdf: Path = typer.Argument(..., exists=True, dir_okay=False),
    output: Path = typer.Option(..., "-o", "--output", help="File YAML da scrivere."),
) -> None:
    """Esporta la divisione rilevata in YAML, da correggere a mano."""
    doc, detection = _load(pdf, None, False)
    if not detection.sections:
        raise _fail("Nessun capitolo rilevato: scrivi il file a mano o usa `build`.")
    write_toc_file(doc, detection, output)
    console.print(f"[green]{len(detection.sections)} sezioni scritte in[/green] {output}")


@app.command()
def build(
    pdf: Path = typer.Argument(..., exists=True, dir_okay=False),
    output: Path | None = typer.Option(
        None, "-o", "--output", help="Default: generator/out/<id>.bookpack.json"
    ),
    toc: Path | None = typer.Option(None, "--toc", exists=True, dir_okay=False),
    chapters: str | None = typer.Option(None, "--chapters", help="Es. 1-3 oppure 1-3,7"),
    lang: str | None = typer.Option(None, "--lang", help="Lingua di output (default: del libro)."),
    model: str | None = typer.Option(None, "--model", help="Id del modello su OpenRouter."),
    fake: bool = typer.Option(False, "--fake", help="Prova gratis, senza LLM né rete."),
    include_all: bool = typer.Option(False, "--include-all", help="Includi le sezioni escluse."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Ignora la cache delle risposte."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Non chiedere conferma del costo."),
) -> None:
    """Genera il pack. Mostra la stima del costo e chiede conferma, salvo --yes."""
    doc, detection = _load(pdf, toc, include_all)
    settings = _settings(model, fake)
    info = _model_info(settings)
    budget = context_budget(settings.context_tokens, info)
    selected = _parse_chapters(chapters)
    pages = clean_pages(doc.pages)

    try:
        llm = StructuredLLM(
            get_provider(settings, info), ResponseCache(settings.cache_dir, enabled=not no_cache)
        )
    except LLMError as exc:
        raise _fail(str(exc)) from exc

    _print_metadata(doc, detection)
    if not detection.chapters and detection.method == "none":
        console.print("[yellow]Nessun capitolo rilevato:[/yellow] serve una chiamata all'LLM.")
        if not yes:
            typer.confirm("Procedere?", abort=True)
        try:
            detection = detect_with_llm(llm, doc, pages)
        except LLMError as exc:
            raise _fail(str(exc)) from exc

    targets = target_sections(detection, pages, selected)
    estimate = estimate_build(targets, pages, _prices(settings, info), budget)
    console.print(
        f"{len(targets)} capitoli con {settings.model}: circa {estimate.calls} chiamate, "
        f"{estimate.input_tokens:,} token in input, {estimate.output_tokens:,} in output, "
        f"costo stimato {_format_cost(estimate.cost)} (le risposte in cache non si ripagano)",
        highlight=False,
    )
    if not yes:
        typer.confirm("Procedere?", abort=True)

    progress_columns = (SpinnerColumn(), TextColumn("{task.description}"), TimeElapsedColumn())
    try:
        with Progress(*progress_columns, console=console, transient=True) as progress:
            task = progress.add_task("Avvio")

            def on_step(step: str) -> None:
                progress.update(task, description=step)
                progress.console.print(f"[dim]{step}[/dim]", highlight=False)

            result = build_pack(llm, doc, pages, detection, selected, lang, budget, on_step)
    except (LLMError, PackError) as exc:
        console.print(
            "[dim]Le risposte già ottenute sono in cache: rilanciando non si ripagano.[/dim]"
        )
        raise _fail(str(exc)) from exc

    for skipped in result.skipped:
        console.print(f"[yellow]saltato[/yellow] {skipped}", highlight=False)
    for note in result.notes:
        console.print(f"[yellow]nota[/yellow] {note}", highlight=False)
    for warning in result.report.warnings:
        console.print(f"[yellow]avviso[/yellow] {warning}", highlight=False)
    for error in result.report.errors:
        console.print(f"[red]errore[/red] {error}", highlight=False)
    if not result.report.ok:
        raise _fail("Il pack generato non rispetta i vincoli e non è stato scritto.")

    path = write_pack(result.pack, output)

    usage = llm.usage
    spent = "" if usage.cost is None else f", costo effettivo ${usage.cost:.2f}"
    console.print(
        f"[green]Pack scritto in[/green] {path}: {len(result.pack.chapters)} capitoli. "
        f"Chiamate {usage.calls}, dalla cache {usage.cached}, ritentativi {usage.retries}, "
        f"token {usage.input_tokens:,} in / {usage.output_tokens:,} out{spent}",
        highlight=False,
    )


@app.command()
def schema(
    output: Path = typer.Option(
        DEFAULT_SCHEMA_PATH, "-o", "--output", help="File di destinazione."
    ),
) -> None:
    """Esporta lo schema JSON del book pack."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(export_schema(), indent=2, ensure_ascii=False) + "\n", "utf-8")
    console.print(f"[green]Schema scritto in[/green] {output}")


@app.command()
def validate(pack_path: Path = typer.Argument(..., exists=True, dir_okay=False)) -> None:
    """Valida un pack contro schema e vincoli."""
    try:
        data = json.loads(pack_path.read_text("utf-8"))
    except json.JSONDecodeError as exc:
        raise _fail(f"JSON non valido: {exc}") from exc

    pack, report = validate_data(data)
    for warning in report.warnings:
        console.print(f"[yellow]avviso[/yellow] {warning}", highlight=False)
    for error in report.errors:
        console.print(f"[red]errore[/red] {error}", highlight=False)
    if not report.ok:
        raise _fail(f"Pack non valido: {len(report.errors)} errori")
    assert pack is not None
    console.print(
        f"[green]Pack valido:[/green] {pack.book.title}, {len(pack.chapters)} capitoli, "
        f"{len(report.warnings)} avvisi",
        highlight=False,
    )
