import copy
import json
from pathlib import Path

from typer.testing import CliRunner

from bookpack.cli import app
from bookpack.models import export_schema
from bookpack.validate import mindmap_stats, validate_data

REPO = Path(__file__).resolve().parents[2]
SAMPLE = REPO / "samples" / "sample.bookpack.json"


def errors_of(data: dict) -> list[str]:
    return validate_data(data)[1].errors


def test_valid_pack_passes(valid_pack):
    assert errors_of(valid_pack) == []


def test_too_many_cards_fails(valid_pack):
    cards = valid_pack["chapters"][0]["cards"]
    takeaway = cards.pop()
    for i in range(5, 201):
        cards.append({"id": f"ch-01-c{i:02d}", "type": "concept", "body": "Idea.", "page": 2})
    takeaway["id"] = "ch-01-c201"
    cards.append(takeaway)
    assert errors_of(valid_pack)


def test_long_chapters_can_have_many_cards(valid_pack):
    cards = valid_pack["chapters"][0]["cards"]
    takeaway = cards.pop()
    for i in range(5, 40):
        cards.append({"id": f"ch-01-c{i:02d}", "type": "concept", "body": "Idea.", "page": 2})
    takeaway["id"] = "ch-01-c40"
    cards.append(takeaway)
    assert errors_of(valid_pack) == []


def test_too_few_flashcards_fails(valid_pack):
    valid_pack["chapters"][0]["flashcards"].pop()
    assert errors_of(valid_pack)


def test_long_body_fails_and_slightly_long_warns(valid_pack):
    data = copy.deepcopy(valid_pack)
    data["chapters"][0]["cards"][0]["body"] = "parola " * 100
    assert any("body" in error for error in errors_of(data))

    data["chapters"][0]["cards"][0]["body"] = "parola " * 65
    _, report = validate_data(data)
    assert report.ok and any("body" in warning for warning in report.warnings)


def test_duplicate_ids_fail(valid_pack):
    cards = valid_pack["chapters"][0]["cards"]
    cards[1]["id"] = cards[0]["id"]
    assert any("duplicato" in error for error in errors_of(valid_pack))


def test_last_card_must_be_takeaway(valid_pack):
    cards = valid_pack["chapters"][0]["cards"]
    cards[-1] = {"id": cards[-1]["id"], "type": "concept", "body": "Idea.", "page": 2}
    assert any("takeaway" in error for error in errors_of(valid_pack))


def test_quote_limits(valid_pack):
    cards = valid_pack["chapters"][0]["cards"]
    cards[0].update(type="quote", body="parola " * 30)
    assert any("citazione" in error for error in errors_of(valid_pack))

    cards[0]["body"] = "breve"
    cards[1].update(type="quote", body="breve")
    assert any("citazioni" in error for error in errors_of(valid_pack))


def test_details_limit(valid_pack):
    card = valid_pack["chapters"][0]["cards"][0]
    card["details"] = "parola " * 120
    assert errors_of(valid_pack) == []
    card["details"] = "parola " * 200
    assert any("details" in error for error in errors_of(valid_pack))


def test_check_needs_an_answer_and_answer_needs_a_check(valid_pack):
    cards = valid_pack["chapters"][0]["cards"]
    cards[0].update(type="check", body="Perché?")
    assert any("risposta" in error for error in errors_of(valid_pack))
    cards[0]["answer"] = "Perché sì."
    assert errors_of(valid_pack) == []
    cards[1]["answer"] = "Non c'entra."
    assert any("answer" in error for error in errors_of(valid_pack))


def test_procedure_needs_steps(valid_pack):
    cards = valid_pack["chapters"][0]["cards"]
    cards[0].update(type="procedure", title="Come si fa")
    assert any("passi" in error for error in errors_of(valid_pack))
    cards[0]["steps"] = ["Primo passo", "Secondo passo"]
    cards[0]["code"] = "ls -la"
    assert errors_of(valid_pack) == []
    cards[0]["code"] = "riga\n" * 40
    assert any("codice" in error for error in errors_of(valid_pack))
    del cards[0]["code"]
    cards[1]["steps"] = ["Fuori posto", "Anche questo"]
    assert any("steps" in error for error in errors_of(valid_pack))


def test_section_card_needs_title_but_no_page(valid_pack):
    card = valid_pack["chapters"][0]["cards"][0]
    del card["page"]
    card.update(type="section", body="Cosa vedremo.")
    assert any("titolo" in error for error in errors_of(valid_pack))
    card["title"] = "Prima parte"
    assert errors_of(valid_pack) == []


def test_summary_is_required_and_bounded(valid_pack):
    chapter = valid_pack["chapters"][0]
    chapter["summary"] = "troppo breve"
    assert any("riassunto" in error for error in errors_of(valid_pack))
    chapter["summary"] = "parola " * 1000
    assert any("riassunto" in error for error in errors_of(valid_pack))
    del chapter["summary"]
    assert errors_of(valid_pack)


def test_v1_packs_are_rejected(valid_pack):
    valid_pack["schemaVersion"] = 1
    assert errors_of(valid_pack)


def test_page_outside_chapter_fails(valid_pack):
    valid_pack["chapters"][0]["cards"][0]["page"] = 9
    assert any("fuori dal capitolo" in error for error in errors_of(valid_pack))


def test_missing_page_fails_except_takeaway(valid_pack):
    del valid_pack["chapters"][0]["cards"][0]["page"]
    assert any("pagina di origine" in error for error in errors_of(valid_pack))


def test_mindmap_depth():
    assert mindmap_stats("# A\n## B\n- C\n  - D") == (4, 4)
    assert mindmap_stats("# A\n## B\n- C\n  - D\n    - E")[0] == 5


def test_deep_mindmap_fails(valid_pack):
    valid_pack["chapters"][0]["mindmap"] = "# A\n## B\n- C\n  - D\n    - E"
    assert any("profondità" in error for error in errors_of(valid_pack))


def test_wrong_schema_version_fails(valid_pack):
    valid_pack["schemaVersion"] = 3
    assert errors_of(valid_pack)


def test_sample_pack_is_valid():
    result = CliRunner().invoke(app, ["validate", str(SAMPLE)])
    assert result.exit_code == 0, result.output


def test_committed_schema_is_up_to_date():
    committed = json.loads((REPO / "schema" / "bookpack.schema.json").read_text("utf-8"))
    assert committed == export_schema()
