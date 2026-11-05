"""Livello libro: overview, idee portanti, mindmap globale e glossario, dalle sintesi dei capitoli."""

import re

from pydantic import BaseModel

from ..llm.structured import StructuredLLM
from ..models import MAX_KEY_IDEAS, MIN_KEY_IDEAS, Chapter, GlossaryEntry, Overview
from .prompts import render


class GlossaryDraft(BaseModel):
    term: str
    definition: str
    chapterId: str | None


class BookDraft(BaseModel):
    summary: str
    keyIdeas: list[str]
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
) -> tuple[Overview, list[GlossaryEntry] | None]:
    user = render(
        "book",
        book_title=book_title,
        author_clause=f" by {author}" if author else "",
        lang=lang,
        chapters="\n\n".join(chapter_digest(chapter) for chapter in chapters),
    )
    draft, _ = llm.generate(
        render("book_system"), user, BookDraft, lambda parsed: _check(parsed, chapters)
    )
    overview = Overview(summary=draft.summary, keyIdeas=draft.keyIdeas, mindmap=draft.mindmap)
    glossary = [GlossaryEntry(**entry.model_dump()) for entry in draft.glossary]
    return overview, glossary or None
