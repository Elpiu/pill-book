"""Lettura del PDF: testo per pagina, righe con informazioni di font, metadati e outline."""

from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

# Con i flag di default PyMuPDF conserva le legature (fi, fl) come caratteri singoli
_TEXT_FLAGS = pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_LIGATURES
_BOLD_FLAG = 16
# Sotto questa media di caratteri per pagina il PDF è probabilmente una scansione
MIN_CHARS_PER_PAGE = 100


class PdfError(Exception):
    pass


@dataclass
class Line:
    text: str
    size: float
    bold: bool
    y: float  # posizione verticale relativa nella pagina, da 0 a 1
    block_end: bool = False


@dataclass
class Page:
    number: int  # numero fisico nel PDF, a partire da 1
    lines: list[Line] = field(default_factory=list)


@dataclass
class OutlineEntry:
    level: int
    title: str
    page: int


@dataclass
class PdfDocument:
    path: Path
    title: str | None
    author: str | None
    pages: list[Page]
    outline: list[OutlineEntry]

    @property
    def page_count(self) -> int:
        return len(self.pages)


def _read_page(page: pymupdf.Page, number: int) -> Page:
    result = Page(number=number)
    height = page.rect.height or 1
    data = page.get_text("dict", flags=_TEXT_FLAGS)
    for block in data["blocks"]:
        if block.get("type") != 0:
            continue
        for raw in block["lines"]:
            spans = [span for span in raw["spans"] if span["text"].strip()]
            if not spans:
                continue
            text = "".join(span["text"] for span in raw["spans"]).strip()
            size = max(span["size"] for span in spans)
            bold = all(
                span["flags"] & _BOLD_FLAG or "bold" in span["font"].lower() for span in spans
            )
            result.lines.append(Line(text, round(size, 1), bold, raw["bbox"][1] / height))
        if result.lines:
            result.lines[-1].block_end = True
    return result


def open_pdf(path: Path) -> PdfDocument:
    try:
        doc = pymupdf.open(path)
    except Exception as exc:
        raise PdfError(f"Impossibile aprire {path}: {exc}") from exc

    with doc:
        if doc.needs_pass:
            raise PdfError(f"{path} è protetto da password")
        pages = [_read_page(page, i + 1) for i, page in enumerate(doc)]
        metadata = doc.metadata or {}
        outline = [
            OutlineEntry(level, title.strip(), page)
            for level, title, page, *_ in doc.get_toc(simple=False)
            if title.strip() and page >= 1
        ]

    total_chars = sum(len(line.text) for page in pages for line in page.lines)
    if total_chars < MIN_CHARS_PER_PAGE * max(len(pages), 1):
        raise PdfError(
            f"{path} contiene pochissimo testo ({total_chars} caratteri su {len(pages)} pagine): "
            "sembra una scansione. Serve prima un passaggio OCR."
        )

    return PdfDocument(
        path=path,
        title=(metadata.get("title") or "").strip() or None,
        author=(metadata.get("author") or "").strip() or None,
        pages=pages,
        outline=outline,
    )
