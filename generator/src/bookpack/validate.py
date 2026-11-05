"""Vincoli del pack oltre lo schema: lunghezze, unicità, coerenza di id e pagine.

Il piano indica alcuni limiti come "circa": oltre il limite nominale si produce un avviso,
oltre la tolleranza un errore. Per le citazioni il limite è rigido.
"""

import re
from dataclasses import dataclass, field

from pydantic import ValidationError

from .models import MAX_CARDS, BookPack, Card, CardType, Chapter, Flashcard

BODY_WORDS_SOFT = 60
BODY_WORDS_HARD = 75
TITLE_WORDS_SOFT = 8
TITLE_WORDS_HARD = 12
QUOTE_WORDS_MAX = 25
MAX_QUOTES_PER_CHAPTER = 1
MINDMAP_MAX_DEPTH = 4
MINDMAP_NODES_SOFT = 25
MINDMAP_NODES_HARD = 45
BOOK_MINDMAP_NODES_HARD = 150

_HEADING = re.compile(r"^(#{1,6})\s+\S")
_LIST_ITEM = re.compile(r"^(\s*)(?:[-*+]|\d+\.)\s+\S")


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def extend(self, other: "Report") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def word_count(text: str) -> int:
    return len(text.split())


def mindmap_stats(markdown: str) -> tuple[int, int]:
    """Restituisce (profondità massima, numero di nodi) di una mindmap markdown."""
    depth = 0
    nodes = 0
    heading_level = 0
    for line in markdown.splitlines():
        if not line.strip():
            continue
        if match := _HEADING.match(line):
            heading_level = len(match.group(1))
            level = heading_level
        elif match := _LIST_ITEM.match(line):
            indent = len(match.group(1).expandtabs(2))
            level = heading_level + 1 + indent // 2
        else:
            continue
        nodes += 1
        depth = max(depth, level)
    return depth, nodes


def _check_card(card: Card, chapter: Chapter, report: Report) -> None:
    where = f"{card.id}"
    words = word_count(card.body)
    if card.type == CardType.QUOTE:
        if words > QUOTE_WORDS_MAX:
            report.errors.append(
                f"{where}: citazione di {words} parole (massimo {QUOTE_WORDS_MAX})"
            )
    elif words > BODY_WORDS_HARD:
        report.errors.append(f"{where}: body di {words} parole (massimo circa {BODY_WORDS_SOFT})")
    elif words > BODY_WORDS_SOFT:
        report.warnings.append(f"{where}: body di {words} parole (consigliate {BODY_WORDS_SOFT})")

    if card.title:
        title_words = word_count(card.title)
        if title_words > TITLE_WORDS_HARD:
            report.errors.append(
                f"{where}: title di {title_words} parole (massimo circa {TITLE_WORDS_SOFT})"
            )
        elif title_words > TITLE_WORDS_SOFT:
            report.warnings.append(
                f"{where}: title di {title_words} parole (consigliate {TITLE_WORDS_SOFT})"
            )

    if card.page is None:
        if card.type != CardType.TAKEAWAY:
            report.errors.append(f"{where}: manca la pagina di origine")
    elif not chapter.pageStart <= card.page <= chapter.pageEnd:
        report.errors.append(
            f"{where}: pagina {card.page} fuori dal capitolo "
            f"({chapter.pageStart}-{chapter.pageEnd})"
        )


def _check_flashcard(card: Flashcard, chapter: Chapter, report: Report) -> None:
    if not chapter.pageStart <= card.page <= chapter.pageEnd:
        report.errors.append(
            f"{card.id}: pagina {card.page} fuori dal capitolo "
            f"({chapter.pageStart}-{chapter.pageEnd})"
        )


def _check_mindmap(markdown: str, where: str, report: Report, hard_nodes: int, soft: int) -> None:
    depth, nodes = mindmap_stats(markdown)
    if nodes == 0:
        report.errors.append(f"{where}: mindmap vuota o senza heading e liste")
    if depth > MINDMAP_MAX_DEPTH:
        report.errors.append(
            f"{where}: mindmap con profondità {depth} (massimo {MINDMAP_MAX_DEPTH})"
        )
    if nodes > hard_nodes:
        report.errors.append(f"{where}: mindmap con {nodes} nodi (massimo circa {soft})")
    elif nodes > soft:
        report.warnings.append(f"{where}: mindmap con {nodes} nodi (consigliati {soft})")


def check_chapter(chapter: Chapter) -> Report:
    report = Report()
    where = chapter.id

    if chapter.pageEnd < chapter.pageStart:
        report.errors.append(f"{where}: pageEnd precede pageStart")
    if chapter.id != f"ch-{chapter.index:02d}":
        report.errors.append(f"{where}: id non coerente con index {chapter.index}")

    if chapter.cards[-1].type != CardType.TAKEAWAY:
        report.errors.append(f"{where}: l'ultima card deve essere di tipo takeaway")
    takeaways = sum(card.type == CardType.TAKEAWAY for card in chapter.cards)
    if takeaways > 1:
        report.warnings.append(f"{where}: {takeaways} card takeaway (attesa una)")
    quotes = sum(card.type == CardType.QUOTE for card in chapter.cards)
    if quotes > MAX_QUOTES_PER_CHAPTER:
        report.errors.append(f"{where}: {quotes} citazioni (massimo {MAX_QUOTES_PER_CHAPTER})")

    for card in chapter.cards:
        if not card.id.startswith(f"{chapter.id}-"):
            report.errors.append(f"{card.id}: id non appartiene al capitolo {chapter.id}")
        _check_card(card, chapter, report)
    for flashcard in chapter.flashcards:
        if not flashcard.id.startswith(f"{chapter.id}-"):
            report.errors.append(f"{flashcard.id}: id non appartiene al capitolo {chapter.id}")
        _check_flashcard(flashcard, chapter, report)

    _check_mindmap(chapter.mindmap, where, report, MINDMAP_NODES_HARD, MINDMAP_NODES_SOFT)
    return report


def check_pack(pack: BookPack) -> Report:
    report = Report()

    seen: set[str] = set()
    for chapter in pack.chapters:
        ids = [chapter.id, *(c.id for c in chapter.cards), *(f.id for f in chapter.flashcards)]
        for item in ids:
            if item in seen:
                report.errors.append(f"id duplicato: {item}")
            seen.add(item)
        report.extend(check_chapter(chapter))

    indexes = [chapter.index for chapter in pack.chapters]
    if indexes != sorted(indexes):
        report.errors.append("i capitoli non sono in ordine di index")

    for chapter in pack.chapters:
        if chapter.pageEnd > pack.book.sourcePages:
            report.errors.append(
                f"{chapter.id}: pageEnd {chapter.pageEnd} oltre le pagine del libro "
                f"({pack.book.sourcePages})"
            )

    chapter_ids = {chapter.id for chapter in pack.chapters}
    for entry in pack.glossary or []:
        if entry.chapterId and entry.chapterId not in chapter_ids:
            report.errors.append(
                f"glossario: '{entry.term}' rimanda al capitolo inesistente {entry.chapterId}"
            )

    _check_mindmap(pack.overview.mindmap, "overview", report, BOOK_MINDMAP_NODES_HARD, 60)
    return report


def validate_data(data: object) -> tuple[BookPack | None, Report]:
    """Valida dati grezzi contro schema e vincoli."""
    report = Report()
    try:
        pack = BookPack.model_validate(data)
    except ValidationError as exc:
        for error in exc.errors():
            location = ".".join(str(part) for part in error["loc"]) or "(radice)"
            report.errors.append(f"{location}: {error['msg']}")
        return None, report
    report.extend(check_pack(pack))
    return pack, report


__all__ = ["MAX_CARDS", "Report", "check_chapter", "check_pack", "mindmap_stats", "validate_data"]
