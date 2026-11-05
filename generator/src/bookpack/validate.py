"""Vincoli del pack oltre lo schema: lunghezze, unicità, coerenza di id e pagine.

Alcuni limiti sono indicativi: oltre quello nominale si produce un avviso, oltre la tolleranza un
errore. Per le citazioni il limite è rigido.
"""

import re
from dataclasses import dataclass, field

from pydantic import ValidationError

from .models import BookPack, Card, CardType, Chapter, Flashcard

BODY_WORDS_SOFT = 60
BODY_WORDS_HARD = 80
DETAILS_WORDS_SOFT = 130
DETAILS_WORDS_HARD = 180
TITLE_WORDS_SOFT = 8
TITLE_WORDS_HARD = 12
QUOTE_WORDS_MAX = 25
ANSWER_WORDS_HARD = 90
STEP_WORDS_HARD = 40
MIN_STEPS = 2
MAX_STEPS = 12
CODE_LINES_HARD = 30
# Una citazione ogni quattro card al massimo, e sempre almeno una ammessa
CARDS_PER_QUOTE = 4
SUMMARY_WORDS_MIN = 40
SUMMARY_WORDS_MAX = 900
MINDMAP_MAX_DEPTH = 4
MINDMAP_NODES_SOFT = 40
MINDMAP_NODES_HARD = 90
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


def _check_length(text: str, label: str, soft: int, hard: int, where: str, report: Report) -> None:
    words = word_count(text)
    if words > hard:
        report.errors.append(f"{where}: {label} di {words} parole (massimo circa {soft})")
    elif words > soft:
        report.warnings.append(f"{where}: {label} di {words} parole (consigliate {soft})")


def check_card(card: Card, page_start: int, page_end: int) -> Report:
    report = Report()
    where = card.id

    if card.type == CardType.QUOTE:
        words = word_count(card.body)
        if words > QUOTE_WORDS_MAX:
            report.errors.append(
                f"{where}: citazione di {words} parole (massimo {QUOTE_WORDS_MAX})"
            )
    else:
        _check_length(card.body, "body", BODY_WORDS_SOFT, BODY_WORDS_HARD, where, report)

    if card.title:
        _check_length(card.title, "title", TITLE_WORDS_SOFT, TITLE_WORDS_HARD, where, report)
    if card.details:
        _check_length(
            card.details, "details", DETAILS_WORDS_SOFT, DETAILS_WORDS_HARD, where, report
        )

    if card.type == CardType.CHECK:
        if not card.answer:
            report.errors.append(f"{where}: una domanda deve avere la risposta in answer")
        elif word_count(card.answer) > ANSWER_WORDS_HARD:
            report.errors.append(f"{where}: risposta troppo lunga (massimo {ANSWER_WORDS_HARD})")
    elif card.answer:
        report.errors.append(f"{where}: answer è ammesso solo sulle card di tipo check")

    if card.type == CardType.PROCEDURE:
        steps = card.steps or []
        if not MIN_STEPS <= len(steps) <= MAX_STEPS:
            report.errors.append(
                f"{where}: una procedura ha da {MIN_STEPS} a {MAX_STEPS} passi, non {len(steps)}"
            )
        for number, step in enumerate(steps, start=1):
            if word_count(step) > STEP_WORDS_HARD:
                report.errors.append(
                    f"{where}: passo {number} troppo lungo (massimo {STEP_WORDS_HARD} parole)"
                )
    elif card.steps:
        report.errors.append(f"{where}: steps è ammesso solo sulle card di tipo procedure")

    if card.code and card.code.count("\n") + 1 > CODE_LINES_HARD:
        report.errors.append(f"{where}: codice troppo lungo (massimo {CODE_LINES_HARD} righe)")

    if card.type == CardType.SECTION and not card.title:
        report.errors.append(f"{where}: una sezione deve avere un titolo")

    if card.page is None:
        if card.type not in (CardType.TAKEAWAY, CardType.SECTION):
            report.errors.append(f"{where}: manca la pagina di origine")
    elif not page_start <= card.page <= page_end:
        report.errors.append(
            f"{where}: pagina {card.page} fuori dal capitolo ({page_start}-{page_end})"
        )
    return report


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
    allowed_quotes = max(1, len(chapter.cards) // CARDS_PER_QUOTE)
    if quotes > allowed_quotes:
        report.errors.append(f"{where}: {quotes} citazioni (massimo {allowed_quotes})")

    summary_words = word_count(chapter.summary)
    if not SUMMARY_WORDS_MIN <= summary_words <= SUMMARY_WORDS_MAX:
        report.errors.append(
            f"{where}: riassunto di {summary_words} parole "
            f"(da {SUMMARY_WORDS_MIN} a {SUMMARY_WORDS_MAX})"
        )

    for card in chapter.cards:
        if not card.id.startswith(f"{chapter.id}-"):
            report.errors.append(f"{card.id}: id non appartiene al capitolo {chapter.id}")
        report.extend(check_card(card, chapter.pageStart, chapter.pageEnd))
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


__all__ = ["Report", "check_card", "check_chapter", "check_pack", "mindmap_stats", "validate_data"]
