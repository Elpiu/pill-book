"""Esecuzione delle attività di una generazione: alcune insieme, e senza fermarsi al primo errore.

Ogni attività è una chiamata all'LLM che aspetta la rete, quindi bastano i thread. Le risposte
finiscono in cache, perciò interrompersi tra un'attività e l'altra non fa perdere nulla.
"""

from collections.abc import Callable
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from threading import Event

from ..llm.base import LLMError

# Ogni quanto il thread principale si sveglia: su Windows Ctrl+C non interrompe un'attesa senza fine
POLL_SECONDS = 0.2
_NOT_STARTED = object()


@dataclass
class Task:
    name: str  # stabile, per il file di stato
    label: str  # per chi legge
    work: Callable[[], object]


def _describe(error: Exception) -> str:
    return str(error) if isinstance(error, LLMError) else f"{type(error).__name__}: {error}"


class TaskRunner:
    """`on_finished` gira nel thread di chi chiama `run`; `should_stop` in quelli delle attività."""

    def __init__(
        self,
        workers: int,
        should_stop: Callable[[], bool],
        on_finished: Callable[[Task, str | None], None],
    ) -> None:
        self.workers = workers
        self.should_stop = should_stop
        self.on_finished = on_finished
        self.halted = Event()
        self.failures: dict[str, str] = {}  # per etichetta

    def _start(self, task: Task) -> object:
        if self.should_stop():
            self.halted.set()
        if self.halted.is_set():
            return _NOT_STARTED
        try:
            return task.work()
        except LLMError as exc:
            # Le attività in corso e già pagate finiscono: si ferma solo ciò che non è partito
            if exc.fatal:
                self.halted.set()
            raise

    def _collect(self, task: Task, future: Future, results: dict[str, object]) -> None:
        error = future.exception()
        if error is None:
            result = future.result()
            if result is not _NOT_STARTED:
                results[task.name] = result
                self.on_finished(task, None)
            return
        self.failures[task.label] = _describe(error)
        self.on_finished(task, self.failures[task.label])

    def run(self, tasks: list[Task]) -> dict[str, object]:
        """I risultati delle attività riuscite, per nome. Si possono eseguire più gruppi di fila."""
        results: dict[str, object] = {}
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            pending = {pool.submit(self._start, task): task for task in tasks}
            while pending:
                try:
                    done, _ = wait(pending, timeout=POLL_SECONDS, return_when=FIRST_COMPLETED)
                    for future in done:
                        self._collect(pending[future], future, results)
                        del pending[future]
                except KeyboardInterrupt:
                    self.halted.set()  # Ctrl+C: come Interrompi nella finestra
        return results
