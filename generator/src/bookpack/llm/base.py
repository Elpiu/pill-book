"""Astrazione dei provider LLM e schema compatibile con gli output strutturati."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic import BaseModel

# Il testo di un capitolo sta in circa 2.000 token: il resto del margine è per il ragionamento,
# che sulla maggior parte dei provider conta nello stesso limite
MAX_OUTPUT_TOKENS = 32_000
RETRY_OUTPUT_TOKENS = 64_000

# I vincoli numerici e di lunghezza non sono accettati da tutti i modelli:
# si tolgono dallo schema inviato e si verificano in locale con Pydantic.
_UNSUPPORTED_KEYS = {
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "multipleOf",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
    "pattern",
    "default",
    "title",
}


class LLMError(Exception):
    pass


@dataclass
class LLMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float | None = None  # costo effettivo, se il provider lo comunica


class LLMProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
        """Restituisce un testo JSON conforme allo schema."""


def _inline_refs(node: object, defs: dict) -> object:
    # Alcuni modelli non gestiscono $ref: lo schema inviato è sempre esplicito
    if isinstance(node, list):
        return [_inline_refs(item, defs) for item in node]
    if not isinstance(node, dict):
        return node
    if "$ref" in node:
        return _inline_refs(defs[node["$ref"].rsplit("/", 1)[-1]], defs)
    return {key: _inline_refs(value, defs) for key, value in node.items()}


def _strict(node: object, *, in_properties: bool = False) -> object:
    if isinstance(node, list):
        return [_strict(item) for item in node]
    if not isinstance(node, dict):
        return node
    if in_properties:
        return {key: _strict(value) for key, value in node.items()}
    result = {}
    for key, value in node.items():
        if key in _UNSUPPORTED_KEYS:
            continue
        result[key] = _strict(value, in_properties=key == "properties")
    if result.get("type") == "object" and "properties" in result:
        result["additionalProperties"] = False
        result["required"] = list(result["properties"])
    return result


def strict_schema(model: type[BaseModel]) -> dict:
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})
    return _strict(_inline_refs(schema, defs))  # type: ignore[return-value]
