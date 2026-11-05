"""Prompt LLM versionati in file .md. Segnaposto: {{nome}}."""

from pathlib import Path

_DIRECTORY = Path(__file__).parent


def render(name: str, **values: str) -> str:
    text = (_DIRECTORY / f"{name}.md").read_text("utf-8")
    for key, value in values.items():
        text = text.replace(f"{{{{{key}}}}}", value)
    return text.strip()
