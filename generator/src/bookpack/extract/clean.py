"""Pulizia del testo: header e footer ripetuti, numeri di pagina, sillabazione, spazi."""

import re
from collections import Counter

from .pdf import Page

# Quante righe in cima e in fondo alla pagina possono essere header o footer
EDGE_LINES = 3
MIN_REPEATS = 3

_PAGE_NUMBER = re.compile(
    r"^[\W_]*(?:p\.?|pag\.?|pagina|page)?\s*(?:\d{1,4}|[ivxlc]{1,7})[\W_]*$", re.I
)
_CHAPTER_LABEL = re.compile(r"^(?:capitolo|chapter|parte|part)\s+\S+$", re.I)
_HYPHEN_BREAK = re.compile(r"(\w)-\n(?=[a-zà-ÿ])")
_TRAILING_HYPHEN = re.compile(r"(\w)-$")
_FIRST_WORD = re.compile(r"^([a-zà-ÿ][\w'’]*[.,;:!?]?)\s*")


def _normalize(line: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\d+", "#", line)).strip().lower()


def _edge_indexes(count: int) -> set[int]:
    return {*range(min(EDGE_LINES, count)), *range(max(count - EDGE_LINES, 0), count)}


def find_repeated_lines(pages: list[list[str]], min_repeats: int = MIN_REPEATS) -> set[str]:
    """Righe che compaiono ai bordi di più pagine, a meno dei numeri."""
    counts: Counter[str] = Counter()
    for lines in pages:
        keys = {_normalize(lines[i]) for i in _edge_indexes(len(lines))}
        counts.update(keys)
    return {
        key
        for key, count in counts.items()
        if count >= min_repeats and key and not _CHAPTER_LABEL.match(key)
    }


def _clean_text(text: str) -> str:
    text = text.replace("­", "")
    text = _HYPHEN_BREAK.sub(r"\1", text)
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _join_across_pages(texts: list[str]) -> None:
    """Ricompone le parole spezzate tra una pagina e la successiva."""
    for i in range(len(texts) - 1):
        if not _TRAILING_HYPHEN.search(texts[i]):
            continue
        match = _FIRST_WORD.match(texts[i + 1])
        if match:
            texts[i] = texts[i][:-1] + match.group(1)
            texts[i + 1] = texts[i + 1][match.end() :]


def clean_pages(pages: list[Page]) -> dict[int, str]:
    """Restituisce il testo pulito per numero di pagina."""
    raw = [[line.text for line in page.lines] for page in pages]
    repeated = find_repeated_lines(raw)

    def is_furniture(text: str) -> bool:
        return _normalize(text) in repeated or bool(_PAGE_NUMBER.match(text))

    texts: list[str] = []
    for page in pages:
        # Si consuma dai bordi riga per riga: un numero di pagina può stare sotto l'header
        lines = page.lines
        start, end = 0, len(lines)
        while start < end and is_furniture(lines[start].text):
            start += 1
        while end > start and is_furniture(lines[end - 1].text):
            end -= 1
        parts: list[str] = []
        for line in lines[start:end]:
            parts.append(line.text)
            parts.append("\n\n" if line.block_end else "\n")
        texts.append(_clean_text("".join(parts)))

    _join_across_pages(texts)
    return {page.number: text for page, text in zip(pages, texts, strict=True)}
