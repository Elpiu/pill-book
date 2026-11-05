"""Cache su disco delle risposte LLM, per riprendere un build senza ripagare le chiamate."""

import hashlib
import json
import os
import threading
from pathlib import Path


class ResponseCache:
    def __init__(self, directory: Path, enabled: bool = True) -> None:
        self.directory = directory
        self.enabled = enabled

    @staticmethod
    def key(*parts: str) -> str:
        digest = hashlib.sha256()
        for part in parts:
            digest.update(part.encode("utf-8"))
            digest.update(b"\0")
        return digest.hexdigest()

    def _path(self, key: str) -> Path:
        return self.directory / key[:2] / f"{key}.json"

    def get(self, key: str) -> dict | None:
        if not self.enabled:
            return None
        path = self._path(key)
        try:
            return json.loads(path.read_text("utf-8"))
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            return None  # file corrotto: si rifà la chiamata e lo si sovrascrive

    def put(self, key: str, value: dict) -> None:
        if not self.enabled:
            return
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Due attività con lo stesso prompt possono scrivere insieme: ognuna ha il suo temporaneo
        temp = path.with_name(f"{key}.{threading.get_ident()}.tmp")
        temp.write_text(json.dumps(value, ensure_ascii=False), "utf-8")
        os.replace(temp, path)

    def delete(self, key: str) -> None:
        if self.enabled:
            self._path(key).unlink(missing_ok=True)
