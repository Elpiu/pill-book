"""Provider LLM con output strutturato."""

from ..config import Settings
from .base import MAX_OUTPUT_TOKENS, RETRY_OUTPUT_TOKENS, LLMError, LLMProvider
from .catalog import ModelInfo


def get_provider(settings: Settings, info: ModelInfo | None = None) -> LLMProvider:
    if settings.fake:
        from .fake import FakeProvider

        return FakeProvider(settings.model)

    from .openrouter import OpenRouterProvider

    max_output, retry_output = MAX_OUTPUT_TOKENS, RETRY_OUTPUT_TOKENS
    if info and info.max_output:
        max_output = min(max_output, info.max_output)
        retry_output = min(retry_output, info.max_output)
    return OpenRouterProvider(
        settings.model,
        settings.api_key,
        max_output,
        retry_output,
        info.reasoning_effort if info else None,
    )


__all__ = ["LLMError", "LLMProvider", "get_provider"]
