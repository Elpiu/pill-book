"""Modelli del book pack: fonte di verità del formato.

Lo schema JSON in `schema/bookpack.schema.json` è generato da qui con `bookpack schema`.
Se il formato cambia in modo incompatibile va incrementato `SCHEMA_VERSION`.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = 1

MIN_CARDS = 5
MAX_CARDS = 12
MIN_FLASHCARDS = 3
MAX_FLASHCARDS = 5
MIN_KEY_IDEAS = 3
MAX_KEY_IDEAS = 7

CHAPTER_ID_PATTERN = r"^ch-\d{2,}$"
CARD_ID_PATTERN = r"^ch-\d{2,}-c\d{2,}$"
FLASHCARD_ID_PATTERN = r"^ch-\d{2,}-f\d{2,}$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CardType(StrEnum):
    CONCEPT = "concept"
    DEFINITION = "definition"
    EXAMPLE = "example"
    QUOTE = "quote"
    TAKEAWAY = "takeaway"


class GeneratorInfo(_Strict):
    version: str
    model: str
    generatedAt: str = Field(description="Data di generazione, ISO-8601")


class Book(_Strict):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$", description="Slug stabile del libro")
    title: str = Field(min_length=1)
    author: str | None = None
    lang: str = Field(min_length=2, description="Lingua di output, codice ISO 639-1")
    sourcePages: int = Field(ge=1)
    coverColor: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")


class Overview(_Strict):
    summary: str = Field(min_length=1, description="5-8 frasi sul libro intero")
    keyIdeas: list[str] = Field(min_length=MIN_KEY_IDEAS, max_length=MAX_KEY_IDEAS)
    mindmap: str = Field(min_length=1, description="Markdown gerarchico per markmap")


class Card(_Strict):
    id: str = Field(pattern=CARD_ID_PATTERN)
    type: CardType
    title: str | None = None
    body: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1, description="Pagina del PDF, a partire da 1")


class Flashcard(_Strict):
    id: str = Field(pattern=FLASHCARD_ID_PATTERN)
    q: str = Field(min_length=1)
    a: str = Field(min_length=1)
    page: int = Field(ge=1)


class Chapter(_Strict):
    id: str = Field(pattern=CHAPTER_ID_PATTERN)
    index: int = Field(ge=1)
    title: str = Field(min_length=1)
    pageStart: int = Field(ge=1)
    pageEnd: int = Field(ge=1)
    estMinutes: int = Field(ge=1)
    tldr: str = Field(min_length=1)
    cards: list[Card] = Field(min_length=MIN_CARDS, max_length=MAX_CARDS)
    mindmap: str = Field(min_length=1)
    flashcards: list[Flashcard] = Field(min_length=MIN_FLASHCARDS, max_length=MAX_FLASHCARDS)


class GlossaryEntry(_Strict):
    term: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    chapterId: str | None = Field(default=None, pattern=CHAPTER_ID_PATTERN)


class BookPack(_Strict):
    schemaVersion: Literal[1]
    generator: GeneratorInfo
    book: Book
    overview: Overview
    chapters: list[Chapter] = Field(min_length=1)
    glossary: list[GlossaryEntry] | None = None


def export_schema() -> dict:
    schema = BookPack.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = f"https://bookpack.local/schema/v{SCHEMA_VERSION}/bookpack.schema.json"
    return schema
