"""Livello libro: overview, idee portanti, mindmap globale e glossario, dalle sintesi dei capitoli."""

import re

from pydantic import BaseModel

from ..llm.structured import StructuredLLM
from ..models import MAX_KEY_IDEAS, MIN_KEY_IDEAS, Chapter, GlossaryEntry, Overview
from .chapter import translated_title
from .prompts import render


class GlossaryDraft(BaseModel):
    term: str
    definition: str
    chapterId: str | None


class BookDraft(BaseModel):
    summary: str
    keyIdeas: list[str]
    # Dopo il testo, nella stessa lingua; prima della mindmap, che lo usa come radice
    title: str
    mindmap: str
    glossary: list[GlossaryDraft]


def chapter_digest(chapter: Chapter) -> str:
    return "\n".join(
        [f"### {chapter.id} | {chapter.title}", f"In brief: {chapter.tldr}", chapter.summary]
    )


def _check(draft: BookDraft, chapters: list[Chapter]) -> None:
    errors = []
    if not MIN_KEY_IDEAS <= len(draft.keyIdeas) <= MAX_KEY_IDEAS:
        errors.append(f"keyIdeas has {len(draft.keyIdeas)} items, expected 3 to 7")
    # L'app usa questi nodi per aprire il capitolo toccandolo nella mindmap globale
    headings = re.findall(r"^##\s+(.+?)\s*$", draft.mindmap, re.M)
    missing = [chapter.title for chapter in chapters if chapter.title not in headings]
    if missing:
        errors.append(
            "mindmap needs a '##' heading with exactly these titles: " + "; ".join(missing)
        )
    known = {chapter.id for chapter in chapters}
    for entry in draft.glossary:
        if entry.chapterId and entry.chapterId not in known:
            errors.append(
                f"glossary term '{entry.term}' refers to unknown chapter {entry.chapterId}"
            )
    if errors:
        raise ValueError("\n".join(f"- {error}" for error in errors))


def condense_book(
    llm: StructuredLLM,
    chapters: list[Chapter],
    book_title: str,
    author: str | None,
    lang: str,
) -> tuple[str, Overview, list[GlossaryEntry] | None]:
    """Restituisce anche il titolo del libro nella lingua del pack."""
    user = render(
        "book",
        book_title=book_title,
        author_clause=f" by {author}" if author else "",
        lang=lang,
        chapters="\n\n".join(chapter_digest(chapter) for chapter in chapters),
    )

    def convert(parsed: BookDraft) -> str:
        _check(parsed, chapters)
        return translated_title(parsed.title, book_title)

    draft, title = llm.generate(render("book_system"), user, BookDraft, convert)
    overview = Overview(summary=draft.summary, keyIdeas=draft.keyIdeas, mindmap=draft.mindmap)
    glossary = [GlossaryEntry(**entry.model_dump()) for entry in draft.glossary]
    assert isinstance(title, str)
    return title, overview, glossary or None
