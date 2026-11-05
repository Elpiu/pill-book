from pathlib import Path

import pytest
from typer.testing import CliRunner

from bookpack.cli import app
from bookpack.extract.clean import clean_pages, find_repeated_lines
from bookpack.extract.pdf import Line, Page, PdfError, open_pdf
from bookpack.extract.toc import (
    Section,
    TocError,
    detect_chapters,
    find_overlaps,
    read_toc_file,
    set_section_pages,
    write_toc_file,
)

REPO = Path(__file__).resolve().parents[2]
SAMPLE_PDF = REPO / "samples" / "how-to-live-on-24-hours-a-day.pdf"


def make_page(number: int, *texts: str) -> Page:
    return Page(number, [Line(text, 11, False, 0.5) for text in texts])


def test_outline_detection(pdf_with_outline):
    detection = detect_chapters(open_pdf(pdf_with_outline))
    assert detection.method == "outline"
    assert [s.title for s in detection.chapters] == [f"Capitolo {i}: tema {i}" for i in range(1, 5)]
    first = detection.chapters[0]
    assert (first.page_start, first.page_end) == (3, 6)


def test_heading_detection_without_outline(pdf_without_outline):
    detection = detect_chapters(open_pdf(pdf_without_outline))
    assert detection.method == "headings"
    assert [s.page_start for s in detection.chapters] == [3, 7, 11, 15]


def test_useless_sections_are_excluded_unless_asked(pdf_with_outline):
    doc = open_pdf(pdf_with_outline)
    excluded = [s.title for s in detect_chapters(doc).sections if s.excluded]
    assert excluded == ["Copyright", "Bibliografia"]
    assert len(detect_chapters(doc, include_all=True).chapters) == 6


def test_outline_prefers_level_with_chapters_over_parts():
    from bookpack.extract.pdf import OutlineEntry, PdfDocument
    from bookpack.extract.toc import from_outline

    outline = [OutlineEntry(1, f"Parte {p}", 1 + (p - 1) * 300) for p in (1, 2, 3)]
    full = []
    for part, entry in enumerate(outline):
        full.append(entry)
        full += [OutlineEntry(2, f"Cap {part}.{c}", entry.page + c * 30) for c in range(9)]
    doc = PdfDocument(Path("x.pdf"), None, None, [Page(i + 1) for i in range(900)], full)
    sections = from_outline(doc)
    assert sections and sections[0].title == "Cap 0.0"
    assert len(sections) == 27


def test_toc_file_round_trip_overrides_detection(pdf_with_outline, tmp_path):
    doc = open_pdf(pdf_with_outline)
    path = tmp_path / "libro.toc.yaml"
    write_toc_file(doc, detect_chapters(doc), path)
    assert "Capitolo 1" in path.read_text("utf-8")

    path.write_text(
        "book: {title: Altro titolo}\nchapters:\n"
        "- {title: Primo, pageStart: 3, pageEnd: 10}\n"
        "- {title: Secondo, pageStart: 11, pageEnd: 18, exclude: true}\n",
        "utf-8",
    )
    detection = detect_chapters(doc, path)
    assert detection.method == "file"
    assert detection.book["title"] == "Altro titolo"
    assert [s.title for s in detection.chapters] == ["Primo"]


@pytest.mark.parametrize(
    "body",
    [
        "foo: bar",
        "chapters:\n- {title: A, pageStart: 5, pageEnd: 2}",
        "chapters:\n- {title: A, pageStart: 1, pageEnd: 9999}",
        "chapters:\n- {title: A}",
        "chapters:\n- {title: A, pageStart: 1, pageEnd: 2, exclude: true}",
    ],
)
def test_invalid_toc_file_is_rejected(tmp_path, body):
    path = tmp_path / "bad.yaml"
    path.write_text(body, "utf-8")
    with pytest.raises(TocError):
        read_toc_file(path, 100)


def test_scanned_pdf_is_rejected(tmp_path):
    import pymupdf

    path = tmp_path / "scan.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(path)
    with pytest.raises(PdfError, match="scansione"):
        open_pdf(path)


def test_headers_and_footers_are_removed():
    texts = ["Alfa", "Beta", "Gamma", "Delta", "Epsilon"]
    pages = [
        make_page(
            n, "IL MIO LIBRO", str(n), texts[n - 1], "Riga centrale " + texts[n - 1], f"Pagina {n}"
        )
        for n in range(1, 6)
    ]
    clean = clean_pages(pages)
    assert clean[3] == "Gamma\nRiga centrale Gamma"


def test_page_numbers_are_removed_even_if_not_repeated():
    clean = clean_pages([make_page(1, "12", "Testo centrale.", "Altro testo.", "- 12 -")])
    assert clean[1] == "Testo centrale.\nAltro testo."


def test_chapter_labels_are_not_treated_as_headers():
    pages = [
        make_page(n, f"Capitolo {n}", "Corpo.", "Corpo due.", "Corpo tre.") for n in range(1, 6)
    ]
    raw = [[line.text for line in page.lines] for page in pages]
    assert "capitolo #" not in find_repeated_lines(raw)


def test_hyphenation_and_spaces():
    clean = clean_pages([make_page(1, "uno", "una par-", "ola    con  spazi", "fine")])
    assert "parola con spazi" in clean[1]


def test_hyphenation_keeps_real_hyphens_before_capitals():
    clean = clean_pages([make_page(1, "uno", "anglo-", "Saxon", "fine")])
    assert "anglo-\nSaxon" in clean[1]


def test_hyphenation_across_pages():
    clean = clean_pages(
        [
            make_page(1, "uno", "due", "tre", "fine della par-"),
            make_page(2, "ola, poi il resto", "due", "tre", "quattro"),
        ]
    )
    assert clean[1].endswith("fine della parola,")
    assert clean[2].startswith("poi il resto")


def test_inspect_gutenberg_pdf_shows_correct_chapters():
    result = CliRunner().invoke(app, ["inspect", str(SAMPLE_PDF)])
    assert result.exit_code == 0, result.output
    doc = open_pdf(SAMPLE_PDF)
    detection = detect_chapters(doc)
    assert detection.method == "headings"
    assert [s.title for s in detection.chapters][1:] == [
        "The Daily Miracle",
        "The Desire To Exceed One's Programme",
        "Precautions Before Beginning",
        "The Cause Of The Troubles",
        "Tennis And The Immortal Soul",
        "Remember Human Nature",
        "Controlling The Mind",
        "The Reflective Mood",
        "Interest In The Arts",
        "Nothing In Life Is Humdrum",
        "Serious Reading",
        "Dangers To Avoid",
    ]
    assert "The Daily Miracle" in result.output


def test_toc_command_writes_yaml(pdf_with_outline, tmp_path):
    output = tmp_path / "out.yaml"
    result = CliRunner().invoke(app, ["toc", str(pdf_with_outline), "-o", str(output)])
    assert result.exit_code == 0, result.output
    assert read_toc_file(output, 100).chapters


def three_sections() -> list[Section]:
    return [Section("A", 1, 10), Section("B", 11, 20), Section("C", 21, 30)]


def test_moving_a_boundary_moves_the_adjacent_neighbours():
    sections = three_sections()
    set_section_pages(sections, 1, 13, 18, 100)
    assert (sections[0].page_end, sections[2].page_start) == (12, 19)


def test_moving_a_boundary_inside_a_neighbour_trims_it():
    sections = three_sections()
    set_section_pages(sections, 1, 5, 25, 100)
    assert (sections[0].page_start, sections[0].page_end) == (1, 4)
    assert (sections[2].page_start, sections[2].page_end) == (26, 30)


def test_gaps_between_sections_are_kept():
    sections = [Section("A", 1, 5), Section("B", 11, 20), Section("C", 25, 30)]
    set_section_pages(sections, 1, 12, 19, 100)
    assert sections[0].page_end == 5
    assert sections[2].page_start == 25


def test_neighbour_never_ends_up_with_an_invalid_range():
    sections = three_sections()
    set_section_pages(sections, 1, 1, 40, 100)
    assert sections[0].page_start <= sections[0].page_end
    assert sections[2].page_start <= sections[2].page_end
    assert find_overlaps(sections) == {0, 1, 2}


def test_only_the_changed_side_moves_the_neighbour():
    sections = three_sections()
    set_section_pages(sections, 1, 11, 25, 100)
    assert sections[0].page_end == 10
    assert sections[2].page_start == 26


@pytest.mark.parametrize(("start", "end"), [(0, 5), (5, 4), (1, 101)])
def test_invalid_pages_are_rejected_without_changes(start, end):
    sections = three_sections()
    with pytest.raises(TocError):
        set_section_pages(sections, 1, start, end, 100)
    assert (sections[1].page_start, sections[1].page_end) == (11, 20)


def test_overlaps_ignore_excluded_sections():
    sections = [Section("A", 1, 10), Section("B", 5, 15, excluded=True), Section("C", 16, 20)]
    assert find_overlaps(sections) == set()
    sections[1].excluded = False
    assert find_overlaps(sections) == {0, 1}


def test_saving_keeps_book_data_from_the_opened_file(pdf_with_outline, tmp_path):
    doc = open_pdf(pdf_with_outline)
    source = tmp_path / "in.yaml"
    source.write_text(
        "book: {id: mio-id, title: Mio titolo, lang: it}\n"
        "chapters:\n- {title: A, pageStart: 3, pageEnd: 6}\n",
        "utf-8",
    )
    target = tmp_path / "out.yaml"
    write_toc_file(doc, read_toc_file(source, doc.page_count), target)
    reread = read_toc_file(target, doc.page_count)
    assert reread.book["id"] == "mio-id"
    assert reread.book["title"] == "Mio titolo"
    assert reread.book["lang"] == "it"
