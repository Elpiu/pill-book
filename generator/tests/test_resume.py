"""Generazione in parallelo, errori, interruzioni e ripresa, senza rete né costi."""

import json
import threading
import time

import pytest
from pydantic import BaseModel
from typer.testing import CliRunner

from bookpack.cache import ResponseCache
from bookpack.cli import app
from bookpack.condense import tasks as tasks_module
from bookpack.condense.pipeline import BuildIncomplete, build_pack, make_input
from bookpack.condense.state import BuildState, StateError, file_sha256, find_state, state_path_for
from bookpack.condense.tasks import Task, TaskRunner
from bookpack.extract.clean import clean_pages
from bookpack.extract.pdf import open_pdf
from bookpack.extract.toc import detect_chapters
from bookpack.llm.base import LLMError, LLMResponse, strict_schema
from bookpack.llm.fake import FakeProvider
from bookpack.llm.structured import StructuredLLM


class Out(BaseModel):
    value: int


class FailsOn(FakeProvider):
    """Fallisce sulle chiamate il cui prompt contiene `marker`."""

    def __init__(self, marker: str, fatal: bool = False) -> None:
        super().__init__()
        self.marker = marker
        self.fatal = fatal

    def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
        if self.marker in user:
            raise LLMError("il provider ha sbagliato", fatal=self.fatal)
        return super().complete(system, user, schema)


class Costly(FakeProvider):
    def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
        response = super().complete(system, user, schema)
        response.cost = 0.01
        return response


def _run(pdf, provider, cache_dir, **kwargs):
    doc = open_pdf(pdf)
    llm = StructuredLLM(provider, ResponseCache(cache_dir))
    return build_pack(llm, doc, clean_pages(doc.pages), detect_chapters(doc), **kwargs), llm


# --- Cache ---------------------------------------------------------------------------------------


def test_rejected_answers_are_asked_again_when_rerunning(tmp_path):
    """Prima il rilancio rileggeva dalla cache le stesse risposte sbagliate, per sempre."""

    class WrongThenRight(FakeProvider):
        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            self.calls += 1
            return LLMResponse('{"value": "x"}' if self.calls <= 3 else '{"value": 1}')

    provider = WrongThenRight()
    with pytest.raises(LLMError, match="3 tentativi"):
        StructuredLLM(provider, ResponseCache(tmp_path)).generate("s", "u", Out)
    assert provider.calls == 3

    parsed, _ = StructuredLLM(provider, ResponseCache(tmp_path)).generate("s", "u", Out)
    assert parsed.value == 1
    assert provider.calls == 4


def test_an_answer_that_needed_a_retry_is_not_paid_again(tmp_path):
    class Answers(FakeProvider):
        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            self.calls += 1
            return LLMResponse('{"value": "x"}' if self.calls == 1 else '{"value": 1}')

    provider = Answers()
    first = StructuredLLM(provider, ResponseCache(tmp_path))
    assert first.generate("s", "u", Out)[0].value == 1
    assert first.usage.retries == 1
    assert provider.calls == 2

    second = StructuredLLM(provider, ResponseCache(tmp_path))
    assert second.generate("s", "u", Out)[0].value == 1
    assert provider.calls == 2
    assert second.usage.cached == 1


def test_a_cache_written_by_the_old_version_gets_unstuck(tmp_path):
    """Le vecchie cache contengono risposte scartate: non devono bloccare il rilancio."""
    cache = ResponseCache(tmp_path)

    class Right(FakeProvider):
        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            self.calls += 1
            return LLMResponse('{"value": 1}')

    provider = Right()
    llm = StructuredLLM(provider, cache)
    cache.put(llm._key("s", "u", strict_schema(Out)), {"text": '{"value": "x"}'})
    assert llm.generate("s", "u", Out)[0].value == 1
    assert provider.calls == 1
    assert StructuredLLM(provider, cache).generate("s", "u", Out)[0].value == 1
    assert provider.calls == 1


# --- Parallelismo --------------------------------------------------------------------------------


def test_parallel_pack_is_identical_to_the_sequential_one(pdf_with_outline, tmp_path):
    class Scrambled(FakeProvider):
        """Le risposte arrivano in ordine diverso da quello delle richieste."""

        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            time.sleep(0.05 - 0.01 * (hash(user) % 5))
            return super().complete(system, user, schema)

    sequential, _ = _run(pdf_with_outline, FakeProvider(), tmp_path / "a", workers=1)
    parallel, _ = _run(pdf_with_outline, Scrambled(), tmp_path / "b", workers=4)
    assert parallel.report.ok
    assert parallel.pack.model_dump(exclude={"generator"}) == sequential.pack.model_dump(
        exclude={"generator"}
    )
    assert parallel.notes == sequential.notes


def test_workers_limit_the_calls_running_together(pdf_with_outline, tmp_path):
    class Measuring(FakeProvider):
        def __init__(self) -> None:
            super().__init__()
            self.running = 0
            self.highest = 0
            self.lock = threading.Lock()

        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            with self.lock:
                self.running += 1
                self.highest = max(self.highest, self.running)
            time.sleep(0.03)
            with self.lock:
                self.running -= 1
            return super().complete(system, user, schema)

    provider = Measuring()
    _run(pdf_with_outline, provider, tmp_path / "a", workers=3)
    assert provider.highest == 3

    provider = Measuring()
    _run(pdf_with_outline, provider, tmp_path / "b", workers=1)
    assert provider.highest == 1


def test_phases_run_in_order(pdf_with_outline, tmp_path):
    seen: list[str] = []

    class Recording(FakeProvider):
        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            seen.append(
                next(k for k in ("intro", "takeaway", "keyIdeas") if k in schema["properties"])
            )
            return super().complete(system, user, schema)

    _run(pdf_with_outline, Recording(), tmp_path / "cache", workers=4)
    assert seen == ["intro"] * 4 + ["takeaway"] * 4 + ["keyIdeas"]


def test_steps_report_progress(pdf_with_outline, tmp_path):
    steps: list[tuple[str, int, int]] = []
    _run(
        pdf_with_outline,
        FakeProvider(),
        tmp_path / "cache",
        workers=4,
        on_step=lambda *step: steps.append(step),
    )
    assert [done for _, done, _ in steps] == list(range(1, 10))
    assert all(total == 9 for _, _, total in steps)
    assert steps[-1][0] == "Panoramica del libro"


# --- Errori e interruzioni -----------------------------------------------------------------------


def test_one_failure_does_not_stop_the_others_and_rerun_does_only_that(pdf_with_outline, tmp_path):
    cache = tmp_path / "cache"
    failing = FailsOn("Capitolo 2: tema 2")
    with pytest.raises(BuildIncomplete) as caught:
        _run(pdf_with_outline, failing, cache, workers=2)
    # Fallisce sia la parte sia, se ci arrivasse, la chiusura: gli altri 3 capitoli sono completi
    assert failing.calls == 6
    assert caught.value.done == 6
    assert caught.value.total == 9
    assert list(caught.value.failures.values()) == ["il provider ha sbagliato"]
    assert "Capitolo 2, parte 1 di 1" in next(iter(caught.value.failures))

    resumed = FakeProvider()
    result, llm = _run(pdf_with_outline, resumed, cache, workers=2)
    assert result.report.ok
    assert resumed.calls == 3  # la parte, la sua chiusura e il libro
    assert llm.usage.cached == 6
    assert len(result.pack.chapters) == 4


def test_fatal_error_does_not_try_everything_else(pdf_with_outline, tmp_path):
    provider = FailsOn("<chapter_part>", fatal=True)
    with pytest.raises(BuildIncomplete) as caught:
        _run(pdf_with_outline, provider, tmp_path / "cache", workers=1)
    assert len(caught.value.failures) == 1
    assert caught.value.done == 0


def test_stop_starts_nothing_new_and_keeps_what_is_running(pdf_with_outline, tmp_path):
    cache = tmp_path / "cache"
    stop = threading.Event()

    class StopAtFirst(FakeProvider):
        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            stop.set()
            time.sleep(0.05)
            return super().complete(system, user, schema)

    provider = StopAtFirst()
    with pytest.raises(BuildIncomplete) as caught:
        _run(pdf_with_outline, provider, cache, workers=2, should_stop=stop.is_set)
    assert caught.value.failures == {}
    assert 1 <= provider.calls <= 2
    assert caught.value.done == provider.calls

    resumed = FakeProvider()
    _run(pdf_with_outline, resumed, cache, workers=2)
    assert resumed.calls == 9 - provider.calls


def test_ctrl_c_behaves_like_stop(pdf_with_outline, tmp_path, monkeypatch):
    real_wait = tasks_module.wait
    interrupts = [KeyboardInterrupt()]

    def wait_interrupted(*args, **kwargs):
        if interrupts:
            raise interrupts.pop()
        return real_wait(*args, **kwargs)

    monkeypatch.setattr(tasks_module, "wait", wait_interrupted)

    class Slow(FakeProvider):
        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            time.sleep(0.05)
            return super().complete(system, user, schema)

    provider = Slow()
    with pytest.raises(BuildIncomplete) as caught:
        _run(pdf_with_outline, provider, tmp_path / "cache", workers=1)
    assert caught.value.failures == {}
    assert provider.calls < 9


def test_unexpected_exceptions_are_reported_not_lost():
    finished: list[tuple[str, str | None]] = []

    def boom() -> None:
        raise RuntimeError("guasto")

    runner = TaskRunner(2, lambda: False, lambda task, error: finished.append((task.name, error)))
    results = runner.run([Task("a", "A", boom), Task("b", "B", lambda: 7)])
    assert results == {"b": 7}
    assert runner.failures == {"A": "RuntimeError: guasto"}
    assert ("a", "RuntimeError: guasto") in finished


# --- File di stato -------------------------------------------------------------------------------


def _state(pdf, output, detection=None, model="fake-1"):
    doc = open_pdf(pdf)
    detection = detection or detect_chapters(doc)
    build_input = make_input(
        pdf, file_sha256(pdf), model, True, None, None, output, 40_000, detection
    )
    return BuildState.begin(state_path_for(output), build_input)


def test_state_path_sits_next_to_the_pack(tmp_path):
    assert state_path_for(tmp_path / "x.bookpack.json") == tmp_path / "x.state.json"
    assert state_path_for(tmp_path / "x.json") == tmp_path / "x.state.json"


def test_state_tracks_every_task_and_survives_a_failure(pdf_with_outline, tmp_path):
    state = _state(pdf_with_outline, tmp_path / "x.bookpack.json")
    with pytest.raises(BuildIncomplete):
        _run(
            pdf_with_outline,
            FailsOn("Capitolo 2: tema 2"),
            tmp_path / "cache",
            workers=2,
            state=state,
        )

    saved = json.loads(state.path.read_text("utf-8"))
    assert saved["tasks"]["ch-01/part-1"] == {"state": "done"}
    assert saved["tasks"]["ch-01/wrap"] == {"state": "done"}
    assert saved["tasks"]["ch-02/part-1"] == {
        "state": "failed",
        "error": "il provider ha sbagliato",
    }
    assert saved["tasks"]["ch-02/wrap"] == {"state": "pending"}
    assert saved["tasks"]["book"] == {"state": "pending"}
    assert saved["spent"]["calls"] == 6

    loaded = BuildState.load(state.path)
    assert loaded.input == state.input
    assert loaded.counts() == {"done": 6, "failed": 1, "pending": 2}


def test_state_contains_neither_the_book_text_nor_secrets(pdf_with_outline, tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-segretissima")
    state = _state(pdf_with_outline, tmp_path / "x.bookpack.json")
    _run(pdf_with_outline, FakeProvider(), tmp_path / "cache", state=state)
    text = state.path.read_text("utf-8")
    assert "sk-or-segretissima" not in text
    assert "separa le decisioni" not in text


def test_cost_adds_up_across_runs_of_the_same_work(pdf_with_outline, tmp_path):
    output = tmp_path / "x.bookpack.json"
    cache = tmp_path / "cache"

    class CostlyFailing(Costly):
        def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
            if "Capitolo 2: tema 2" in user:
                raise LLMError("il provider ha sbagliato")
            return super().complete(system, user, schema)

    with pytest.raises(BuildIncomplete):
        _run(
            pdf_with_outline,
            CostlyFailing(),
            cache,
            state=_state(pdf_with_outline, output),
        )

    state = _state(pdf_with_outline, output)
    assert state.previous.calls == 6
    assert state.previous.cost == pytest.approx(0.06)
    _run(pdf_with_outline, Costly(), cache, state=state)
    assert state.spent.calls == 9
    assert state.spent.cost == pytest.approx(0.09)


def test_a_different_work_starts_counting_again(pdf_with_outline, tmp_path):
    output = tmp_path / "x.bookpack.json"
    state = _state(pdf_with_outline, output)
    _run(pdf_with_outline, Costly(), tmp_path / "cache", state=state)
    assert _state(pdf_with_outline, output).previous.calls == 9
    assert _state(pdf_with_outline, output, model="altro").previous.calls == 0


def test_broken_state_files_are_refused_and_ignored(pdf_with_outline, tmp_path):
    broken = tmp_path / "rotto.state.json"
    broken.write_text("{ non è json", "utf-8")
    with pytest.raises(StateError, match="non è un file di stato valido"):
        BuildState.load(broken)
    other = tmp_path / "altro.state.json"
    other.write_text(json.dumps({"version": 999}), "utf-8")
    with pytest.raises(StateError, match="999"):
        BuildState.load(other)
    assert find_state([tmp_path], "qualunque") is None

    state = _state(pdf_with_outline, tmp_path / "x.bookpack.json")
    assert state.previous.calls == 0
    state.plan(["a"])
    assert find_state([tmp_path, tmp_path], state.input.pdf_sha256).path == state.path
    assert find_state([tmp_path], "altro hash") is None


# --- CLI -----------------------------------------------------------------------------------------


def _write_toc(pdf, path):
    path.write_text(
        "book: {title: Titolo dal file}\nchapters:\n"
        "- {title: Primo capitolo, pageStart: 3, pageEnd: 6}\n"
        "- {title: Secondo capitolo, pageStart: 7, pageEnd: 10}\n"
        "- {title: Terzo capitolo, pageStart: 11, pageEnd: 14}\n",
        "utf-8",
    )
    return path


def test_cli_failure_then_resume_with_the_same_parameters(pdf_with_outline, tmp_path, monkeypatch):
    monkeypatch.setenv("BOOKPACK_CACHE_DIR", str(tmp_path / "cache"))
    output = tmp_path / "libro.bookpack.json"
    state_file = tmp_path / "libro.state.json"
    toc = _write_toc(pdf_with_outline, tmp_path / "libro.toc.yaml")
    failing = FailsOn("Secondo capitolo")
    monkeypatch.setattr("bookpack.cli.get_provider", lambda *_: failing)
    args = ["build", str(pdf_with_outline), "-o", str(output), "--fake", "--yes"]
    failed = CliRunner().invoke(
        app, [*args, "--toc", str(toc), "--chapters", "1-2", "--lang", "fr", "--workers", "2"]
    )
    assert failed.exit_code == 1, failed.output
    assert "il provider ha sbagliato" in " ".join(failed.output.split())
    assert "bookpack resume" in failed.output
    assert not output.exists()
    assert state_file.exists()

    # Riprende senza ripetere file dei capitoli, selezione e lingua
    provider = FakeProvider()
    monkeypatch.setattr("bookpack.cli.get_provider", lambda *_: provider)
    toc.unlink()
    resumed = CliRunner().invoke(app, ["resume", str(state_file), "--yes"])
    assert resumed.exit_code == 0, resumed.output
    assert "1 non riuscite" in " ".join(resumed.output.split())
    assert provider.calls == 3
    pack = json.loads(output.read_text("utf-8"))
    assert pack["book"]["title"] == "Titolo dal file"
    assert pack["book"]["lang"] == "fr"
    assert [chapter["title"] for chapter in pack["chapters"]] == [
        "Primo capitolo",
        "Secondo capitolo",
    ]
    assert not state_file.exists()


def test_cli_resume_asks_confirmation(pdf_with_outline, tmp_path, monkeypatch):
    state_file = _prepare_unfinished(pdf_with_outline, tmp_path, monkeypatch)
    declined = CliRunner().invoke(app, ["resume", str(state_file)], input="n\n")
    assert declined.exit_code != 0
    assert "6 attività fatte" in declined.output
    assert state_file.exists()


def _prepare_unfinished(pdf, tmp_path, monkeypatch):
    monkeypatch.setenv("BOOKPACK_CACHE_DIR", str(tmp_path / "cache"))
    output = tmp_path / "libro.bookpack.json"
    with monkeypatch.context() as patch:
        patch.setattr("bookpack.cli.get_provider", lambda *_: FailsOn("Capitolo 2: tema 2"))
        result = CliRunner().invoke(app, ["build", str(pdf), "-o", str(output), "--fake", "--yes"])
    assert result.exit_code == 1, result.output
    return tmp_path / "libro.state.json"


def test_cli_resume_refuses_a_different_pdf(pdf_with_outline, tmp_path, monkeypatch):
    state_file = _prepare_unfinished(pdf_with_outline, tmp_path, monkeypatch)
    other = tmp_path / "altro.pdf"
    other.write_bytes(pdf_with_outline.read_bytes() + b"\n% cambiato")
    refused = CliRunner().invoke(app, ["resume", str(state_file), "--pdf", str(other), "--yes"])
    assert refused.exit_code == 1
    assert "non è il PDF" in refused.output.replace("\n", " ")


def test_cli_resume_finds_a_moved_pdf_with_the_option(pdf_with_outline, tmp_path, monkeypatch):
    state_file = _prepare_unfinished(pdf_with_outline, tmp_path, monkeypatch)
    moved = tmp_path / "spostato.pdf"
    pdf_with_outline.rename(moved)

    missing = CliRunner().invoke(app, ["resume", str(state_file), "--yes"])
    assert missing.exit_code == 1
    assert "--pdf" in missing.output

    resumed = CliRunner().invoke(app, ["resume", str(state_file), "--pdf", str(moved), "--yes"])
    assert resumed.exit_code == 0, resumed.output
    assert (tmp_path / "libro.bookpack.json").exists()


def test_bad_workers_setting_is_explained(pdf_with_outline, tmp_path, monkeypatch):
    monkeypatch.setenv("BOOKPACK_WORKERS", "tanti")
    output = tmp_path / "x.bookpack.json"
    result = CliRunner().invoke(
        app, ["build", str(pdf_with_outline), "-o", str(output), "--fake", "--yes"]
    )
    assert result.exit_code == 1
    assert "BOOKPACK_WORKERS" in result.output
