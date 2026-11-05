"""Costruzione del pack: dal PDF già estratto al modello BookPack validato."""

import hashlib
import json
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

from .. import __version__
from ..config import DEFAULT_OUTPUT_DIR
from ..extract.lang import detect_lang
from ..extract.pdf import PdfDocument
from ..extract.toc import Detection, Section, book_title
from ..llm.structured import StructuredLLM
from ..models import SCHEMA_VERSION, Book, BookPack, GeneratorInfo
from ..validate import Report, check_pack
from .book import condense_book
from .chapter import chapter_id, condense_part, wrap_chapter
from .chunking import split_parts, word_count
from .state import BuildInput, BuildState
from .tasks import Task, TaskRunner

# Una sezione più corta non regge 5 card senza inventare (es. la pagina di apertura di una parte)
MIN_CHAPTER_WORDS = 150
BOOK_TASK = "book"
COVER_COLORS = [
    "#1f6feb", "#0f766e", "#b45309", "#be123c", "#6d28d9", "#15803d", "#0e7490", "#a21caf",
]  # fmt: skip


class PackError(Exception):
    pass


class BuildIncomplete(PackError):
    """Mancano delle attività, perché fallite o interrotte. `failures` è vuoto se interrotta."""

    def __init__(self, failures: dict[str, str], done: int, total: int) -> None:
        self.failures = failures
        self.done = done
        self.total = total
        reason = f"{len(failures)} non riuscite" if failures else "generazione interrotta"
        super().__init__(f"{reason}, {done} attività completate su {total}.")


@dataclass
class BuildResult:
    pack: BookPack
    report: Report
    skipped: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "libro"


def cover_color(book_id: str) -> str:
    digest = hashlib.sha256(book_id.encode()).digest()
    return COVER_COLORS[digest[0] % len(COVER_COLORS)]


def numbered_chapters(detection: Detection) -> list[tuple[int, Section]]:
    """Numera i capitoli sull'elenco completo: `--chapters` non deve cambiare gli id."""
    return list(enumerate(detection.chapters, start=1))


def is_too_short(section: Section, pages: dict[int, str]) -> bool:
    return word_count(section, pages) < MIN_CHAPTER_WORDS


def target_sections(
    detection: Detection, pages: dict[int, str], selected: set[int] | None
) -> list[Section]:
    """Le sezioni che verranno davvero condensate."""
    return [
        section
        for index, section in numbered_chapters(detection)
        if (selected is None or index in selected) and not is_too_short(section, pages)
    ]


def default_output_path(book_title_or_id: str) -> Path:
    return DEFAULT_OUTPUT_DIR / f"{slugify(book_title_or_id)}.bookpack.json"


def write_pack(pack: BookPack, output: Path | None = None) -> Path:
    path = output or default_output_path(pack.book.id)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = pack.model_dump(mode="json", exclude_none=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", "utf-8")
    return path


def book_id_of(doc: PdfDocument, detection: Detection) -> str:
    return slugify(detection.book.get("id") or book_title(doc, detection))


def make_input(
    pdf: Path,
    pdf_sha256: str,
    model: str,
    fake: bool,
    lang: str | None,
    selected: set[int] | None,
    output: Path,
    context_tokens: int,
    detection: Detection,
) -> BuildInput:
    """I parametri da conservare per riprendere: tutto ciò da cui dipendono i prompt."""
    chosen = range(1, len(detection.chapters) + 1) if selected is None else selected
    return BuildInput(
        pdf=str(pdf.resolve()),
        pdf_sha256=pdf_sha256,
        model=model,
        fake=fake,
        lang=lang,
        selected=sorted(chosen),
        output=str(output),
        context_tokens=context_tokens,
        detection=detection,
    )


def build_pack(
    llm: StructuredLLM,
    doc: PdfDocument,
    pages: dict[int, str],
    detection: Detection,
    selected: set[int] | None = None,
    lang: str | None = None,
    context_tokens: int = 40_000,
    on_step: Callable[[str, int, int], None] = lambda *_: None,
    workers: int = 1,
    should_stop: Callable[[], bool] = lambda: False,
    state: BuildState | None = None,
) -> BuildResult:
    """Lavora per fasi: tutte le parti, poi la chiusura dei capitoli, infine il libro.

    Dentro una fase le attività non dipendono l'una dall'altra e girano insieme; `on_step` riceve
    etichetta, attività riuscite e totale. Solleva BuildIncomplete se qualcosa manca: ciò che è
    pronto resta in cache, quindi rilanciando si rifà solo il resto. `should_stop` viene chiamata
    da più thread.
    """
    title = book_title(doc, detection)
    author = detection.book.get("author") or doc.author
    book_id = book_id_of(doc, detection)
    sample = " ".join(list(pages.values())[: min(30, len(pages))])
    output_lang = lang or detection.book.get("lang") or detect_lang(sample)

    targets: list[tuple[int, Section, list[str]]] = []
    skipped: list[str] = []
    for index, section in numbered_chapters(detection):
        if selected is not None and index not in selected:
            continue
        if is_too_short(section, pages):
            skipped.append(f"{index}. {section.title} (troppo breve)")
            continue
        targets.append((index, section, split_parts(section, pages, context_tokens)))
    if not targets:
        raise PackError("Nessun capitolo da condensare: controlla --chapters e la divisione.")

    part_tasks = [
        Task(
            f"{chapter_id(index)}/part-{number}",
            f"Capitolo {index}, parte {number} di {len(texts)}: {section.title}",
            partial(
                condense_part, llm, text, number, len(texts), section, index, title, output_lang
            ),
        )
        for index, section, texts in targets
        for number, text in enumerate(texts, start=1)
    ]
    total = len(part_tasks) + len(targets) + 1
    if state:
        state.plan(
            [
                *(task.name for task in part_tasks),
                *(f"{chapter_id(index)}/wrap" for index, _, _ in targets),
                BOOK_TASK,
            ]
        )

    finished = 0

    def on_finished(task: Task, error: str | None) -> None:
        nonlocal finished
        finished += error is None
        if state:
            state.mark(task.name, error, llm.usage)
        on_step(task.label if error is None else f"Non riuscita: {task.label}", finished, total)

    runner = TaskRunner(max(1, workers), should_stop, on_finished)

    parts = runner.run(part_tasks)
    notes: list[str] = []
    wrap_tasks: list[Task] = []
    for index, section, texts in targets:
        done = [parts.get(f"{chapter_id(index)}/part-{n}") for n in range(1, len(texts) + 1)]
        if None in done:
            continue
        notes.extend(note for part in done for note in part.notes)
        wrap_tasks.append(
            Task(
                f"{chapter_id(index)}/wrap",
                f"Capitolo {index}, riassunto e flashcard: {section.title}",
                partial(wrap_chapter, llm, done, section, index, title, output_lang),
            )
        )

    wrapped = runner.run(wrap_tasks)
    chapters = [wrapped[task.name] for task in wrap_tasks if task.name in wrapped]

    if len(chapters) == len(targets):
        book_task = Task(
            BOOK_TASK,
            "Panoramica del libro",
            partial(condense_book, llm, chapters, title, author, output_lang),
        )
        book = runner.run([book_task]).get(BOOK_TASK)
    else:
        book = None
    if book is None:
        raise BuildIncomplete(runner.failures, finished, total)
    overview, glossary = book

    pack = BookPack(
        schemaVersion=SCHEMA_VERSION,
        generator=GeneratorInfo(
            version=__version__,
            model=llm.provider.model,
            generatedAt=datetime.now(UTC).isoformat(timespec="seconds"),
        ),
        book=Book(
            id=book_id,
            title=title,
            author=author,
            lang=output_lang,
            sourcePages=doc.page_count,
            coverColor=cover_color(book_id),
        ),
        overview=overview,
        chapters=chapters,
        glossary=glossary,
    )
    return BuildResult(pack, check_pack(pack), skipped, notes)
