"""Costruzione del pack: dal PDF già estratto al modello BookPack validato."""

import hashlib
import json
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from .. import __version__
from ..config import DEFAULT_OUTPUT_DIR
from ..extract.lang import detect_lang
from ..extract.pdf import PdfDocument
from ..extract.toc import Detection, Section, book_title
from ..llm.structured import StructuredLLM
from ..models import SCHEMA_VERSION, Book, BookPack, Chapter, GeneratorInfo
from ..validate import Report, check_pack
from .book import condense_book
from .chapter import condense_chapter
from .chunking import word_count

# Una sezione più corta non regge 5 card senza inventare (es. la pagina di apertura di una parte)
MIN_CHAPTER_WORDS = 150
COVER_COLORS = [
    "#1f6feb", "#0f766e", "#b45309", "#be123c", "#6d28d9", "#15803d", "#0e7490", "#a21caf",
]  # fmt: skip


class PackError(Exception):
    pass


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


def build_pack(
    llm: StructuredLLM,
    doc: PdfDocument,
    pages: dict[int, str],
    detection: Detection,
    selected: set[int] | None = None,
    lang: str | None = None,
    context_tokens: int = 40_000,
    on_step: Callable[[str], None] = lambda _: None,
) -> BuildResult:
    title = book_title(doc, detection)
    author = detection.book.get("author") or doc.author
    book_id = slugify(detection.book.get("id") or title)
    sample = " ".join(list(pages.values())[: min(30, len(pages))])
    output_lang = lang or detection.book.get("lang") or detect_lang(sample)

    chapters: list[Chapter] = []
    skipped: list[str] = []
    notes: list[str] = []
    for index, section in numbered_chapters(detection):
        if selected is not None and index not in selected:
            continue
        if is_too_short(section, pages):
            skipped.append(f"{index}. {section.title} (troppo breve)")
            continue
        on_step(f"Capitolo {index}: {section.title}")
        chapters.append(
            condense_chapter(llm, section, index, pages, title, output_lang, context_tokens, notes)
        )
    if not chapters:
        raise PackError("Nessun capitolo da condensare: controlla --chapters e la divisione.")

    on_step("Panoramica del libro")
    overview, glossary = condense_book(llm, chapters, title, author, output_lang)

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
