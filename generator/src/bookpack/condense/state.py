"""File di stato di una generazione: parametri, attività e costo, per riprenderla più tardi.

Le risposte restano solo nella cache: riprendendo, ciò che è pronto si ritrova da lì. Il file serve
a riavere gli stessi parametri (comprese le pagine corrette a mano, da cui dipendono i prompt), a
sommare il costo tra un lancio e l'altro e a vedere a che punto si è. Non contiene testo del libro
né chiavi. Quando il pack è scritto si cancella.
"""

import hashlib
import json
import os
import threading
from collections import Counter
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from ..extract.toc import Detection, Section
from ..llm.structured import Usage

STATE_VERSION = 1
STATE_SUFFIX = ".state.json"
PENDING = "pending"
DONE = "done"
FAILED = "failed"


class StateError(Exception):
    pass


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def state_path_for(output: Path) -> Path:
    stem = output.name.removesuffix(".json").removesuffix(".bookpack")
    return output.with_name(stem + STATE_SUFFIX)


@dataclass
class BuildInput:
    pdf: str
    pdf_sha256: str
    model: str
    fake: bool
    lang: str | None
    selected: list[int]
    output: str
    context_tokens: int
    detection: Detection

    @classmethod
    def from_dict(cls, data: dict) -> "BuildInput":
        found = data["detection"]
        sections = [Section(**section) for section in found["sections"]]
        detection = Detection(found["method"], sections, found["book"], found.get("note"))
        return cls(**{**data, "detection": detection})


@dataclass
class Spent:
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float | None = None

    def plus(self, usage: Usage) -> "Spent":
        known = [cost for cost in (self.cost, usage.cost) if cost is not None]
        return Spent(
            self.calls + usage.calls,
            self.input_tokens + usage.input_tokens,
            self.output_tokens + usage.output_tokens,
            sum(known) if known else None,
        )


class BuildState:
    def __init__(
        self,
        path: Path,
        build_input: BuildInput,
        tasks: dict[str, dict] | None = None,
        spent: Spent | None = None,
    ) -> None:
        self.path = path
        self.input = build_input
        self.tasks = tasks or {}
        self.previous = spent or Spent()  # speso nei lanci precedenti
        self.spent = self.previous
        self._lock = threading.Lock()

    @classmethod
    def load(cls, path: Path) -> "BuildState":
        try:
            data = json.loads(path.read_text("utf-8"))
            if data["version"] != STATE_VERSION:
                raise StateError(f"{path}: versione {data['version']} non supportata")
            return cls(
                path,
                BuildInput.from_dict(data["input"]),
                data["tasks"],
                Spent(**data["spent"]),
            )
        except OSError as exc:
            raise StateError(f"Non riesco a leggere {path}: {exc}") from exc
        except (ValueError, KeyError, TypeError) as exc:
            raise StateError(f"{path} non è un file di stato valido: {exc}") from exc

    @classmethod
    def begin(cls, path: Path, build_input: BuildInput) -> "BuildState":
        """Se il file descrive lo stesso lavoro, il costo già speso continua a sommarsi."""
        try:
            old = cls.load(path)
        except StateError:
            return cls(path, build_input)
        same = replace(old.input, pdf=build_input.pdf) == build_input
        return cls(path, build_input, spent=old.spent if same else None)

    def plan(self, names: list[str]) -> None:
        """Tutto da fare: ciò che è già pronto torna subito dalla cache."""
        with self._lock:
            self.tasks = {name: {"state": PENDING} for name in names}
            self._save()

    def mark(self, name: str, error: str | None, usage: Usage) -> None:
        with self._lock:
            self.tasks[name] = (
                {"state": DONE} if error is None else {"state": FAILED, "error": error}
            )
            self.spent = self.previous.plus(usage)
            self._save()

    def counts(self) -> Counter:
        return Counter(task["state"] for task in self.tasks.values())

    def remove(self) -> None:
        self.path.unlink(missing_ok=True)

    def _save(self) -> None:
        data = {
            "version": STATE_VERSION,
            "input": asdict(self.input),
            "tasks": self.tasks,
            "spent": asdict(self.spent),
        }
        temp = self.path.with_name(f"{self.path.name}.tmp")
        # È un aiuto: non vale la pena perdere una generazione se non si riesce a scriverlo
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", "utf-8")
            os.replace(temp, self.path)
        except OSError:
            pass


def find_state(folders: list[Path], pdf_sha256: str) -> BuildState | None:
    """La generazione incompleta più recente di questo PDF, se c'è."""
    found: list[BuildState] = []
    for folder in dict.fromkeys(folders):
        for path in folder.glob(f"*{STATE_SUFFIX}"):
            try:
                state = BuildState.load(path)
            except StateError:
                continue
            if state.input.pdf_sha256 == pdf_sha256:
                found.append(state)
    return max(found, key=lambda state: state.path.stat().st_mtime, default=None)
