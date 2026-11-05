"""Rilevamento dei capitoli: file utente, outline del PDF, euristiche sui titoli."""

import re
import string
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median

import yaml

from .pdf import Line, OutlineEntry, PdfDocument

MIN_CHAPTERS = 3
MAX_CHAPTERS = 60
# Sopra questa mediana di pagine un livello dell'outline è fatto di parti, non di capitoli
MAX_MEDIAN_PAGES = 60

_EXCLUDED_SECTIONS = re.compile(
    r"^(?:"
    r"copertina|cover|front cover|back cover|retro di copertina|frontespizio|title page|half title"
    r"|copyright|colophon|crediti|credits|dedica|dedication"
    r"|indice|indice generale|indice analitico|indice dei nomi|sommario"
    r"|contents|table of contents|index|list of (?:figures|tables)"
    r"|ringraziamenti|acknowledge?ments|bibliografia|bibliography|references|riferimenti bibliografici"
    r"|about the authors?|l'autore|gli autori|also by .*|altri libri .*"
    r")$",
    re.I,
)
_NUMBER_PREFIX = re.compile(r"^(?:\d+(?:\.\d+)*\.?|[ivxlc]+\.)\s+", re.I)
_CHAPTER_LABEL = re.compile(
    r"^(?:capitolo|cap\.|chapter|lezione|lesson)\s+(?:\d+|[ivxlc]+|[a-zà-ÿ]+)\b", re.I
)
_BARE_NUMBER = re.compile(r"^(?:\d{1,3}|[IVXLC]+)\.?$")
_BARE_LABEL = re.compile(r"^(?:capitolo|cap\.|chapter|lezione|lesson)\s+\S+$", re.I)
_MAX_HEADING_WORDS = 14
_HEADING_SIZE_RATIO = 1.2
_TOP_OF_PAGE = 0.5


class TocError(Exception):
    pass


@dataclass
class Section:
    title: str
    page_start: int
    page_end: int
    excluded: bool = False


@dataclass
class Detection:
    method: str  # file | outline | headings | llm | none
    sections: list[Section] = field(default_factory=list)
    book: dict[str, str] = field(default_factory=dict)
    note: str | None = None

    @property
    def chapters(self) -> list[Section]:
        return [section for section in self.sections if not section.excluded]


def set_section_pages(
    sections: list[Section], position: int, start: int, end: int, page_count: int
) -> None:
    """Cambia l'intervallo di una sezione. I vicini seguono il confine se lo toccavano.

    Un vuoto voluto tra due sezioni resta: la sezione vicina si sposta solo se era contigua al
    vecchio confine o se finirebbe per sovrapporsi a quello nuovo.
    """
    if not 1 <= start <= end <= page_count:
        raise TocError(
            f"Le pagine devono andare da 1 a {page_count}, con l'inizio prima della fine."
        )

    section = sections[position]
    old_start, old_end = section.page_start, section.page_end
    section.page_start, section.page_end = start, end

    if position > 0 and start != old_start:
        previous = sections[position - 1]
        if previous.page_end == old_start - 1 or previous.page_end >= start:
            previous.page_end = max(previous.page_start, start - 1)
    if position + 1 < len(sections) and end != old_end:
        following = sections[position + 1]
        if following.page_start == old_end + 1 or following.page_start <= end:
            following.page_start = min(following.page_end, end + 1)


def find_overlaps(sections: list[Section]) -> set[int]:
    """Posizioni delle sezioni incluse che condividono pagine con un'altra sezione inclusa."""
    included = [(i, section) for i, section in enumerate(sections) if not section.excluded]
    overlapping: set[int] = set()
    for offset, (i, first) in enumerate(included):
        for j, second in included[offset + 1 :]:
            if first.page_start <= second.page_end and second.page_start <= first.page_end:
                overlapping.update((i, j))
    return overlapping


def is_excluded_title(title: str) -> bool:
    return bool(_EXCLUDED_SECTIONS.match(_NUMBER_PREFIX.sub("", title).strip(" .:")))


def _nice_title(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return string.capwords(text) if text.isupper() else text


# --- Outline -----------------------------------------------------------------------------------


def _frontier(entries: list[OutlineEntry], level: int, page_count: int) -> list[Section]:
    """Le voci al livello dato, più le foglie dei livelli superiori (es. "Prefazione")."""
    sections: list[Section] = []
    for i, entry in enumerate(entries):
        if entry.level > level:
            continue
        following = entries[i + 1] if i + 1 < len(entries) else None
        has_children = following is not None and following.level > entry.level
        if entry.level < level and has_children:
            continue
        end = page_count
        for later in entries[i + 1 :]:
            if later.level <= level:
                end = max(entry.page, later.page - 1)
                break
        sections.append(Section(entry.title, entry.page, end, is_excluded_title(entry.title)))
    return sections


def from_outline(doc: PdfDocument) -> list[Section] | None:
    entries = doc.outline
    if not entries:
        return None
    candidates: list[tuple[float, list[Section]]] = []
    for level in sorted({entry.level for entry in entries}):
        sections = _frontier(entries, level, doc.page_count)
        included = [section for section in sections if not section.excluded]
        if not MIN_CHAPTERS <= len(included) <= MAX_CHAPTERS:
            continue
        pages = median(section.page_end - section.page_start + 1 for section in included)
        if pages <= MAX_MEDIAN_PAGES:
            return sections
        candidates.append((pages, sections))
    return min(candidates, key=lambda item: item[0])[1] if candidates else None


# --- Euristiche sui titoli ---------------------------------------------------------------------


def _body_size(doc: PdfDocument) -> float:
    weights: Counter[float] = Counter()
    for page in doc.pages:
        for line in page.lines:
            weights[line.size] += len(line.text)
    return weights.most_common(1)[0][0] if weights else 0.0


def _running_heads(doc: PdfDocument) -> set[str]:
    counts: Counter[str] = Counter()
    for page in doc.pages:
        counts.update({line.text.strip().lower() for line in page.lines})
    return {text for text, count in counts.items() if count >= MIN_CHAPTERS}


def _is_candidate_shape(line: Line) -> bool:
    text = line.text.strip()
    if not text or len(text.split()) > _MAX_HEADING_WORDS:
        return False
    if re.search(r"(?:\.{3,}|\s)\d{1,4}$", text) and not _BARE_LABEL.match(text):
        return False  # riga di un indice testuale: "Capitolo 1 ..... 12"
    return not (text[-1] in ".,;:" and not _BARE_NUMBER.match(text))


def _merge_title(lines: list[Line]) -> str:
    parts = [line.text.strip() for line in lines]
    if len(parts) > 1 and (_BARE_NUMBER.match(parts[0]) or _BARE_LABEL.match(parts[0])):
        parts = parts[1:]
    return _nice_title(" ".join(parts))


def _sections_from_starts(doc: PdfDocument, starts: list[tuple[int, str]]) -> list[Section]:
    sections = []
    for i, (page, title) in enumerate(starts):
        end = starts[i + 1][0] - 1 if i + 1 < len(starts) else doc.page_count
        sections.append(Section(title, page, max(page, end), is_excluded_title(title)))
    return sections


def _heading_block(lines: list[Line], start: int, size: float) -> list[Line]:
    block = [lines[start]]
    for line in lines[start + 1 :]:
        if line.size < size * 0.95 or not _is_candidate_shape(line) or len(block) >= 3:
            break
        block.append(line)
    return block


def from_headings(doc: PdfDocument) -> list[Section] | None:
    body = _body_size(doc)
    if not body:
        return None
    repeated = _running_heads(doc)

    # Prima i titoli espliciti ("Capitolo 3", "Chapter III"), che sono i più affidabili
    labelled: list[tuple[int, str]] = []
    for page in doc.pages:
        for i, line in enumerate(page.lines):
            if line.y > _TOP_OF_PAGE or not _is_candidate_shape(line):
                continue
            prominent = line.size > body * 1.05 or line.bold
            if prominent and _CHAPTER_LABEL.match(line.text.strip()):
                labelled.append(
                    (page.number, _merge_title(_heading_block(page.lines, i, line.size)))
                )
                break
    if MIN_CHAPTERS <= len(labelled) <= MAX_CHAPTERS:
        return _sections_from_starts(doc, labelled)

    # Altrimenti le righe in evidenza per dimensione, dalla più grande a scendere
    by_size: dict[float, list[tuple[int, int]]] = {}
    for page in doc.pages[1:]:  # la prima pagina è di solito il frontespizio
        for i, line in enumerate(page.lines):
            if (
                line.y <= _TOP_OF_PAGE
                and line.size >= body * _HEADING_SIZE_RATIO
                and _is_candidate_shape(line)
                and line.text.strip().lower() not in repeated
            ):
                by_size.setdefault(line.size, []).append((page.number, i))

    pages_by_number = {page.number: page for page in doc.pages}
    for size in sorted(by_size, reverse=True):
        starts: list[tuple[int, str]] = []
        for number, i in by_size[size]:
            if starts and starts[-1][0] == number:
                continue  # un solo titolo per pagina
            page = pages_by_number[number]
            starts.append((number, _merge_title(_heading_block(page.lines, i, size))))
        sections = _sections_from_starts(doc, starts)
        included = [section for section in sections if not section.excluded]
        if MIN_CHAPTERS <= len(included) <= MAX_CHAPTERS:
            return sections
    return None


# --- File utente -------------------------------------------------------------------------------

_TOC_HEADER = """\
# Divisione in capitoli di bookpack. Correggila a mano e passala a `bookpack build --toc`.
# - pageStart e pageEnd sono numeri di pagina del PDF, a partire da 1.
# - `exclude: true` salta la sezione. Cambiare l'ordine dei capitoli cambia i loro id.
"""


def write_toc_file(doc: PdfDocument, detection: Detection, path: Path) -> None:
    data = {
        "book": {
            "title": doc.title or _title_from_stem(doc.path),
            "author": doc.author,
            **detection.book,
        },
        "chapters": [
            {
                "title": section.title,
                "pageStart": section.page_start,
                "pageEnd": section.page_end,
                **({"exclude": True} if section.excluded else {}),
            }
            for section in detection.sections
        ],
    }
    body = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100)
    path.write_text(_TOC_HEADER + body, "utf-8")


def read_toc_file(path: Path, page_count: int) -> Detection:
    try:
        data = yaml.safe_load(path.read_text("utf-8"))
    except yaml.YAMLError as exc:
        raise TocError(f"{path}: YAML non valido: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("chapters"), list):
        raise TocError(f"{path}: manca la lista 'chapters'")

    sections: list[Section] = []
    for i, item in enumerate(data["chapters"], start=1):
        try:
            title = str(item["title"]).strip()
            start, end = int(item["pageStart"]), int(item["pageEnd"])
        except (KeyError, TypeError, ValueError) as exc:
            raise TocError(
                f"{path}: la voce {i} deve avere title, pageStart e pageEnd numerici"
            ) from exc
        if not title:
            raise TocError(f"{path}: la voce {i} ha un titolo vuoto")
        if not 1 <= start <= end <= page_count:
            raise TocError(
                f"{path}: '{title}' ha pagine {start}-{end} non valide (il PDF ha {page_count} pagine)"
            )
        sections.append(Section(title, start, end, bool(item.get("exclude", False))))

    if not any(not section.excluded for section in sections):
        raise TocError(f"{path}: tutti i capitoli sono esclusi")
    book = {
        key: str(value)
        for key, value in (data.get("book") or {}).items()
        if value not in (None, "")
    }
    return Detection("file", sections, book)


# --- Punto d'ingresso --------------------------------------------------------------------------


def _title_from_stem(path: Path) -> str:
    return re.sub(r"[_\-.]+", " ", path.stem).strip()


def book_title(doc: PdfDocument, detection: Detection) -> str:
    return detection.book.get("title") or doc.title or _title_from_stem(doc.path)


def detect_chapters(
    doc: PdfDocument, toc_file: Path | None = None, include_all: bool = False
) -> Detection:
    """Applica in ordine file utente, outline ed euristiche. Non usa mai l'LLM."""
    if toc_file:
        detection = read_toc_file(toc_file, doc.page_count)
    elif sections := from_outline(doc):
        detection = Detection("outline", sections)
    elif sections := from_headings(doc):
        detection = Detection("headings", sections)
    else:
        detection = Detection("none", note="Nessun capitolo rilevato da outline o titoli.")
    if include_all:
        for section in detection.sections:
            section.excluded = False
    return detection
