"""Stima di chiamate, token e costo di un build, prima di spendere."""

from dataclasses import dataclass

from ..extract.toc import Section
from .chunking import chunk_section, estimate_tokens, section_text

PROMPT_OVERHEAD_TOKENS = 700
# Output per chiamata, compreso il ragionamento del modello
CHAPTER_OUTPUT_TOKENS = 4_000
NOTES_OUTPUT_TOKENS = 1_200
BOOK_INPUT_TOKENS_PER_CHAPTER = 500
BOOK_OUTPUT_TOKENS = 3_000


@dataclass
class Estimate:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float | None = None


def estimate_section(section: Section, pages: dict[int, str], context_tokens: int) -> Estimate:
    tokens = estimate_tokens(section_text(section, pages))
    if tokens <= context_tokens:
        return Estimate(1, tokens + PROMPT_OVERHEAD_TOKENS, CHAPTER_OUTPUT_TOKENS)
    chunks = chunk_section(section, pages)
    notes_output = NOTES_OUTPUT_TOKENS * len(chunks)
    input_tokens = (
        sum(estimate_tokens(chunk) for chunk in chunks)
        + PROMPT_OVERHEAD_TOKENS * (len(chunks) + 1)
        + notes_output
    )
    return Estimate(len(chunks) + 1, input_tokens, notes_output + CHAPTER_OUTPUT_TOKENS)


def estimate_build(
    sections: list[Section],
    pages: dict[int, str],
    prices: tuple[float, float] | None,
    context_tokens: int,
) -> Estimate:
    """`prices` è (input, output) in dollari per milione di token: None se non si conoscono."""
    total = Estimate()
    for section in sections:
        part = estimate_section(section, pages, context_tokens)
        total.calls += part.calls
        total.input_tokens += part.input_tokens
        total.output_tokens += part.output_tokens
    total.calls += 1
    total.input_tokens += BOOK_INPUT_TOKENS_PER_CHAPTER * len(sections) + PROMPT_OVERHEAD_TOKENS
    total.output_tokens += BOOK_OUTPUT_TOKENS
    if prices:
        price_in, price_out = prices
        total.cost = (total.input_tokens * price_in + total.output_tokens * price_out) / 1_000_000
    return total
