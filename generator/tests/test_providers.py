"""Il provider OpenRouter contro un trasporto HTTP simulato: niente rete, ma SDK e richieste veri."""

import json

import httpx2 as httpx
import openai
import pytest
from pydantic import BaseModel

from bookpack.cache import ResponseCache
from bookpack.config import load_settings
from bookpack.llm import get_provider
from bookpack.llm import openrouter as openrouter_module
from bookpack.llm.base import MAX_OUTPUT_TOKENS, RETRY_OUTPUT_TOKENS, LLMError
from bookpack.llm.catalog import ModelInfo
from bookpack.llm.fake import FakeProvider
from bookpack.llm.openrouter import OpenRouterProvider
from bookpack.llm.structured import StructuredLLM

SCHEMA = {
    "type": "object",
    "properties": {"a": {"type": "string"}},
    "required": ["a"],
    "additionalProperties": False,
}


def _completion(content='{"a":"ok"}', finish_reason="stop", **extra) -> dict:
    return {
        "id": "c1",
        "object": "chat.completion",
        "created": 1,
        "model": "x/y",
        "choices": [
            {
                "index": 0,
                "finish_reason": finish_reason,
                "message": {"role": "assistant", "content": content},
                **extra,
            }
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8, "cost": 0.0123},
    }


def _provider(handler, model="x/y") -> OpenRouterProvider:
    provider = OpenRouterProvider(model, "sk-or-test")
    provider.client = openai.OpenAI(
        api_key="sk-or-test",
        max_retries=0,
        base_url="https://llm.test/api/v1",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    return provider


@pytest.fixture(autouse=True)
def no_delay(monkeypatch):
    monkeypatch.setattr(openrouter_module, "_TRANSIENT_DELAY_SECONDS", 0)


def test_request_uses_json_schema_and_only_compliant_providers():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers["authorization"]
        return httpx.Response(200, json=_completion())

    response = _provider(handler).complete("sistema", "utente", SCHEMA)

    assert response.text == '{"a":"ok"}'
    assert (response.input_tokens, response.output_tokens) == (5, 3)
    assert response.cost == 0.0123
    body = seen["body"]
    assert body["model"] == "x/y"
    assert body["response_format"]["json_schema"]["schema"] == SCHEMA
    assert body["provider"] == {"require_parameters": True}
    assert body["messages"][0] == {"role": "system", "content": "sistema"}
    assert seen["auth"] == "Bearer sk-or-test"


@pytest.mark.parametrize("status", [400, 404, 503])
def test_model_without_structured_outputs_falls_back_to_prompt(status):
    bodies = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        if "response_format" in bodies[-1]:
            return httpx.Response(status, json={"error": {"code": status, "message": "no"}})
        return httpx.Response(200, json=_completion('```json\n{"a":"ok"}\n```'))

    provider = _provider(handler)
    assert provider.complete("s", "u", SCHEMA).text == '{"a":"ok"}'
    assert "provider" not in bodies[1]
    assert "schema" in bodies[1]["messages"][0]["content"]

    # Non riprova lo schema a ogni chiamata
    provider.complete("s", "u2", SCHEMA)
    assert len(bodies) == 3


def test_json_is_extracted_from_surrounding_text():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_completion('Ecco il risultato: {"a":"ok"} fine'))

    assert _provider(handler).complete("s", "u", SCHEMA).text == '{"a":"ok"}'


@pytest.mark.parametrize(
    "first",
    [
        {"error": {"code": 502, "message": "boom"}},
        _completion(content=""),
        _completion(finish_reason="error", error={"message": "boom"}),
    ],
    ids=["solo errore", "vuota", "errore nella scelta"],
)
def test_errors_with_status_200_are_retried(first):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(200, json=first if len(calls) == 1 else _completion())

    assert _provider(handler).complete("s", "u", SCHEMA).text == '{"a":"ok"}'
    assert len(calls) == 2


def test_persistent_empty_response_gives_up():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_completion(content=""))

    with pytest.raises(LLMError, match="non ha risposto"):
        _provider(handler).complete("s", "u", SCHEMA)


def test_truncated_response_is_retried_once_with_a_higher_limit_and_paid_for():
    limits = []

    def handler(request: httpx.Request) -> httpx.Response:
        limits.append(json.loads(request.content)["max_tokens"])
        if len(limits) == 1:
            return httpx.Response(200, json=_completion(content="", finish_reason="length"))
        return httpx.Response(200, json=_completion())

    response = _provider(handler).complete("s", "u", SCHEMA)

    assert limits == [MAX_OUTPUT_TOKENS, RETRY_OUTPUT_TOKENS]
    assert response.text == '{"a":"ok"}'
    assert response.cost == pytest.approx(0.0246)  # si pagano entrambi i tentativi
    assert (response.input_tokens, response.output_tokens) == (10, 6)


def test_truncated_twice_gives_up_and_reports_reasoning_tokens():
    limits = []

    def handler(request: httpx.Request) -> httpx.Response:
        limits.append(json.loads(request.content)["max_tokens"])
        body = _completion(content="", finish_reason="length")
        body["usage"]["completion_tokens_details"] = {"reasoning_tokens": 63_000}
        return httpx.Response(200, json=body)

    with pytest.raises(LLMError, match="di cui 63000 per ragionare"):
        _provider(handler).complete("s", "u", SCHEMA)
    assert len(limits) == 2


def test_no_retry_on_truncation_when_the_model_limit_is_already_reached():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(200, json=_completion(content="", finish_reason="length"))

    provider = _provider(handler)
    provider.max_output_tokens = provider.retry_output_tokens = 4096
    with pytest.raises(LLMError, match="4096"):
        provider.complete("s", "u", SCHEMA)
    assert len(calls) == 1


@pytest.mark.parametrize(("effort", "expected"), [("low", {"effort": "low"}), (None, None)])
def test_reasoning_effort_is_sent_only_when_set(effort, expected):
    bodies = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json=_completion())

    provider = _provider(handler)
    provider.reasoning_effort = effort
    provider.complete("s", "u", SCHEMA)
    assert bodies[0].get("reasoning") == expected
    assert bodies[0]["provider"] == {"require_parameters": True}


def test_reasoning_effort_also_applies_without_structured_outputs():
    bodies = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        if "response_format" in bodies[-1]:
            return httpx.Response(400, json={"error": {"code": 400, "message": "no"}})
        return httpx.Response(200, json=_completion())

    provider = _provider(handler)
    provider.reasoning_effort = "low"
    provider.complete("s", "u", SCHEMA)
    assert bodies[1]["reasoning"] == {"effort": "low"}
    assert "provider" not in bodies[1]


def test_cache_is_kept_when_reasoning_or_limits_change(tmp_path):
    """Le risposte già pagate restano valide: non si rigenera ciò che è pronto."""
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(200, json=_completion())

    class Answer(BaseModel):
        a: str

    cache = ResponseCache(tmp_path)
    before = _provider(handler)
    StructuredLLM(before, cache).generate("s", "u", Answer)
    after = _provider(handler)
    after.reasoning_effort = "low"
    after.max_output_tokens = 1
    StructuredLLM(after, cache).generate("s", "u", Answer)
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("status", "message"),
    [
        (401, "Chiave OpenRouter"),
        (402, "Credito"),
        (404, "Modello non trovato"),
        (429, "cache"),
        (500, "500"),
    ],
)
def test_api_errors_are_explained(status, message):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"error": {"code": status, "message": "boom"}})

    with pytest.raises(LLMError, match=message):
        _provider(handler).complete("s", "u", SCHEMA)


def test_missing_key_is_explained():
    with pytest.raises(LLMError, match="OPENROUTER_API_KEY"):
        OpenRouterProvider("x/y", None)


def test_default_model_comes_from_env_and_can_be_any_openrouter_id(monkeypatch):
    monkeypatch.setenv("BOOKPACK_MODEL", "mistralai/qualcosa")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-env")
    settings = load_settings()
    assert settings.model == "mistralai/qualcosa"
    assert settings.api_key == "sk-or-env"
    assert load_settings("google/altro").model == "google/altro"


def test_output_limit_follows_the_model():
    settings = load_settings("x/y")
    settings.api_key = "k"
    info = ModelInfo("x/y", "X", 1.0, 2.0, 100_000, 4096, True, ("high", "low"))
    provider = get_provider(settings, info)
    assert isinstance(provider, OpenRouterProvider)
    assert provider.max_output_tokens == 4096
    assert provider.retry_output_tokens == 4096
    assert provider.reasoning_effort == "low"


def test_without_catalog_data_the_model_defaults_apply():
    settings = load_settings("x/y")
    settings.api_key = "k"
    provider = get_provider(settings)
    assert provider.max_output_tokens == MAX_OUTPUT_TOKENS
    assert provider.retry_output_tokens == RETRY_OUTPUT_TOKENS
    assert provider.reasoning_effort is None


def test_fake_needs_no_key():
    settings = load_settings(fake=True)
    settings.api_key = None
    assert isinstance(get_provider(settings), FakeProvider)
