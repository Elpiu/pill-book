"""Impagina un testo Project Gutenberg in un PDF d'esempio, senza outline.

Serve ad avere in `samples/` un PDF di pubblico dominio con header ripetuti, numeri di pagina e
titoli riconoscibili solo dal font: il caso più difficile per il rilevamento dei capitoli.

    uv run --project ../generator python make_sample_pdf.py pg2274.txt how-to-live-on-24-hours-a-day.pdf
"""

import re
import sys
from pathlib import Path

import pymupdf

TITLE = "How to Live on Twenty-Four Hours a Day"
AUTHOR = "Arnold Bennett"
PAGE = pymupdf.paper_rect("a5")
MARGIN = 48
BODY_SIZE = 10.5
LEADING = 15
CONTENT_WIDTH = PAGE.width - 2 * MARGIN
TOP = MARGIN + 18
BOTTOM = PAGE.height - MARGIN - 8
ROMAN = re.compile(r"^[IVX]+$")


def body_of(text: str) -> str:
    start = text.index("*** START OF")
    end = text.index("*** END OF")
    body = text[text.index("\n", start) + 1 : end]
    body = body[: body.index("End of Project Gutenberg")]
    return body[body.index("PREFACE TO THIS EDITION") :]


def paragraphs(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


class Layout:
    def __init__(self) -> None:
        self.doc = pymupdf.open()
        self.page = None
        self.y = 0.0
        self.font = pymupdf.Font("helv")

    def new_page(self) -> None:
        self.page = self.doc.new_page(width=PAGE.width, height=PAGE.height)
        number = self.doc.page_count
        self.page.insert_text((MARGIN, MARGIN), TITLE.upper(), fontsize=7.5, fontname="helv")
        self.page.insert_text(
            (PAGE.width / 2, PAGE.height - MARGIN + 10), str(number), fontsize=8, fontname="helv"
        )
        self.y = TOP

    def wrap(self, text: str, size: float) -> list[str]:
        lines, current = [], ""
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if self.font.text_length(candidate, fontsize=size) > CONTENT_WIDTH and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        return [*lines, current] if current else lines

    def paragraph(self, text: str) -> None:
        for line in self.wrap(text, BODY_SIZE):
            if self.page is None or self.y + LEADING > BOTTOM:
                self.new_page()
            self.page.insert_text((MARGIN, self.y), line, fontsize=BODY_SIZE, fontname="helv")
            self.y += LEADING
        self.y += LEADING / 2

    def heading(self, lines: list[str]) -> None:
        self.new_page()
        self.y += 40
        for line in lines:
            for part in self.wrap(line, 15):
                self.page.insert_text((MARGIN, self.y), part, fontsize=15, fontname="hebo")
                self.y += 21
        self.y += 18


def build(source: Path, output: Path) -> None:
    items = paragraphs(body_of(source.read_text("utf-8")))
    layout = Layout()

    layout.new_page()
    layout.page.insert_text((MARGIN, 200), "How to Live on", fontsize=22, fontname="hebo")
    layout.page.insert_text((MARGIN, 228), "Twenty-Four Hours a Day", fontsize=22, fontname="hebo")
    layout.page.insert_text((MARGIN, 262), AUTHOR, fontsize=13, fontname="helv")

    i = 0
    while i < len(items):
        item = items[i]
        if item == "PREFACE TO THIS EDITION":
            layout.heading([item])
        elif item == "CONTENTS":
            layout.heading([item])
            i += 1
            layout.paragraph(items[i])
            for line in re.findall(r"[IVX]+ [A-Z' -]+?(?= [IVX]+ |$)", items[i + 1]):
                layout.paragraph(line)
            i += 1
        elif ROMAN.match(item):
            layout.heading([item, items[i + 1]])
            i += 1
        else:
            layout.paragraph(item.replace("_", ""))
        i += 1

    layout.doc.set_metadata({"title": TITLE, "author": AUTHOR})
    layout.doc.save(output, garbage=3, deflate=True)
    print(f"{output}: {layout.doc.page_count} pagine")


if __name__ == "__main__":
    build(Path(sys.argv[1]), Path(sys.argv[2]))
