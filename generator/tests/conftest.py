from pathlib import Path

import pymupdf
import pytest

LOREM = (
    "Il metodo funziona perché separa le decisioni dall'esecuzione. Ogni passaggio riduce il "
    "rischio di errore e rende il lavoro verificabile da chiunque. Questo principio vale per le "
    "piccole squadre come per le grandi organizzazioni. Quando il processo è esplicito diventa "
    "più semplice migliorarlo nel tempo e insegnarlo a chi arriva dopo. "
)

CATALOG = {
    "data": [
        {
            "id": "test/buono",
            "name": "Modello Buono",
            "context_length": 1_000_000,
            "pricing": {"prompt": "0.000002", "completion": "0.00001"},
            "top_provider": {"max_completion_tokens": 8000},
            "supported_parameters": ["max_tokens", "response_format", "structured_outputs"],
            "architecture": {"output_modalities": ["text"]},
            "reasoning": {"supported_efforts": ["high", "low", "none"]},
        },
        {
            "id": "test/piccolo",
            "name": "Piccolo",
            "context_length": 10_000,
            "pricing": {"prompt": "0", "completion": "0"},
            "top_provider": {"max_completion_tokens": None},
            "supported_parameters": ["max_tokens"],
            "architecture": {"output_modalities": ["text"]},
        },
        {
            "id": "test/immagini",
            "name": "Solo immagini",
            "context_length": 1000,
            "pricing": {"prompt": "0.1", "completion": "0.1"},
            "architecture": {"output_modalities": ["image"]},
        },
        {
            "id": "openrouter/auto",
            "name": "Auto",
            "context_length": 2_000_000,
            "pricing": {"prompt": "-1", "completion": "-1"},
            "architecture": {"output_modalities": ["text"]},
        },
    ]
}


@pytest.fixture(autouse=True)
def isolated_environment(tmp_path, monkeypatch):
    """I test non leggono il .env di chi li lancia e non escono su internet."""
    monkeypatch.setattr("bookpack.config.load_dotenv", lambda *_, **__: False)
    monkeypatch.setattr("bookpack.llm.catalog._fetch", lambda: CATALOG)
    monkeypatch.setenv("BOOKPACK_CACHE_DIR", str(tmp_path / "isolated-cache"))
    monkeypatch.setenv("BOOKPACK_MODEL", "test/buono")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("BOOKPACK_CONTEXT_TOKENS", raising=False)


def _add_body_page(doc: pymupdf.Document, header: str | None = "MANUALE DI PROVA") -> None:
    page = doc.new_page()
    number = doc.page_count
    if header:
        page.insert_text((72, 40), header, fontsize=8)
    page.insert_textbox(pymupdf.Rect(72, 80, 520, 740), LOREM * 4, fontsize=11)
    page.insert_text((300, 800), str(number), fontsize=8)


def _make_book(path: Path, *, outline: bool) -> Path:
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 200), "Manuale di prova", fontsize=26)
    doc.new_page().insert_text((72, 100), "Copyright 2024", fontsize=11)

    toc = [[1, "Copyright", 2]]
    for chapter in range(1, 5):
        page = doc.new_page()
        page.insert_text((72, 120), f"Capitolo {chapter}", fontsize=20)
        page.insert_textbox(pymupdf.Rect(72, 160, 520, 740), LOREM * 3, fontsize=11)
        toc.append([1, f"Capitolo {chapter}: tema {chapter}", doc.page_count])
        for _ in range(3):
            _add_body_page(doc)
    page = doc.new_page()
    page.insert_text((72, 120), "Bibliografia", fontsize=20)
    page.insert_textbox(pymupdf.Rect(72, 160, 520, 740), "Autore, Titolo, 2001.", fontsize=11)
    toc.append([1, "Bibliografia", doc.page_count])

    if outline:
        doc.set_toc(toc)
    doc.set_metadata({"title": "Manuale di prova", "author": "Ada Autrice"})
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def pdf_with_outline(tmp_path: Path) -> Path:
    return _make_book(tmp_path / "con-outline.pdf", outline=True)


@pytest.fixture
def pdf_without_outline(tmp_path: Path) -> Path:
    return _make_book(tmp_path / "senza-outline.pdf", outline=False)


@pytest.fixture
def valid_pack() -> dict:
    def card(i: int, kind: str = "concept") -> dict:
        data = {"id": f"ch-01-c{i:02d}", "type": kind, "body": "Un'idea breve e chiara."}
        if kind != "takeaway":
            data["page"] = 2
        return data

    return {
        "schemaVersion": 1,
        "generator": {"version": "0.1.0", "model": "test", "generatedAt": "2026-01-01T00:00:00Z"},
        "book": {"id": "libro", "title": "Libro", "lang": "it", "sourcePages": 10},
        "overview": {
            "summary": "Riassunto.",
            "keyIdeas": ["Uno", "Due", "Tre"],
            "mindmap": "# Libro\n## Capitolo",
        },
        "chapters": [
            {
                "id": "ch-01",
                "index": 1,
                "title": "Capitolo",
                "pageStart": 1,
                "pageEnd": 5,
                "estMinutes": 5,
                "tldr": "In breve.",
                "cards": [*(card(i) for i in range(1, 5)), card(5, "takeaway")],
                "mindmap": "# Capitolo\n## Ramo\n- Foglia",
                "flashcards": [
                    {"id": f"ch-01-f{i:02d}", "q": "Domanda?", "a": "Risposta.", "page": 2}
                    for i in range(1, 4)
                ],
            }
        ],
    }
