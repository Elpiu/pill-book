"""Pipeline per capitolo: card parte per parte, poi riassunto e flashcard ricavati dalle card."""

import re
from dataclasses import dataclass
from math import ceil, floor

from pydantic import BaseModel

from ..extract.toc import Section
from ..llm.structured import StructuredLLM
from ..models import Card, CardType, Chapter, Flashcard
from ..validate import check_card, check_chapter, word_count
from .chunking import card_target, split_parts
from .prompts import render

WORDS_PER_MINUTE = 200
SECONDS_PER_QUESTION = 20
MINDMAP_MINUTES = 0.5
# Tolleranza sul numero di card: il modello non può centrare un numero esatto
TARGET_LOW_SHARE = 0.7
TARGET_HIGH_SHARE = 1.4
CARDS_PER_CHECK = 4
CARDS_PER_FLASHCARD = 4
MAX_TARGET_FLASHCARDS = 15
MIN_FLASHCARDS = 3
SUMMARY_SHARE = 1 / 6  # parole del riassunto rispetto a quelle delle card
MIN_SUMMARY_WORDS = 120
MAX_SUMMARY_WORDS = 500
SUMMARY_LOW_SHARE = 0.4
SUMMARY_HIGH_SHARE = 1.8
PART_CARD_TYPES = {
    CardType.CONCEPT,
    CardType.DEFINITION,
    CardType.EXAMPLE,
    CardType.PROCEDURE,
    CardType.QUOTE,
    CardType.CHECK,
}


class PartCard(BaseModel):
    type: CardType
    title: str | None
    body: str
    details: str | None
    steps: list[str] | None
    code: str | None
    answer: str | None
    page: int


class PartDraft(BaseModel):
    title: str
    intro: str
    cards: list[PartCard]


class FlashcardDraft(BaseModel):
    q: str
    a: str
    page: int


class ChapterWrap(BaseModel):
    tldr: str
    summary: str
    takeaway: str
    mindmap: str
    flashcards: list[FlashcardDraft]


@dataclass
class DonePart:
    text: str
    draft: PartDraft
    notes: list[str]


def chapter_id(index: int) -> str:
    return f"ch-{index:02d}"


def _words_of(card: Card) -> int:
    parts = [card.body, card.details, card.code, card.answer, *(card.steps or [])]
    return sum(word_count(part) for part in parts if part)


def estimate_minutes(cards: list[Card], flashcards: list[Flashcard], summary: str) -> int:
    words = sum(_words_of(card) for card in cards) + word_count(summary)
    questions = len(flashcards) + sum(card.type == CardType.CHECK for card in cards)
    minutes = words / WORDS_PER_MINUTE + questions * SECONDS_PER_QUESTION / 60
    return max(1, ceil(minutes + MINDMAP_MINUTES))


def _normalized(text: str) -> str:
    return re.sub(r"\W+", "", text.lower())


def _check_part(draft: PartDraft, section: Section, ident: str, low: int, high: int) -> None:
    """Solleva ValueError con gli errori da far correggere al modello."""
    errors: list[str] = []
    wrong = {card.type.value for card in draft.cards} - {t.value for t in PART_CARD_TYPES}
    if wrong:
        errors.append(f"card types not allowed in a part: {', '.join(sorted(wrong))}")
    content = [card for card in draft.cards if card.type != CardType.CHECK]
    if not low <= len(content) <= high:
        errors.append(f"{len(content)} content cards, expected between {low} and {high}")
    checks = len(draft.cards) - len(content)
    if len(content) >= CARDS_PER_CHECK - 1 and not checks:
        errors.append("add at least one check question")
    quotes = sum(card.type == CardType.QUOTE for card in draft.cards)
    if quotes > 1:
        errors.append(f"{quotes} quote cards, at most 1 per part")
    if word_count(draft.title) > 12:
        errors.append("the part title is too long")
    for number, card in enumerate(draft.cards, start=1):
        built = Card(id=f"{ident}-c{number:02d}", **card.model_dump())
        report = check_card(built, section.page_start, section.page_end)
        errors.extend(report.errors)
    if errors:
        raise ValueError("\n".join(f"- {error}" for error in errors))


def condense_part(
    llm: StructuredLLM,
    text: str,
    number: int,
    total: int,
    section: Section,
    index: int,
    book_title: str,
    lang: str,
) -> DonePart:
    """Dipende solo dal testo della parte, quindi si può eseguire insieme alle altre."""
    ident = chapter_id(index)
    system = render("rules", lang=lang)
    target = card_target(text, total > 1)
    low = max(1, floor(target * TARGET_LOW_SHARE))
    high = ceil(target * TARGET_HIGH_SHARE) + 1
    user = render(
        "part",
        book_title=book_title,
        chapter_title=section.title,
        part=str(number),
        parts=str(total),
        words=str(len(text.split())),
        target=str(target),
        low=str(low),
        high=str(high),
        checks=str(max(1, round(target / CARDS_PER_CHECK))),
        page_start=str(section.page_start),
        page_end=str(section.page_end),
        text=text,
    )
    draft, _ = llm.generate(
        system, user, PartDraft, lambda parsed: _check_part(parsed, section, ident, low, high)
    )
    # Una citazione non presente nel testo non si conserva: la fedeltà conta più della card
    source = _normalized(text)
    notes: list[str] = []
    kept = []
    for card in draft.cards:
        if card.type == CardType.QUOTE and _normalized(card.body) not in source:
            notes.append(f"{ident}: citazione non trovata nel testo, scartata")
            continue
        kept.append(card)
    draft.cards = kept
    return DonePart(text, draft, notes)


def _card_digest(card: Card) -> str | None:
    if card.type in (CardType.CHECK, CardType.SECTION, CardType.QUOTE):
        return None
    label = f"{card.title}: " if card.title else ""
    extra = "".join(f" {part}" for part in [card.details, *(card.steps or [])] if part)
    return f"- (p. {card.page}) [{card.type.value}] {label}{card.body}{extra}"


def _to_chapter(
    wrap: ChapterWrap,
    cards: list[Card],
    section: Section,
    index: int,
    ident: str,
    summary_target: int,
) -> Chapter:
    """Applica i vincoli al capitolo completo. Solleva ValueError per ottenere un nuovo tentativo."""
    low = SUMMARY_LOW_SHARE * summary_target
    high = SUMMARY_HIGH_SHARE * summary_target
    if not low <= word_count(wrap.summary) <= high:
        raise ValueError(
            f"- the summary has {word_count(wrap.summary)} words, write about {summary_target}"
        )
    takeaway = Card(id=f"{ident}-c{len(cards) + 1:02d}", type=CardType.TAKEAWAY, body=wrap.takeaway)
    flashcards = [
        Flashcard(id=f"{ident}-f{i:02d}", **card.model_dump())
        for i, card in enumerate(wrap.flashcards, start=1)
    ]
    all_cards = [*cards, takeaway]
    chapter = Chapter(
        id=ident,
        index=index,
        title=section.title,
        pageStart=section.page_start,
        pageEnd=section.page_end,
        estMinutes=estimate_minutes(all_cards, flashcards, wrap.summary),
        tldr=wrap.tldr,
        summary=wrap.summary,
        cards=all_cards,
        mindmap=wrap.mindmap,
        flashcards=flashcards,
    )
    report = check_chapter(chapter)
    if not report.ok:
        raise ValueError("\n".join(f"- {error}" for error in report.errors))
    return chapter


def _first_page(text: str, section: Section) -> int:
    match = re.search(r"\[p\. (\d+)\]", text)
    return int(match.group(1)) if match else section.page_start


def wrap_chapter(
    llm: StructuredLLM,
    parts: list[DonePart],
    section: Section,
    index: int,
    book_title: str,
    lang: str,
) -> Chapter:
    """Unisce le parti, nell'ordine del libro, e scrive riassunto e flashcard dalle card."""
    system = render("rules", lang=lang)
    ident = chapter_id(index)

    cards: list[Card] = []

    def add_card(**fields: object) -> None:
        cards.append(Card(id=f"{ident}-c{len(cards) + 1:02d}", **fields))

    for part in parts:
        if len(parts) > 1:
            add_card(
                type=CardType.SECTION,
                title=part.draft.title,
                body=part.draft.intro,
                page=_first_page(part.text, section),
            )
        for card in part.draft.cards:
            add_card(**card.model_dump())

    digest = "\n".join(line for line in map(_card_digest, cards) if line)
    content = sum(card.type not in (CardType.CHECK, CardType.SECTION) for card in cards)
    card_words = sum(_words_of(card) for card in cards)
    summary_target = min(
        MAX_SUMMARY_WORDS, max(MIN_SUMMARY_WORDS, round(card_words * SUMMARY_SHARE))
    )
    flashcards = min(
        MAX_TARGET_FLASHCARDS, max(MIN_FLASHCARDS, round(content / CARDS_PER_FLASHCARD))
    )
    user = render(
        "chapter_wrap",
        book_title=book_title,
        chapter_title=section.title,
        page_start=str(section.page_start),
        page_end=str(section.page_end),
        summary_words=str(summary_target),
        mindmap_nodes=str(min(40, 15 + content)),
        flashcards=str(flashcards),
        cards=digest,
    )
    _, chapter = llm.generate(
        system,
        user,
        ChapterWrap,
        lambda wrap: _to_chapter(wrap, cards, section, index, ident, summary_target),
    )
    assert isinstance(chapter, Chapter)
    return chapter


def condense_chapter(
    llm: StructuredLLM,
    section: Section,
    index: int,
    pages: dict[int, str],
    book_title: str,
    lang: str,
    context_tokens: int,
    notes: list[str] | None = None,
) -> Chapter:
    """Un capitolo solo, una chiamata alla volta."""
    texts = split_parts(section, pages, context_tokens)
    parts = [
        condense_part(llm, text, number, len(texts), section, index, book_title, lang)
        for number, text in enumerate(texts, start=1)
    ]
    if notes is not None:
        notes.extend(note for part in parts for note in part.notes)
    return wrap_chapter(llm, parts, section, index, book_title, lang)
