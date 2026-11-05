"""Provider finto, senza rete: compone l'output dal testo ricevuto.

Serve ai test e a provare la pipeline su un PDF senza spendere. I contenuti sono frasi estratte
meccanicamente dal capitolo, non una vera condensazione.
"""

import json
import re

from .base import LLMProvider, LLMResponse

_PAGE_MARK = re.compile(r"\[p\. (\d+)\]")
_CHAPTER_LINE = re.compile(r"^### (ch-\d+) \| (.+)$", re.M)
_SENTENCE = re.compile(r"[^.!?\n][^.!?]{30,}[.!?]")
_TARGET_CARDS = re.compile(r"Target: (\d+) content cards")
_SUMMARY_WORDS = re.compile(r"About (\d+) words")


def _sentences(text: str) -> list[tuple[str, int]]:
    """Frasi del testo con la pagina in cui si trovano."""
    result: list[tuple[str, int]] = []
    pieces = _PAGE_MARK.split(text)
    # re.split con un gruppo alterna testo e numeri di pagina
    for number, chunk in zip(pieces[1::2], pieces[2::2], strict=True):
        for match in _SENTENCE.finditer(chunk):
            sentence = " ".join(match.group(0).split())
            words = sentence.split()
            if len(words) > 40:
                sentence = " ".join(words[:40]) + "..."
            result.append((sentence, int(number)))
    return result


class FakeProvider(LLMProvider):
    name = "fake"

    def __init__(self, model: str = "fake-1", fail_first: int = 0) -> None:
        self.model = model
        self.fail_first = fail_first
        self.calls = 0

    def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
        self.calls += 1
        if self.calls <= self.fail_first:
            return LLMResponse(text='{"non": "valido"}', input_tokens=10, output_tokens=5)

        properties = schema.get("properties", {})
        if "intro" in properties:
            output = self._part(user)
        elif "takeaway" in properties:
            output = self._wrap(user)
        elif "keyIdeas" in properties:
            output = self._book(user)
        elif "chapters" in properties:
            output = {"chapters": self._detect(user)}
        else:
            output = {}
        text = json.dumps(output, ensure_ascii=False)
        return LLMResponse(text=text, input_tokens=len(user) // 4, output_tokens=len(text) // 4)

    def _part(self, user: str) -> dict:
        target = int(_TARGET_CARDS.search(user).group(1))
        found = _sentences(user) or [("Contenuto non disponibile per questa parte.", 1)]
        cards = []
        for i in range(target):
            text, page = found[i * len(found) // target]
            cards.append(
                {
                    "type": "concept",
                    "title": f"Idea {i + 1}",
                    "body": text,
                    "details": f"Spiegazione di prova: {text}",
                    "steps": None,
                    "code": None,
                    "answer": None,
                    "page": page,
                }
            )
            if (i + 1) % 4 == 3:
                cards.append(
                    {
                        "type": "check",
                        "title": None,
                        "body": f"Come spiegheresti l'idea {i + 1}?",
                        "details": None,
                        "steps": None,
                        "code": None,
                        "answer": text,
                        "page": page,
                    }
                )
        return {"title": "Parte di prova", "intro": "Introduzione di prova.", "cards": cards}

    def _wrap(self, user: str) -> dict:
        found = [
            (text, int(page))
            for page, text in re.findall(r"^- \(p\. (\d+)\) \[\w+\] (.+)$", user, re.M)
        ]
        target = int(_SUMMARY_WORDS.search(user).group(1))
        flashcards = [
            {"q": f"Qual è il punto {i}?", "a": " ".join(text.split()[:30]), "page": page}
            for i, (text, page) in enumerate(found[:5], start=1)
        ]
        while len(flashcards) < 3:
            flashcards.append(dict(flashcards[-1]))
        return {
            "tldr": "Sintesi di prova del capitolo.",
            "summary": " ".join(["Riassunto di prova del capitolo."] * (target // 5)),
            "takeaway": "Cosa portare via, di prova.",
            "mindmap": "# Capitolo\n" + "\n".join(f"## Idea {i}" for i in range(1, 4)),
            "flashcards": flashcards,
        }

    def _book(self, user: str) -> dict:
        chapters = _CHAPTER_LINE.findall(user)
        titles = [title for _, title in chapters]
        return {
            "summary": "Riassunto di prova generato senza LLM.",
            "keyIdeas": ["Idea portante di prova 1", "Idea portante di prova 2", "Idea di prova 3"],
            "mindmap": "# Libro\n" + "\n".join(f"## {title}" for title in titles),
            "glossary": [],
        }

    def _detect(self, user: str) -> list[dict]:
        return [{"title": f"Parte {i}", "page": i} for i in (1, 2, 3)]
