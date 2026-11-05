import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookpack.cache import ResponseCache
from bookpack.cli import app
from bookpack.condense.chunking import chunk_section, estimate_tokens
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


def test_interrupted_build_resumes_from_cache(pdf_with_outline, tmp_path):
    cache = tmp_path / "cache"

    class Interrupted(FakeProvider):
        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            if self.calls == 2:
                raise LLMError("rete caduta")
            return super().complete(system, user, schema)

    with pytest.raises(LLMError):
        _build(pdf_with_outline, Interrupted(), cache)

    resumed = FakeProvider()
    result, llm = _build(pdf_with_outline, resumed, cache)
    assert result.report.ok
    assert llm.usage.cached == 2
    assert resumed.calls == 3  # due capitoli restanti e il livello libro


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
            if "cards" in schema["properties"] and "rejected" not in user:
                data = json.loads(response.text)
                data["cards"][0]["body"] = "parola " * 200
                response.text = json.dumps(data)
            return response

    result, llm = _build(pdf_with_outline, TooLong(), tmp_path / "cache", selected={1})
    assert result.report.ok
    assert llm.usage.retries == 1


def test_long_chapter_uses_map_reduce(pdf_with_outline, tmp_path):
    provider = FakeProvider()
    result, _ = _build(
        pdf_with_outline, provider, tmp_path / "cache", context_tokens=100, selected={1}
    )
    assert result.report.ok, result.report.errors
    # Almeno una chiamata per le note, una per il capitolo e una per il libro
    assert provider.calls >= 3
    chapter = result.pack.chapters[0]
    assert all(chapter.pageStart <= c.page <= chapter.pageEnd for c in chapter.flashcards)


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
