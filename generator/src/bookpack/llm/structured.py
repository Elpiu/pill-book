"""Chiamate LLM con output validato, retry passando l'errore al modello e cache."""

import json
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ..cache import ResponseCache
from .base import LLMError, LLMProvider, LLMResponse, strict_schema

T = TypeVar("T", bound=BaseModel)
# Una chiamata iniziale e fino a 2 tentativi con l'errore
MAX_ATTEMPTS = 3


@dataclass
class Usage:
    calls: int = 0
    cached: int = 0
    retries: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float | None = None  # somma dei costi comunicati dal provider


class StructuredLLM:
    """Si può usare da più thread: il provider e la cache lo reggono, i contatori hanno un lock."""

    def __init__(self, provider: LLMProvider, cache: ResponseCache) -> None:
        self.provider = provider
        self.cache = cache
        self.usage = Usage()
        self._lock = threading.Lock()

    def _key(self, system: str, user: str, schema: dict) -> str:
        return self.cache.key(
            self.provider.name,
            self.provider.model,
            system,
            user,
            json.dumps(schema, sort_keys=True),
        )

    def _complete(self, system: str, user: str, schema: dict) -> LLMResponse:
        if (cached := self.cache.get(self._key(system, user, schema))) is not None:
            with self._lock:
                self.usage.cached += 1
            return LLMResponse(
                text=cached["text"],
                input_tokens=cached.get("input_tokens", 0),
                output_tokens=cached.get("output_tokens", 0),
                cost=cached.get("cost"),
            )

        response = self.provider.complete(system, user, schema)
        with self._lock:
            self.usage.calls += 1
            self.usage.input_tokens += response.input_tokens
            self.usage.output_tokens += response.output_tokens
            if response.cost is not None:
                self.usage.cost = (self.usage.cost or 0.0) + response.cost
        return response

    def generate(
        self,
        system: str,
        user: str,
        output_model: type[T],
        convert: Callable[[T], object] | None = None,
    ) -> tuple[T, object]:
        """Genera e valida. `convert` può sollevare ValueError per chiedere un nuovo tentativo.

        Restituisce il modello grezzo e il risultato di `convert`.
        """
        schema = strict_schema(output_model)
        prompt = user
        last_error = ""
        for attempt in range(MAX_ATTEMPTS):
            if attempt:
                with self._lock:
                    self.usage.retries += 1
            response = self._complete(system, prompt, schema)
            try:
                parsed = output_model.model_validate_json(response.text)
                result = convert(parsed) if convert else None
            except ValidationError as exc:
                last_error = _format_validation_error(exc)
            except ValueError as exc:
                last_error = str(exc)
            else:
                # Si conserva sotto il prompt iniziale, anche se è servito un ritentativo: così
                # riprendendo si ritrova subito, invece di ripagare la prima chiamata
                self.cache.put(
                    self._key(system, user, schema),
                    {
                        "text": response.text,
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost": response.cost,
                    },
                )
                return parsed, result
            # Una risposta scartata non resta: rilanciando va chiesta di nuovo, non riletta
            self.cache.delete(self._key(system, prompt, schema))
            prompt = (
                f"{user}\n\n<previous_attempt>\n{response.text}\n</previous_attempt>\n\n"
                "The previous attempt was rejected for these reasons. Produce a corrected, complete "
                f"output that keeps what was right and fixes all of them:\n{last_error}"
            )
        raise LLMError(f"Output non valido dopo {MAX_ATTEMPTS} tentativi:\n{last_error}")


def _format_validation_error(exc: ValidationError) -> str:
    lines = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"]) or "(root)"
        lines.append(f"- {location}: {error['msg']}")
    return "\n".join(lines)
