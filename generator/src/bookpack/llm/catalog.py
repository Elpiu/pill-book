"""Catalogo dei modelli di OpenRouter: prezzi e limiti, per stimare i costi di qualsiasi modello."""

import difflib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
CATALOG_MAX_AGE_SECONDS = 24 * 60 * 60
_FETCH_TIMEOUT_SECONDS = 15
# Un capitolo non deve occupare tutto il contesto: servono spazio per prompt e risposta
_CONTEXT_SHARE = 0.6
REASONING_EFFORT = "low"


@dataclass(frozen=True)
class ModelInfo:
    id: str
    name: str
    input_price: float | None  # dollari per milione di token
    output_price: float | None
    context_length: int | None
    max_output: int | None
    structured: bool
    reasoning_efforts: tuple[str, ...] = ()

    @property
    def prices(self) -> tuple[float, float] | None:
        if self.input_price is None or self.output_price is None:
            return None
        return self.input_price, self.output_price

    @property
    def reasoning_effort(self) -> str | None:
        """Livello da chiedere: condensare richiede poco ragionamento, che si paga come output.

        Solo se il modello dichiara `low`. Altrimenti resta il suo default: `none` spegnerebbe
        del tutto il ragionamento, e il suo effetto sulla qualità non è stato misurato.
        """
        return REASONING_EFFORT if REASONING_EFFORT in self.reasoning_efforts else None


def _price(value: object) -> float | None:
    # I router come openrouter/auto hanno prezzo -1: dipende dal modello che scelgono
    try:
        price = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return price * 1_000_000 if price >= 0 else None


def parse_catalog(data: dict) -> list[ModelInfo]:
    models = []
    for item in data.get("data", []):
        architecture = item.get("architecture") or {}
        if "text" not in (architecture.get("output_modalities") or ["text"]):
            continue
        pricing = item.get("pricing") or {}
        top_provider = item.get("top_provider") or {}
        reasoning = item.get("reasoning") or {}
        models.append(
            ModelInfo(
                id=item["id"],
                name=item.get("name") or item["id"],
                input_price=_price(pricing.get("prompt")),
                output_price=_price(pricing.get("completion")),
                context_length=item.get("context_length"),
                max_output=top_provider.get("max_completion_tokens"),
                structured="structured_outputs" in (item.get("supported_parameters") or []),
                reasoning_efforts=tuple(reasoning.get("supported_efforts") or ()),
            )
        )
    return models


def _fetch() -> dict:
    with urllib.request.urlopen(
        f"{OPENROUTER_BASE_URL}/models", timeout=_FETCH_TIMEOUT_SECONDS
    ) as response:
        return json.load(response)


def _read_cached(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_catalog(cache_dir: Path, refresh: bool = False) -> list[ModelInfo]:
    """Catalogo da disco se recente, altrimenti dalla rete. Senza rete usa la copia vecchia.

    Non solleva mai: senza catalogo i costi risultano non disponibili, ma tutto il resto funziona.
    """
    path = cache_dir / "openrouter-models.json"
    cached = _read_cached(path)
    if cached and not refresh and time.time() - path.stat().st_mtime < CATALOG_MAX_AGE_SECONDS:
        return parse_catalog(cached)
    try:
        data = _fetch()
    except (OSError, ValueError):  # urllib.error.URLError deriva da OSError
        return parse_catalog(cached) if cached else []

    cache_dir.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data), "utf-8")
    os.replace(temp, path)
    return parse_catalog(data)


def find_model(models: list[ModelInfo], model_id: str) -> ModelInfo | None:
    return next((model for model in models if model.id == model_id), None)


def suggest_models(models: list[ModelInfo], model_id: str, limit: int = 3) -> list[str]:
    return difflib.get_close_matches(model_id, [model.id for model in models], limit, cutoff=0.4)


def search_models(models: list[ModelInfo], query: str) -> list[ModelInfo]:
    terms = query.lower().split()
    return [
        model
        for model in models
        if all(term in f"{model.id} {model.name}".lower() for term in terms)
    ]


def context_budget(context_tokens: int, info: ModelInfo | None) -> int:
    """Budget per capitolo: il valore configurato, se il modello ha abbastanza contesto."""
    if info and info.context_length:
        return min(context_tokens, int(info.context_length * _CONTEXT_SHARE))
    return context_tokens
