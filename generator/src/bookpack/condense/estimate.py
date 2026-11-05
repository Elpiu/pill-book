"""Stima di chiamate, token e costo di un build, prima di spendere."""

from dataclasses import dataclass

from ..extract.toc import Section
from .chunking import card_target, estimate_tokens, split_parts

PROMPT_OVERHEAD_TOKENS = 1_000
# Output per card e per il riassunto del capitolo, compreso il ragionamento del modello.
# Misurati su un capitolo reale di 76 pagine: il ragionamento vale più del testo della risposta.
CARD_OUTPUT_TOKENS = 900
WRAP_OUTPUT_TOKENS = 5_000
# Le card di un capitolo tornano in input per scrivere riassunto e flashcard
CARD_INPUT_TOKENS = 180
BOOK_INPUT_TOKENS_PER_CHAPTER = 500
BOOK_OUTPUT_TOKENS = 3_000


@dataclass
class Estimate:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float | None = None


def estimate_section(section: Section, pages: dict[int, str], context_tokens: int) -> Estimate:
    parts = split_parts(section, pages, context_tokens)
    cards = sum(card_target(part, len(parts) > 1) for part in parts)
    input_tokens = (
        sum(estimate_tokens(part) for part in parts)
        + PROMPT_OVERHEAD_TOKENS * (len(parts) + 1)
        + cards * CARD_INPUT_TOKENS
    )
    output_tokens = cards * CARD_OUTPUT_TOKENS + WRAP_OUTPUT_TOKENS
    return Estimate(len(parts) + 1, input_tokens, output_tokens)


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
