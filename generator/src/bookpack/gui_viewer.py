"""Visualizzatore di pagine PDF per la finestra: PyMuPDF disegna, un Canvas mostra.

PyMuPDF non è adatto ai thread: tutte le chiamate di questo modulo stanno nel thread di Tk, e chi
lo usa deve chiudere il documento prima di aprire un PDF in un thread di lavoro.
"""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk

import pymupdf

MARGIN = 8
ZOOM_STEP = 1.25
MIN_ZOOM = 0.5
MAX_ZOOM = 5.0
# Dimensioni di riserva finché il Canvas non è ancora stato disposto sullo schermo
FALLBACK_WIDTH = 560
FALLBACK_HEIGHT = 760
RESIZE_DELAY_MS = 120
CANVAS_BACKGROUND = "#6b6b6b"


class PdfViewer(ttk.Frame):
    def __init__(self, parent: tk.Misc, on_page: Callable[[int], None] | None = None) -> None:
        super().__init__(parent)
        self.on_page = on_page
        self.document: pymupdf.Document | None = None
        self.page = 0
        self.page_count = 0
        self.zoom = 1.0  # rispetto alla pagina adattata allo spazio disponibile
        self.image: tk.PhotoImage | None = None
        self._resize_job: str | None = None

        self.page_var = tk.StringVar()
        self.count_var = tk.StringVar(value="/ –")

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 4))
        self.previous_button = ttk.Button(toolbar, text="◀", width=3, command=self.previous_page)
        self.previous_button.pack(side="left")
        self.page_entry = ttk.Entry(toolbar, textvariable=self.page_var, width=6, justify="right")
        self.page_entry.pack(side="left", padx=(4, 2))
        self.page_entry.bind("<Return>", lambda _: self._go_to_typed_page())
        self.page_entry.bind("<FocusOut>", lambda _: self._go_to_typed_page())
        ttk.Label(toolbar, textvariable=self.count_var).pack(side="left", padx=(0, 4))
        self.next_button = ttk.Button(toolbar, text="▶", width=3, command=self.next_page)
        self.next_button.pack(side="left")
        ttk.Button(toolbar, text="Adatta", command=self.reset_zoom).pack(side="right")
        ttk.Button(toolbar, text="+", width=3, command=lambda: self._change_zoom(ZOOM_STEP)).pack(
            side="right", padx=(0, 4)
        )
        ttk.Button(
            toolbar, text="−", width=3, command=lambda: self._change_zoom(1 / ZOOM_STEP)
        ).pack(side="right", padx=(0, 2))

        area = ttk.Frame(self)
        area.pack(fill="both", expand=True)
        area.columnconfigure(0, weight=1)
        area.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(area, background=CANVAS_BACKGROUND, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(area, orient="horizontal", command=self.canvas.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)

        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", lambda _: self.canvas.focus_set())
        self.canvas.bind("<MouseWheel>", lambda event: self._on_wheel(event.delta))
        self.canvas.bind("<Button-4>", lambda _: self._on_wheel(1))
        self.canvas.bind("<Button-5>", lambda _: self._on_wheel(-1))
        for key in ("<Left>", "<Prior>"):
            self.canvas.bind(key, lambda _: self.previous_page())
        for key in ("<Right>", "<Next>"):
            self.canvas.bind(key, lambda _: self.next_page())

        self._show_message("Nessun PDF aperto")

    # --- Documento e pagina --------------------------------------------------------------------

    def open(self, path: Path) -> None:
        self.close()
        self.document = pymupdf.open(path)
        self.page_count = self.document.page_count
        self.count_var.set(f"/ {self.page_count}")
        self.show_page(1)

    def close(self) -> None:
        if self.document is not None:
            self.document.close()
        self.document = None
        self.page = 0
        self.page_count = 0
        self.zoom = 1.0
        self.page_var.set("")
        self.count_var.set("/ –")
        self._show_message("Nessun PDF aperto")

    def show_page(self, number: int) -> None:
        if self.document is None:
            return
        self.page = min(max(number, 1), self.page_count)
        self.page_var.set(str(self.page))
        self._render()
        self.canvas.yview_moveto(0)
        self.canvas.xview_moveto(0)
        if self.on_page:
            self.on_page(self.page)

    def previous_page(self) -> None:
        self.show_page(self.page - 1)

    def next_page(self) -> None:
        self.show_page(self.page + 1)

    def _go_to_typed_page(self) -> None:
        if self.document is None:
            return
        typed = self.page_var.get().strip()
        if typed.isdigit():
            if int(typed) != self.page:
                self.show_page(int(typed))
            else:
                self.page_var.set(str(self.page))
        else:
            self.page_var.set(str(self.page))

    # --- Disegno -------------------------------------------------------------------------------

    def _canvas_size(self) -> tuple[int, int]:
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        return (
            width if width > 1 else FALLBACK_WIDTH,
            height if height > 1 else FALLBACK_HEIGHT,
        )

    def _show_message(self, text: str) -> None:
        self.image = None
        self.canvas.delete("all")
        self.canvas.configure(scrollregion=(0, 0, 0, 0))
        width, height = self._canvas_size()
        self.canvas.create_text(width / 2, height / 2, text=text, fill="#f0f0f0")

    def _render(self) -> None:
        if self.document is None or not self.page:
            return
        width, height = self._canvas_size()
        try:
            page = self.document[self.page - 1]
            fit = min(
                (width - 2 * MARGIN) / page.rect.width, (height - 2 * MARGIN) / page.rect.height
            )
            scale = max(fit * self.zoom, 0.05)
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
            self.image = tk.PhotoImage(master=self, data=pixmap.tobytes("ppm"), format="PPM")
        except Exception as exc:  # un PDF danneggiato non deve bloccare la finestra
            self._show_message(f"Pagina {self.page} non disponibile: {exc}")
            return
        total_width = max(width, pixmap.width + 2 * MARGIN)
        total_height = max(height, pixmap.height + 2 * MARGIN)
        self.canvas.delete("all")
        self.canvas.create_image(total_width / 2, MARGIN, anchor="n", image=self.image)
        self.canvas.configure(scrollregion=(0, 0, total_width, total_height))

    def _on_resize(self, _event: tk.Event) -> None:
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(RESIZE_DELAY_MS, self._render)

    def _change_zoom(self, factor: float) -> None:
        self.zoom = min(max(self.zoom * factor, MIN_ZOOM), MAX_ZOOM)
        self._render()

    def reset_zoom(self) -> None:
        self.zoom = 1.0
        self._render()

    def _on_wheel(self, delta: int) -> None:
        if self.document is None:
            return
        direction = -1 if delta > 0 else 1
        # Con la pagina intera a vista la rotella sfoglia, altrimenti scorre
        top, bottom = self.canvas.yview()
        if top <= 0.0 and bottom >= 1.0:
            self.show_page(self.page + direction)
        else:
            self.canvas.yview_scroll(direction * 3, "units")
