"""Provider OpenRouter: qualsiasi modello del catalogo, tramite la sua API compatibile con OpenAI."""

import json
import re
import time

import openai

from .base import MAX_OUTPUT_TOKENS, RETRY_OUTPUT_TOKENS, LLMError, LLMProvider, LLMResponse
from .catalog import OPENROUTER_BASE_URL

# Risposte vuote o errori con stato 200: capitano mentre un modello si scalda o cambia provider
_TRANSIENT_ATTEMPTS = 3
_TRANSIENT_DELAY_SECONDS = 3
_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.S)


class _TransientError(Exception):
    pass


class _TruncatedError(Exception):
    def __init__(self, spent: LLMResponse, reasoning_tokens: int | None) -> None:
        super().__init__("risposta troncata")
        self.spent = spent
        self.reasoning_tokens = reasoning_tokens


def _usage_of(response, text: str = "") -> LLMResponse:
    usage = response.usage
    return LLMResponse(
        text=text,
        input_tokens=(usage.prompt_tokens or 0) if usage else 0,
        output_tokens=(usage.completion_tokens or 0) if usage else 0,
        cost=getattr(usage, "cost", None),
    )


def _add_spent(total: LLMResponse, spent: LLMResponse) -> None:
    """Un tentativo troncato si paga: resta nel conto della risposta finale."""
    total.input_tokens += spent.input_tokens
    total.output_tokens += spent.output_tokens
    if spent.cost is not None:
        total.cost = (total.cost or 0.0) + spent.cost


def _extract_json(text: str) -> str:
    """I modelli senza output strutturato a volte avvolgono il JSON in un blocco di codice."""
    text = text.strip()
    if text.startswith("{"):
        return text
    if match := _JSON_FENCE.search(text):
        return match.group(1)
    start, end = text.find("{"), text.rfind("}")
    return text[start : end + 1] if 0 <= start < end else text


def _error_message(error: object) -> str:
    if isinstance(error, dict):
        return str(error.get("message") or error)
    return str(error)


class OpenRouterProvider(LLMProvider):
    name = "openrouter"

    def __init__(
        self,
        model: str,
        api_key: str | None,
        max_output_tokens: int = MAX_OUTPUT_TOKENS,
        retry_output_tokens: int = RETRY_OUTPUT_TOKENS,
        reasoning_effort: str | None = None,
    ) -> None:
        if not api_key:
            raise LLMError(
                "Manca OPENROUTER_API_KEY: creala su https://openrouter.ai/keys e mettila nel "
                "file generator/.env"
            )
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.retry_output_tokens = retry_output_tokens
        self.reasoning_effort = reasoning_effort
        self.structured = True
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            default_headers={"X-Title": "Bookpack"},
            max_retries=3,
        )

    def _create(self, messages: list[dict], limit: int, body: dict | None = None, **extra: object):
        options = dict(body or {})
        if self.reasoning_effort:
            options["reasoning"] = {"effort": self.reasoning_effort}
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=limit,
            extra_body=options,
            **extra,
        )

    def _request(self, system: str, user: str, schema: dict, limit: int):
        messages = [{"role": "user", "content": user}]
        if self.structured:
            try:
                return self._create(
                    [{"role": "system", "content": system}, *messages],
                    limit,
                    # Solo provider che rispettano davvero lo schema
                    {"provider": {"require_parameters": True}},
                    response_format={
                        "type": "json_schema",
                        "json_schema": {"name": "output", "strict": True, "schema": schema},
                    },
                )
            except openai.APIStatusError as exc:
                if exc.status_code not in (400, 404, 503):
                    raise
                # Nessun provider lo supporta: si chiede il JSON nel prompt e la validazione
                # locale, con i suoi ritentativi, resta a garantire il risultato
                self.structured = False
        plain_system = (
            f"{system}\n\nRespond only with a JSON object matching this schema, with no other "
            f"text:\n{json.dumps(schema, ensure_ascii=False)}"
        )
        return self._create([{"role": "system", "content": plain_system}, *messages], limit)

    def _parse(self, response) -> LLMResponse:
        if error := getattr(response, "error", None):
            raise _TransientError(_error_message(error))
        if not response.choices:
            raise _TransientError("risposta senza contenuto")
        choice = response.choices[0]
        if choice.finish_reason == "error":
            raise _TransientError(_error_message(getattr(choice, "error", "errore del provider")))
        if choice.finish_reason == "length":
            details = getattr(response.usage, "completion_tokens_details", None)
            raise _TruncatedError(_usage_of(response), getattr(details, "reasoning_tokens", None))
        if refusal := getattr(choice.message, "refusal", None):
            raise LLMError(f"Il modello {self.model} ha rifiutato la richiesta: {refusal}")
        if not choice.message.content:
            raise _TransientError("risposta vuota")
        return _usage_of(response, _extract_json(choice.message.content))

    def _truncated_message(self, limit: int, reasoning_tokens: int | None) -> str:
        spent = f", di cui {reasoning_tokens} per ragionare" if reasoning_tokens else ""
        return (
            f"Risposta troncata: {self.model} ha esaurito {limit} token di output{spent}. "
            "Le risposte già ottenute sono in cache: rilancia, oppure prova un altro modello."
        )

    def _complete_with_retries(self, system: str, user: str, schema: dict) -> LLMResponse:
        limit = self.max_output_tokens
        spent = LLMResponse("")
        failures = 0
        while True:
            try:
                response = self._parse(self._request(system, user, schema, limit))
                _add_spent(response, spent)
                return response
            except _TruncatedError as exc:
                if limit >= self.retry_output_tokens:
                    raise LLMError(self._truncated_message(limit, exc.reasoning_tokens)) from exc
                _add_spent(spent, exc.spent)
                limit = self.retry_output_tokens
            except _TransientError as exc:
                failures += 1
                if failures >= _TRANSIENT_ATTEMPTS:
                    raise LLMError(f"Il modello {self.model} non ha risposto: {exc}") from exc
                time.sleep(_TRANSIENT_DELAY_SECONDS)

    def complete(self, system: str, user: str, schema: dict) -> LLMResponse:
        try:
            return self._complete_with_retries(system, user, schema)
        except openai.AuthenticationError as exc:
            raise LLMError(
                "Chiave OpenRouter non valida: controlla OPENROUTER_API_KEY", fatal=True
            ) from exc
        except openai.NotFoundError as exc:
            raise LLMError(f"Modello non trovato su OpenRouter: {self.model}", fatal=True) from exc
        except openai.RateLimitError as exc:
            raise LLMError(
                "Limite di richieste raggiunto anche dopo i ritentativi. Riprendi più tardi, con "
                "meno chiamate insieme: quelle già fatte sono in cache.",
                fatal=True,
            ) from exc
        except openai.APIStatusError as exc:
            if exc.status_code == 402:
                raise LLMError(
                    f"Credito OpenRouter insufficiente ({exc.message}). Ricarica e rilancia: le "
                    "chiamate già fatte sono in cache.",
                    fatal=True,
                ) from exc
            raise LLMError(f"Errore da OpenRouter ({exc.status_code}): {exc.message}") from exc
        except openai.APIConnectionError as exc:
            raise LLMError(f"Connessione a OpenRouter fallita: {exc}", fatal=True) from exc
