"""Testo dei capitoli con i marcatori di pagina e divisione in chunk con overlap."""

from dataclasses import dataclass

from ..extract.toc import Section

CHUNK_TOKENS = 3_500
OVERLAP_TOKENS = 200
CHARS_PER_TOKEN = 4
# Una parte di capitolo: abbastanza piccola da essere coperta tutta, senza saltare sezioni
PART_TOKENS = 5_000
# Un'ultima parte più piccola di così si unisce alla precedente
MIN_LAST_PART_SHARE = 0.25
# Spazio proporzionale: una card densa ogni tot parole del libro
WORDS_PER_CARD = 500
MIN_CARDS_PER_CHAPTER = 3
MIN_CARDS_PER_PART = 2


def estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def section_text(section: Section, pages: dict[int, str]) -> str:
    parts = []
    for number in range(section.page_start, section.page_end + 1):
        text = pages.get(number, "").strip()
        if text:
            parts.append(f"[p. {number}]\n{text}")
    return "\n\n".join(parts)


def word_count(section: Section, pages: dict[int, str]) -> int:
    return sum(
        len(pages.get(number, "").split())
        for number in range(section.page_start, section.page_end + 1)
    )


@dataclass
class Chunk:
    text: str
    first_page: int


def _split_long(text: str, limit: int) -> list[str]:
    """Divide per paragrafi, e per righe se un paragrafo supera da solo il limite."""
    pieces: list[str] = []
    for paragraph in text.split("\n\n"):
        if len(paragraph) <= limit:
            pieces.append(paragraph)
            continue
        current = ""
        for line in paragraph.split("\n"):
            if current and len(current) + len(line) > limit:
                pieces.append(current)
                current = ""
            current = f"{current}\n{line}" if current else line
        pieces.append(current)
    return pieces


def chunk_section(
    section: Section,
    pages: dict[int, str],
    chunk_tokens: int = CHUNK_TOKENS,
    overlap_tokens: int = OVERLAP_TOKENS,
) -> list[str]:
    """Chunk di circa `chunk_tokens` con overlap. Ogni chunk apre con il marcatore della sua pagina."""
    limit = chunk_tokens * CHARS_PER_TOKEN
    overlap = overlap_tokens * CHARS_PER_TOKEN

    # Coppie (pagina, pezzo di testo) in ordine
    pieces: list[tuple[int, str]] = []
    for number in range(section.page_start, section.page_end + 1):
        text = pages.get(number, "").strip()
        if text:
            pieces.extend((number, piece) for piece in _split_long(text, limit))

    chunks: list[str] = []
    current: list[tuple[int, str]] = []
    size = 0
    for number, piece in pieces:
        if current and size + len(piece) > limit:
            chunks.append(_render(current))
            kept: list[tuple[int, str]] = []
            kept_size = 0
            for item in reversed(current):
                if kept_size + len(item[1]) > overlap:
                    break
                kept.insert(0, item)
                kept_size += len(item[1])
            current, size = kept, kept_size
        current.append((number, piece))
        size += len(piece)
    if current:
        chunks.append(_render(current))
    return chunks


def _render(items: list[tuple[int, str]]) -> str:
    parts: list[str] = []
    page = None
    for number, piece in items:
        if number != page:
            parts.append(f"[p. {number}]")
            page = number
        parts.append(piece)
    return "\n\n".join(parts)


def split_parts(section: Section, pages: dict[int, str], context_tokens: int) -> list[str]:
    """Divide un capitolo nelle parti da condensare una alla volta."""
    size = min(PART_TOKENS, context_tokens)
    parts = chunk_section(section, pages, chunk_tokens=size, overlap_tokens=0)
    if len(parts) > 1 and estimate_tokens(parts[-1]) < size * MIN_LAST_PART_SHARE:
        last = parts.pop()
        parts[-1] = f"{parts[-1]}\n\n{last}"
    return parts


def card_target(text: str, multiple_parts: bool) -> int:
    """Quante card merita una parte, in proporzione alla sua lunghezza."""
    words = len(text.split())
    minimum = MIN_CARDS_PER_PART if multiple_parts else MIN_CARDS_PER_CHAPTER
    return max(minimum, round(words / WORDS_PER_CARD))
