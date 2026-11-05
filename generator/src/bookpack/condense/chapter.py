"""Pipeline per capitolo: chiamata unica se entra nel budget, altrimenti map-reduce."""

from math import ceil

from pydantic import BaseModel

from ..extract.toc import Section
from ..llm.structured import StructuredLLM
from ..models import Card, CardType, Chapter, Flashcard
from ..validate import check_chapter, word_count
from .chunking import chunk_section, estimate_tokens, section_text
from .prompts import render

WORDS_PER_MINUTE = 200
SECONDS_PER_FLASHCARD = 20
MINDMAP_MINUTES = 0.5


class CardDraft(BaseModel):
    type: CardType
    title: str | None
    body: str
    page: int | None


class FlashcardDraft(BaseModel):
    q: str
    a: str
    page: int


class ChapterDraft(BaseModel):
    tldr: str
    cards: list[CardDraft]
    mindmap: str
    flashcards: list[FlashcardDraft]


class Note(BaseModel):
    text: str
    page: int


class ChunkNotes(BaseModel):
    notes: list[Note]


def chapter_id(index: int) -> str:
    return f"ch-{index:02d}"


def estimate_minutes(cards: list[Card], flashcards: list[Flashcard]) -> int:
    words = sum(word_count(card.body) for card in cards)
    minutes = words / WORDS_PER_MINUTE + len(flashcards) * SECONDS_PER_FLASHCARD / 60
    return max(1, ceil(minutes + MINDMAP_MINUTES))


def _to_chapter(draft: ChapterDraft, section: Section, index: int) -> Chapter:
    """Assegna gli id e applica i vincoli. Solleva ValueError per ottenere un nuovo tentativo."""
    ident = chapter_id(index)
    cards = [
        Card(id=f"{ident}-c{i:02d}", **card.model_dump())
        for i, card in enumerate(draft.cards, start=1)
    ]
    flashcards = [
        Flashcard(id=f"{ident}-f{i:02d}", **card.model_dump())
        for i, card in enumerate(draft.flashcards, start=1)
    ]
    chapter = Chapter(
        id=ident,
        index=index,
        title=section.title,
        pageStart=section.page_start,
        pageEnd=section.page_end,
        estMinutes=estimate_minutes(cards, flashcards),
        tldr=draft.tldr,
        cards=cards,
        mindmap=draft.mindmap,
        flashcards=flashcards,
    )
    report = check_chapter(chapter)
    if not report.ok:
        raise ValueError("\n".join(f"- {error}" for error in report.errors))
    return chapter


def condense_chapter(
    llm: StructuredLLM,
    section: Section,
    index: int,
    pages: dict[int, str],
    book_title: str,
    lang: str,
    context_tokens: int,
) -> Chapter:
    system = render("rules", lang=lang)
    shared = {
        "book_title": book_title,
        "chapter_title": section.title,
        "page_start": str(section.page_start),
        "page_end": str(section.page_end),
    }
    format_rules = render(
        "chapter_format", page_start=shared["page_start"], page_end=shared["page_end"]
    )

    text = section_text(section, pages)
    if estimate_tokens(text) <= context_tokens:
        user = render("chapter", format=format_rules, text=text, **shared)
    else:
        chunks = chunk_section(section, pages)
        notes: list[Note] = []
        for part, chunk in enumerate(chunks, start=1):
            prompt = render(
                "chunk_notes",
                part=str(part),
                parts=str(len(chunks)),
                book_title=book_title,
                chapter_title=section.title,
                text=chunk,
            )
            parsed, _ = llm.generate(system, prompt, ChunkNotes)
            notes.extend(parsed.notes)
        rendered = "\n".join(f"- (p. {note.page}) {note.text}" for note in notes)
        user = render("chapter_from_notes", format=format_rules, notes=rendered, **shared)

    _, chapter = llm.generate(
        system, user, ChapterDraft, lambda draft: _to_chapter(draft, section, index)
    )
    assert isinstance(chapter, Chapter)
    return chapter
