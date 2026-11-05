import os
import time

from typer.testing import CliRunner

from bookpack.cli import app
from bookpack.condense.estimate import estimate_build
from bookpack.extract.toc import Section
from bookpack.llm import catalog
from bookpack.llm.catalog import (
    context_budget,
    find_model,
    load_catalog,
    parse_catalog,
    search_models,
    suggest_models,
)
from conftest import CATALOG


def test_parse_converts_prices_and_skips_non_text_models():
    models = parse_catalog(CATALOG)
    assert [model.id for model in models] == ["test/buono", "test/piccolo", "openrouter/auto"]
    good = find_model(models, "test/buono")
    assert good.prices == (2.0, 10.0)
    assert good.structured is True
    assert good.max_output == 8000


def test_low_reasoning_only_for_models_that_declare_it():
    models = parse_catalog(CATALOG)
    assert find_model(models, "test/buono").reasoning_effort == "low"
    assert find_model(models, "test/piccolo").reasoning_effort is None
    only_high_or_none = {
        "data": [{"id": "a/b", "reasoning": {"supported_efforts": ["xhigh", "high", "none"]}}]
    }
    assert parse_catalog(only_high_or_none)[0].reasoning_effort is None


def test_variable_prices_are_unknown():
    assert find_model(parse_catalog(CATALOG), "openrouter/auto").prices is None


def test_catalog_is_cached_and_refreshed_when_old(tmp_path, monkeypatch):
    calls = []

    def fetch():
        calls.append(1)
        return CATALOG

    monkeypatch.setattr(catalog, "_fetch", fetch)
    assert load_catalog(tmp_path)
    assert load_catalog(tmp_path)
    assert len(calls) == 1

    old = time.time() - catalog.CATALOG_MAX_AGE_SECONDS - 10
    os.utime(tmp_path / "openrouter-models.json", (old, old))
    load_catalog(tmp_path)
    assert len(calls) == 2


def test_offline_uses_old_copy_or_nothing(tmp_path, monkeypatch):
    def offline():
        raise OSError("niente rete")

    monkeypatch.setattr(catalog, "_fetch", offline)
    assert load_catalog(tmp_path) == []

    monkeypatch.setattr(catalog, "_fetch", lambda: CATALOG)
    load_catalog(tmp_path)
    monkeypatch.setattr(catalog, "_fetch", offline)
    assert load_catalog(tmp_path, refresh=True)


def test_search_and_suggestions():
    models = parse_catalog(CATALOG)
    assert [m.id for m in search_models(models, "BUONO")] == ["test/buono"]
    assert "test/buono" in suggest_models(models, "test/buon")


def test_budget_shrinks_for_small_models():
    models = parse_catalog(CATALOG)
    assert context_budget(40_000, find_model(models, "test/buono")) == 40_000
    assert context_budget(40_000, find_model(models, "test/piccolo")) == 6_000
    assert context_budget(40_000, None) == 40_000


def test_estimate_uses_prices_when_known():
    section = Section("Capitolo", 1, 1)
    pages = {1: "parola " * 500}
    assert estimate_build([section], pages, None, 40_000).cost is None
    assert estimate_build([section], pages, (2.0, 10.0), 40_000).cost > 0


def test_models_command_lists_and_filters():
    result = CliRunner().invoke(app, ["models", "buono"])
    assert result.exit_code == 0, result.output
    assert "test/buono" in result.output
    assert "test/piccolo" not in result.output
    assert "$2.00" in result.output


def test_inspect_uses_catalog_prices(pdf_with_outline):
    result = CliRunner().invoke(app, ["inspect", str(pdf_with_outline), "--model", "test/buono"])
    assert result.exit_code == 0, result.output
    assert "n/d" not in result.output
    assert "$" in result.output


def test_unknown_model_is_rejected_with_a_hint(pdf_with_outline):
    result = CliRunner().invoke(app, ["inspect", str(pdf_with_outline), "--model", "test/buon"])
    assert result.exit_code == 1
    assert "non è nel catalogo" in result.output
    assert "test/buono" in result.output
