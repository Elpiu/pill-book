import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookpack.cache import ResponseCache
from bookpack.cli import app
from bookpack.condense.chapter import condense_chapter
from bookpack.condense.chunking import chunk_section, estimate_tokens
from bookpack.condense.estimate import estimate_section
from bookpack.condense.pipeline import build_pack
from bookpack.extract.clean import clean_pages
from bookpack.extract.pdf import open_pdf
from bookpack.extract.toc import Section, detect_chapters
from bookpack.llm.base import LLMError, LLMResponse, strict_schema
from bookpack.llm.fake import FakeProvider
from bookpack.llm.structured import StructuredLLM
from bookpack.models import Overview
from bookpack.validate import validate_data


def _build(pdf: Path, provider: FakeProvider, cache_dir: Path, **kwargs):
    doc = open_pdf(pdf)
    llm = StructuredLLM(provider, ResponseCache(cache_dir))
    result = build_pack(llm, doc, clean_pages(doc.pages), detect_chapters(doc), **kwargs)
    return result, llm


def test_end_to_end_with_fake_provider(pdf_with_outline, tmp_path):
    result, _ = _build(pdf_with_outline, FakeProvider(), tmp_path / "cache")
    assert result.report.ok, result.report.errors
    data = result.pack.model_dump(mode="json", exclude_none=True)
    pack, report = validate_data(json.loads(json.dumps(data)))
    assert pack and report.ok, report.errors
    assert [chapter.id for chapter in pack.chapters] == ["ch-01", "ch-02", "ch-03", "ch-04"]
    assert pack.chapters[0].cards[-1].type == "takeaway"
    assert pack.book.id == "manuale-di-prova"
    assert pack.book.author == "Ada Autrice"
    assert pack.book.lang == "it"


def test_chapter_selection_keeps_ids_stable(pdf_with_outline, tmp_path):
    result, _ = _build(pdf_with_outline, FakeProvider(), tmp_path / "cache", selected={2, 3})
    assert [chapter.id for chapter in result.pack.chapters] == ["ch-02", "ch-03"]
    assert result.pack.chapters[0].title == "Capitolo 2: tema 2"


def test_lang_override(pdf_with_outline, tmp_path):
    result, _ = _build(pdf_with_outline, FakeProvider(), tmp_path / "cache", lang="fr")
    assert result.pack.book.lang == "fr"


def test_rerun_uses_cache_and_pays_nothing(pdf_with_outline, tmp_path):
    cache = tmp_path / "cache"
    first_provider = FakeProvider()
    first, first_llm = _build(pdf_with_outline, first_provider, cache)
    assert first_llm.usage.calls == first_provider.calls > 0

    second_provider = FakeProvider()
    second, second_llm = _build(pdf_with_outline, second_provider, cache)
    assert second_provider.calls == 0
    assert second_llm.usage.cached == first_llm.usage.calls
    first_data = first.pack.model_dump(exclude={"generator"})
    assert first_data == second.pack.model_dump(exclude={"generator"})


def test_invalid_output_is_retried_with_the_error(tmp_path):
    seen: list[str] = []

    class Recording(FakeProvider):
        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            seen.append(user)
            return super().complete(system, user, schema)

    llm = StructuredLLM(Recording(fail_first=2), ResponseCache(tmp_path, enabled=False))
    parsed, _ = llm.generate(
        "sistema",
        "### ch-01 | Titolo",
        _book_draft(),
    )
    assert parsed.summary
    assert llm.usage.retries == 2
    assert "rejected" in seen[1] and "summary" in seen[1]


def test_gives_up_after_three_attempts(tmp_path):
    provider = FakeProvider(fail_first=99)
    llm = StructuredLLM(provider, ResponseCache(tmp_path, enabled=False))
    with pytest.raises(LLMError, match="3 tentativi"):
        llm.generate("sistema", "testo", _book_draft())
    assert provider.calls == 3


def _book_draft():
    from bookpack.condense.book import BookDraft

    return BookDraft


def test_constraint_failures_trigger_retry(pdf_with_outline, tmp_path):
    """Un capitolo che viola i vincoli viene rigenerato passando l'errore."""

    class TooLong(FakeProvider):
        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            response = super().complete(system, user, schema)
            if "intro" in schema["properties"] and "rejected" not in user:
                data = json.loads(response.text)
                data["cards"][0]["body"] = "parola " * 200
                response.text = json.dumps(data)
            return response

    result, llm = _build(pdf_with_outline, TooLong(), tmp_path / "cache", selected={1})
    assert result.report.ok
    assert llm.usage.retries == 1


class RecordingProvider(FakeProvider):
    def __init__(self) -> None:
        super().__init__()
        self.prompts: list[tuple[dict, str]] = []

    def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
        self.prompts.append((schema, user))
        return super().complete(system, user, schema)


def _chapter_from_text(words: int, tmp_path, provider=None, context_tokens=40_000):
    """Un capitolo con il numero di parole voluto, su pagine da 300 parole."""
    phrase = "Il metodo separa le decisioni dalla esecuzione in modo chiaro e verificabile. "
    per_page = 300
    count = max(words // per_page, 1)
    pages = {n: phrase * (per_page // 12) for n in range(1, count + 1)}
    llm = StructuredLLM(provider or FakeProvider(), ResponseCache(tmp_path / "cache"))
    section = Section("Capitolo lungo", 1, count)
    return condense_chapter(llm, section, 1, pages, "Libro", "it", context_tokens)


def _content_cards(chapter) -> list:
    skip = {"check", "section", "takeaway"}
    return [card for card in chapter.cards if card.type not in skip]


def test_cards_grow_with_chapter_length(tmp_path):
    short = _chapter_from_text(1_200, tmp_path / "a")
    long = _chapter_from_text(15_000, tmp_path / "b")
    assert len(_content_cards(short)) == 3
    assert 25 <= len(_content_cards(long)) <= 35
    assert long.estMinutes > short.estMinutes * 2


def test_long_chapter_is_split_in_parts_with_section_cards(tmp_path):
    chapter = _chapter_from_text(15_000, tmp_path)
    sections = [card for card in chapter.cards if card.type == "section"]
    assert len(sections) >= 3
    assert chapter.cards[0].type == "section"
    assert chapter.cards[-1].type == "takeaway"
    assert all(card.title and card.body for card in sections)
    ids = [card.id for card in chapter.cards]
    assert len(ids) == len(set(ids))


def test_short_chapter_has_no_section_cards(tmp_path):
    chapter = _chapter_from_text(1_200, tmp_path)
    assert not [card for card in chapter.cards if card.type == "section"]


def test_parts_cover_the_whole_chapter(tmp_path):
    provider = RecordingProvider()
    chapter = _chapter_from_text(15_000, tmp_path, provider)
    pages = {card.page for card in chapter.cards if card.page}
    assert max(pages) > chapter.pageEnd * 0.8
    assert min(pages) <= 2


def test_small_models_get_smaller_parts(tmp_path):
    provider = RecordingProvider()
    _chapter_from_text(6_000, tmp_path, provider, context_tokens=1_000)
    parts = [user for schema, user in provider.prompts if "intro" in schema["properties"]]
    assert len(parts) >= 6


def test_checks_are_placed_among_the_cards(tmp_path):
    chapter = _chapter_from_text(5_000, tmp_path)
    checks = [i for i, card in enumerate(chapter.cards) if card.type == "check"]
    assert checks
    assert all(chapter.cards[i].answer for i in checks)
    assert checks[0] > 0


def test_flashcards_and_summary_are_written_from_the_cards_not_the_source(tmp_path):
    provider = RecordingProvider()
    chapter = _chapter_from_text(5_000, tmp_path, provider)
    wraps = [user for schema, user in provider.prompts if "takeaway" in schema["properties"]]
    assert len(wraps) == 1
    assert "<chapter_part>" not in wraps[0]
    assert "[p. " not in wraps[0]
    assert "[concept] Idea 1" in wraps[0]
    assert "[check]" not in wraps[0]
    assert chapter.summary


def test_summary_length_is_enforced_with_a_retry(tmp_path):
    class ShortSummary(FakeProvider):
        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            response = super().complete(system, user, schema)
            if "takeaway" in schema["properties"] and "rejected" not in user:
                data = json.loads(response.text)
                data["summary"] = "Troppo breve."
                response.text = json.dumps(data)
            return response

    chapter = _chapter_from_text(2_000, tmp_path, ShortSummary())
    assert len(chapter.summary.split()) > 40


def _wrong_part(provider_class_changes):
    class Wrong(FakeProvider):
        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            response = super().complete(system, user, schema)
            if "intro" in schema["properties"] and "rejected" not in user:
                data = json.loads(response.text)
                provider_class_changes(data)
                response.text = json.dumps(data)
            return response

    return Wrong()


def test_too_few_cards_are_rejected_and_regenerated(tmp_path):
    def keep_one(data):
        data["cards"] = data["cards"][:1]

    provider = _wrong_part(keep_one)
    chapter = _chapter_from_text(10_000, tmp_path, provider)
    assert len(_content_cards(chapter)) >= 14
    assert provider.calls > 3


def test_missing_checks_are_rejected(tmp_path):
    def no_checks(data):
        data["cards"] = [card for card in data["cards"] if card["type"] != "check"]

    provider = RecordingProvider()
    llm = StructuredLLM(_wrong_part(no_checks), ResponseCache(tmp_path / "cache"))
    pages = {n: "Il metodo separa le decisioni dalla esecuzione. " * 40 for n in range(1, 8)}
    chapter = condense_chapter(llm, Section("C", 1, 7), 1, pages, "Libro", "it", 40_000)
    assert [card for card in chapter.cards if card.type == "check"]
    assert provider.calls == 0


def test_invented_quote_is_dropped_and_real_one_kept(tmp_path):
    real = "separa le decisioni dalla esecuzione"

    def add_quotes(data):
        page = data["cards"][0]["page"]
        quote = {
            "type": "quote", "title": None, "details": None, "steps": None, "code": None,
            "answer": None, "page": page,
        }  # fmt: skip
        data["cards"].append({**quote, "body": INVENTED if "invent" in MODE else real})

    INVENTED = "Una frase che nel libro non esiste affatto."
    MODE = ["invent"]
    notes: list[str] = []
    pages = {n: "Il metodo separa le decisioni dalla esecuzione. " * 40 for n in range(1, 8)}
    section = Section("C", 1, 7)

    class Quoting(FakeProvider):
        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            response = super().complete(system, user, schema)
            if "intro" in schema["properties"]:
                data = json.loads(response.text)
                add_quotes(data)
                response.text = json.dumps(data)
            return response

    llm = StructuredLLM(Quoting(), ResponseCache(tmp_path / "a"))
    chapter = condense_chapter(llm, section, 1, pages, "Libro", "it", 40_000, notes)
    assert not [card for card in chapter.cards if card.type == "quote"]
    assert "citazione non trovata" in notes[0]

    MODE.clear()
    llm = StructuredLLM(Quoting(), ResponseCache(tmp_path / "b"))
    chapter = condense_chapter(llm, section, 1, pages, "Libro", "it", 40_000)
    assert [card.body for card in chapter.cards if card.type == "quote"] == [real]


def test_estimate_grows_with_cards():
    phrase = "parola " * 300
    short = {n: phrase for n in range(1, 4)}
    long = {n: phrase for n in range(1, 51)}
    a = estimate_section(Section("A", 1, 3), short, 40_000)
    b = estimate_section(Section("B", 1, 50), long, 40_000)
    assert a.calls == 2
    assert b.calls > 3
    assert b.output_tokens > a.output_tokens * 3


def test_chunks_respect_size_and_keep_page_markers():
    pages = {n: f"Paragrafo della pagina {n}. " * 200 for n in range(1, 11)}
    section = Section("Lungo", 1, 10)
    chunks = chunk_section(section, pages, chunk_tokens=1000, overlap_tokens=100)
    assert len(chunks) > 1
    assert all(estimate_tokens(chunk) <= 1500 for chunk in chunks)
    assert all(chunk.startswith("[p. ") for chunk in chunks)


def test_chunk_overlap():
    pages = {1: "\n\n".join(f"Paragrafo {i}" * 30 for i in range(40))}
    chunks = chunk_section(Section("x", 1, 1), pages, chunk_tokens=500, overlap_tokens=200)
    last_of_first = chunks[0].split("\n\n")[-1]
    assert last_of_first in chunks[1]


def test_strict_schema_is_accepted_by_structured_outputs():
    schema = strict_schema(Overview)
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])
    assert "minItems" not in schema["properties"]["keyIdeas"]


def test_cli_build_with_fake_provider(pdf_with_outline, tmp_path, monkeypatch):
    monkeypatch.setenv("BOOKPACK_CACHE_DIR", str(tmp_path / "cache"))
    output = tmp_path / "out.bookpack.json"
    args = [
        "build", str(pdf_with_outline), "-o", str(output), "--fake",
        "--chapters", "1-2", "--yes",
    ]  # fmt: skip
    first = CliRunner().invoke(app, args)
    assert first.exit_code == 0, first.output
    assert len(json.loads(output.read_text("utf-8"))["chapters"]) == 2

    second = CliRunner().invoke(app, args)
    assert second.exit_code == 0, second.output
    assert "Chiamate 0" in second.output.replace("\n", " ")

    validated = CliRunner().invoke(app, ["validate", str(output)])
    assert validated.exit_code == 0, validated.output


def test_cli_build_asks_confirmation(pdf_with_outline, tmp_path, monkeypatch):
    monkeypatch.setenv("BOOKPACK_CACHE_DIR", str(tmp_path / "cache"))
    output = tmp_path / "out.bookpack.json"
    args = ["build", str(pdf_with_outline), "-o", str(output), "--fake"]
    declined = CliRunner().invoke(app, args, input="n\n")
    assert declined.exit_code != 0
    assert not output.exists()
