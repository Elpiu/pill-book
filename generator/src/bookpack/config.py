"""Configurazione da ambiente e file .env."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_DIR / ".env"
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "out"
DEFAULT_CACHE_DIR = PROJECT_DIR / ".bookpack-cache"

# Qualsiasi id del catalogo di OpenRouter: si cambia con BOOKPACK_MODEL o --model
DEFAULT_MODEL = "anthropic/claude-sonnet-5.5"
FAKE_MODEL = "fake-1"
# Sopra questa soglia un capitolo passa dal map-reduce invece che da una chiamata unica
DEFAULT_CONTEXT_TOKENS = 40_000
# Quante chiamate all'LLM insieme: si abbassa con BOOKPACK_WORKERS o --workers se il provider limita
DEFAULT_WORKERS = 4


class ConfigError(Exception):
    pass


@dataclass
class Settings:
    model: str
    api_key: str | None
    fake: bool
    cache_dir: Path
    context_tokens: int
    workers: int


def load_settings(model: str | None = None, fake: bool = False) -> Settings:
    load_dotenv(ENV_PATH)
    load_dotenv()

    raw_context = os.getenv("BOOKPACK_CONTEXT_TOKENS") or str(DEFAULT_CONTEXT_TOKENS)
    if not raw_context.isdigit():
        raise ConfigError(f"BOOKPACK_CONTEXT_TOKENS deve essere un numero: {raw_context}")
    raw_workers = os.getenv("BOOKPACK_WORKERS") or str(DEFAULT_WORKERS)
    if not raw_workers.isdigit() or int(raw_workers) < 1:
        raise ConfigError(f"BOOKPACK_WORKERS deve essere un numero da 1 in su: {raw_workers}")

    return Settings(
        model=FAKE_MODEL if fake else model or os.getenv("BOOKPACK_MODEL") or DEFAULT_MODEL,
        api_key=os.getenv("OPENROUTER_API_KEY") or None,
        fake=fake,
        cache_dir=Path(os.getenv("BOOKPACK_CACHE_DIR") or DEFAULT_CACHE_DIR),
        context_tokens=int(raw_context),
        workers=int(raw_workers),
    )
