"""Finestra Tkinter: PDF, capitoli da verificare e correggere, parametri, generazione del pack.

La generazione gira in un thread. Il thread non tocca mai i widget: mette le azioni in una coda
che il thread di Tk svuota a intervalli regolari. Lavora su una copia dei capitoli, così si può
continuare a sfogliare e correggere mentre genera.
"""

import copy
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from dotenv import set_key

from .cache import ResponseCache
from .condense.chunking import word_count
from .condense.detect import detect_with_llm
from .condense.estimate import estimate_build
from .condense.pipeline import (
    PackError,
    build_pack,
    default_output_path,
    is_too_short,
    numbered_chapters,
    target_sections,
    write_pack,
)
from .config import DEFAULT_OUTPUT_DIR, ENV_PATH, load_settings
from .extract.clean import clean_pages
from .extract.pdf import PdfDocument, open_pdf
from .extract.toc import (
    Detection,
    Section,
    TocError,
    book_title,
    detect_chapters,
    find_overlaps,
    set_section_pages,
    write_toc_file,
)
from .gui_viewer import PdfViewer
from .llm import get_provider
from .llm.base import LLMError
from .llm.catalog import (
    ModelInfo,
    context_budget,
    find_model,
    load_catalog,
    search_models,
    suggest_models,
)
from .llm.structured import StructuredLLM

POLL_MS = 80
PAD = 8
WINDOW_WIDTH = 1360
WINDOW_HEIGHT = 900
LEFT_PANEL_WIDTH = 720
CHECKED = "☑"
UNCHECKED = "☐"
AUTO_LANG = "uguale al libro"
LANGUAGES = [AUTO_LANG, "it", "en", "fr", "es", "de", "pt"]
METHOD_LABELS = {
    "file": "file di capitoli",
    "outline": "indice del PDF",
    "headings": "titoli nel testo",
    "llm": "LLM",
    "none": "nessun capitolo rilevato",
}


class BuildCancelled(Exception):
    pass


@dataclass
class BuildRequest:
    model: str
    api_key: str
    fake: bool
    no_cache: bool
    selected: set[int] | None
    lang: str | None
    output: Path
    info: ModelInfo | None
    detection: Detection


class App:
    def __init__(self, root: tk.Tk, pdf: Path | None = None) -> None:
        self.root = root
        self.settings = load_settings()
        self.doc: PdfDocument | None = None
        self.pages: dict[int, str] = {}
        self.detection: Detection | None = None
        self.catalog: list[ModelInfo] = []
        self.events: queue.Queue[Callable[[], None]] = queue.Queue()
        self.cancel = threading.Event()
        self.busy = False
        self.output_is_custom = False
        self.last_output: Path | None = None
        # Le righe sono identificate dalla posizione in detection.sections, che non cambia
        self.checked: set[int] = set()
        self.promoted: set[int] = set()  # sezioni escluse in automatico e incluse a mano
        self.current: int | None = None
        self.chapters_dirty = False

        self.pdf_var = tk.StringVar()
        self.toc_var = tk.StringVar()
        self.info_var = tk.StringVar(value="Scegli un PDF per iniziare.")
        self.model_var = tk.StringVar(value=self.settings.model)
        self.model_info_var = tk.StringVar(value="Carico il catalogo dei modelli…")
        self.key_var = tk.StringVar(value=self.settings.api_key or "")
        self.lang_var = tk.StringVar(value=AUTO_LANG)
        self.output_var = tk.StringVar()
        self.include_all_var = tk.BooleanVar()
        self.no_cache_var = tk.BooleanVar()
        self.fake_var = tk.BooleanVar()
        self.estimate_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.start_var = tk.StringVar()
        self.end_var = tk.StringVar()
        self.editor_message_var = tk.StringVar()
        self.where_var = tk.StringVar()

        root.title("Bookpack")
        width = min(WINDOW_WIDTH, root.winfo_screenwidth() - 40)
        height = min(WINDOW_HEIGHT, root.winfo_screenheight() - 100)
        root.geometry(f"{width}x{height}")
        root.minsize(1000, 640)
        root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._update_controls()
        root.after(POLL_MS, self._poll)

        self._in_background(lambda: load_catalog(self.settings.cache_dir), self._on_catalog)
        if pdf:
            self._load_pdf(pdf)

    # --- Interfaccia ---------------------------------------------------------------------------

    def _build_ui(self) -> None:
        panes = ttk.PanedWindow(self.root, orient="horizontal")
        panes.pack(fill="both", expand=True)
        main = ttk.Frame(panes, padding=PAD)
        preview = ttk.LabelFrame(panes, text="Anteprima", padding=PAD)
        panes.add(main, weight=1)
        panes.add(preview, weight=1)
        self.root.after_idle(lambda: panes.sashpos(0, LEFT_PANEL_WIDTH))

        self._build_preview(preview)

        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=3)
        main.rowconfigure(4, weight=1)

        book = ttk.LabelFrame(main, text="Libro", padding=PAD)
        book.grid(row=0, column=0, sticky="ew")
        book.columnconfigure(1, weight=1)
        ttk.Label(book, text="PDF").grid(row=0, column=0, sticky="w", padx=(0, PAD))
        ttk.Entry(book, textvariable=self.pdf_var, state="readonly").grid(
            row=0, column=1, sticky="ew"
        )
        self.pdf_button = ttk.Button(book, text="Scegli…", command=self._choose_pdf)
        self.pdf_button.grid(row=0, column=2, padx=(PAD, 0))
        ttk.Label(book, text="Capitoli").grid(row=1, column=0, sticky="w", pady=(PAD, 0))
        ttk.Entry(book, textvariable=self.toc_var, state="readonly").grid(
            row=1, column=1, sticky="ew", pady=(PAD, 0)
        )
        toc_buttons = ttk.Frame(book)
        toc_buttons.grid(row=1, column=2, padx=(PAD, 0), pady=(PAD, 0))
        self.toc_button = ttk.Button(toc_buttons, text="Apri…", command=self._choose_toc)
        self.toc_button.pack(side="left")
        self.export_button = ttk.Button(toc_buttons, text="Salva…", command=self._export_toc)
        self.export_button.pack(side="left", padx=(4, 0))
        ttk.Label(book, textvariable=self.info_var, wraplength=LEFT_PANEL_WIDTH - 40).grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(PAD, 0)
        )

        chapters = ttk.LabelFrame(
            main,
            text="Capitoli: spunta quelli da portare nel pack, clicca una riga per controllarla",
            padding=PAD,
        )
        chapters.grid(row=1, column=0, sticky="nsew", pady=(PAD, 0))
        chapters.columnconfigure(0, weight=1)
        chapters.rowconfigure(0, weight=1)
        columns = ("check", "index", "title", "pages", "words", "state")
        self.tree = ttk.Treeview(
            chapters, columns=columns, show="headings", height=8, selectmode="browse"
        )
        for column, label, width, anchor, stretch in (
            ("check", CHECKED, 34, "center", False),
            ("index", "#", 34, "e", False),
            ("title", "Titolo", 310, "w", True),
            ("pages", "Pagine", 70, "e", False),
            ("words", "Parole", 60, "e", False),
            ("state", "Note", 110, "w", False),
        ):
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor=anchor, stretch=stretch)
        self.tree.heading("check", command=self._toggle_all)
        self.tree.tag_configure("off", foreground="#888888")
        self.tree.tag_configure("warning", foreground="#b45309")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(chapters, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<<TreeviewSelect>>", lambda _: self._on_row_selected())
        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.bind("<space>", self._on_tree_space)

        editor = ttk.Frame(chapters)
        editor.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(PAD, 0))
        editor.columnconfigure(1, weight=1)
        ttk.Label(editor, text="Titolo").grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.title_entry = ttk.Entry(editor, textvariable=self.title_var)
        self.title_entry.grid(row=0, column=1, sticky="ew")
        ttk.Label(editor, text="da p.").grid(row=0, column=2, padx=(PAD, 4))
        self.start_spin = ttk.Spinbox(
            editor,
            textvariable=self.start_var,
            from_=1,
            to=1,
            width=6,
            command=self._apply_editor,
        )
        self.start_spin.grid(row=0, column=3)
        ttk.Label(editor, text="a p.").grid(row=0, column=4, padx=(PAD, 4))
        self.end_spin = ttk.Spinbox(
            editor,
            textvariable=self.end_var,
            from_=1,
            to=1,
            width=6,
            command=self._apply_editor,
        )
        self.end_spin.grid(row=0, column=5)
        for widget in (self.title_entry, self.start_spin, self.end_spin):
            widget.bind("<Return>", lambda _: self._apply_editor())
            widget.bind("<FocusOut>", lambda _: self._apply_editor())
        ttk.Label(editor, textvariable=self.editor_message_var, foreground="#b91c1c").grid(
            row=1, column=0, columnspan=6, sticky="w"
        )

        options = ttk.LabelFrame(main, text="Parametri", padding=PAD)
        options.grid(row=2, column=0, sticky="ew", pady=(PAD, 0))
        options.columnconfigure(1, weight=1)

        ttk.Label(options, text="Modello").grid(row=0, column=0, sticky="w", padx=(0, PAD))
        self.model_box = ttk.Combobox(options, textvariable=self.model_var)
        self.model_box.grid(row=0, column=1, sticky="ew")
        self.model_box.bind("<KeyRelease>", self._on_model_typed)
        self.model_box.bind("<<ComboboxSelected>>", lambda _: self._on_model_changed())
        self.model_box.bind("<FocusOut>", lambda _: self._on_model_changed())
        self.save_button = ttk.Button(options, text="Salva in .env", command=self._save_env)
        self.save_button.grid(row=0, column=2, rowspan=2, padx=(PAD, 0))
        ttk.Label(options, textvariable=self.model_info_var, foreground="#555555").grid(
            row=1, column=1, sticky="w"
        )

        ttk.Label(options, text="Chiave API").grid(row=2, column=0, sticky="w", pady=(PAD, 0))
        self.key_entry = ttk.Entry(options, textvariable=self.key_var, show="•")
        self.key_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=(PAD, 0))

        ttk.Label(options, text="Lingua").grid(row=3, column=0, sticky="w", pady=(PAD, 0))
        line = ttk.Frame(options)
        line.grid(row=3, column=1, columnspan=2, sticky="w", pady=(PAD, 0))
        ttk.Combobox(line, textvariable=self.lang_var, values=LANGUAGES, width=16).pack(side="left")
        ttk.Checkbutton(
            line,
            text="Includi le sezioni escluse",
            variable=self.include_all_var,
            command=self._on_include_all,
        ).pack(side="left", padx=(PAD, 0))
        ttk.Checkbutton(line, text="Ignora la cache", variable=self.no_cache_var).pack(
            side="left", padx=(PAD, 0)
        )
        ttk.Checkbutton(
            line,
            text="Prova gratis, senza LLM",
            variable=self.fake_var,
            command=self._on_model_changed,
        ).pack(side="left", padx=(PAD, 0))

        ttk.Label(options, text="Salva in").grid(row=4, column=0, sticky="w", pady=(PAD, 0))
        ttk.Entry(options, textvariable=self.output_var).grid(
            row=4, column=1, sticky="ew", pady=(PAD, 0)
        )
        self.output_button = ttk.Button(options, text="Scegli…", command=self._choose_output)
        self.output_button.grid(row=4, column=2, padx=(PAD, 0), pady=(PAD, 0))

        actions = ttk.Frame(main)
        actions.grid(row=3, column=0, sticky="ew", pady=(PAD, 0))
        actions.columnconfigure(0, weight=1)
        ttk.Label(actions, textvariable=self.estimate_var, wraplength=LEFT_PANEL_WIDTH - 300).grid(
            row=0, column=0, sticky="w"
        )
        self.open_button = ttk.Button(actions, text="Apri cartella", command=self._open_folder)
        self.open_button.grid(row=0, column=1, padx=(PAD, 0))
        self.stop_button = ttk.Button(actions, text="Interrompi", command=self._stop)
        self.stop_button.grid(row=0, column=2, padx=(PAD, 0))
        self.build_button = ttk.Button(actions, text="Genera", command=self._start_build)
        self.build_button.grid(row=0, column=3, padx=(PAD, 0))
        self.progress = ttk.Progressbar(actions, mode="determinate")
        self.progress.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(PAD, 0))

        log_frame = ttk.Frame(main)
        log_frame.grid(row=4, column=0, sticky="nsew", pady=(PAD, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log = tk.Text(log_frame, height=4, wrap="word", state="disabled")
        self.log.grid(row=0, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log.configure(yscrollcommand=log_scroll.set)

    def _build_preview(self, parent: ttk.LabelFrame) -> None:
        self.viewer = PdfViewer(parent, on_page=lambda _: self._update_where())
        self.viewer.pack(fill="both", expand=True)

        ttk.Label(parent, textvariable=self.where_var).pack(anchor="w", pady=(PAD, 4))
        buttons = ttk.Frame(parent)
        buttons.pack(fill="x")
        self.first_button = ttk.Button(
            buttons, text="⏮ Prima pagina", command=lambda: self._show_boundary("start")
        )
        self.first_button.pack(side="left")
        self.last_button = ttk.Button(
            buttons, text="Ultima pagina ⏭", command=lambda: self._show_boundary("end")
        )
        self.last_button.pack(side="left", padx=(4, 0))
        self.end_here_button = ttk.Button(
            buttons, text="Il capitolo finisce qui", command=lambda: self._set_boundary("end")
        )
        self.end_here_button.pack(side="right")
        self.start_here_button = ttk.Button(
            buttons, text="Il capitolo inizia qui", command=lambda: self._set_boundary("start")
        )
        self.start_here_button.pack(side="right", padx=(0, 4))

    def _update_controls(self) -> None:
        ready = not self.busy
        has_book = self.doc is not None
        has_sections = bool(self.detection and self.detection.sections)
        has_row = self.current is not None and self.viewer.document is not None
        for button in (
            self.first_button,
            self.last_button,
            self.start_here_button,
            self.end_here_button,
        ):
            self._set_enabled(button, has_row)
        self._set_enabled(self.pdf_button, ready)
        self._set_enabled(self.toc_button, ready and has_book)
        self._set_enabled(self.export_button, ready and has_sections)
        self._set_enabled(self.output_button, ready and has_book)
        self._set_enabled(self.build_button, ready and has_book)
        self._set_enabled(self.stop_button, self.busy and not self.cancel.is_set())
        self._set_enabled(self.open_button, self.last_output is not None)

    @staticmethod
    def _set_enabled(widget: ttk.Widget, enabled: bool) -> None:
        widget.state(["!disabled"] if enabled else ["disabled"])

    def _write_log(self, message: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    # --- Lavoro in background ------------------------------------------------------------------

    def _poll(self) -> None:
        while True:
            try:
                self.events.get_nowait()()
            except queue.Empty:
                break
        self.root.after(POLL_MS, self._poll)

    def _in_background(
        self,
        work: Callable[[], object],
        done: Callable[[object], None],
        failed: Callable[[Exception], None] | None = None,
    ) -> threading.Thread:
        def run() -> None:
            try:
                result = work()
            except Exception as exc:
                error = exc
                self.events.put(lambda: (failed or self._show_error)(error))
            else:
                self.events.put(lambda: done(result))

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread

    def _show_error(self, error: Exception) -> None:
        self._set_busy(False)
        self._write_log(f"Errore: {error}")
        messagebox.showerror("Bookpack", str(error), parent=self.root)

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        self._update_controls()

    # --- Libro e capitoli ----------------------------------------------------------------------

    def _confirm_discard(self) -> bool:
        return not self.chapters_dirty or messagebox.askyesno(
            "Bookpack",
            "Hai modificato i capitoli senza salvarli. Vuoi perdere le modifiche?",
            parent=self.root,
        )

    def _choose_pdf(self) -> None:
        if not self._confirm_discard():
            return
        path = filedialog.askopenfilename(
            parent=self.root, title="Scegli un PDF", filetypes=[("PDF", "*.pdf")]
        )
        if path:
            self._load_pdf(Path(path))

    def _load_pdf(self, path: Path) -> None:
        self._set_busy(True)
        # PyMuPDF non regge due thread: si chiude prima che il lavoro in background apra il PDF
        self.viewer.close()
        self.chapters_dirty = False
        self.pdf_var.set(str(path.resolve()))
        self.toc_var.set("")
        self.output_is_custom = False
        self.info_var.set("Leggo il PDF…")
        self.progress.configure(mode="indeterminate")
        self.progress.start(15)

        def work() -> tuple[PdfDocument, dict[int, str], Detection]:
            doc = open_pdf(path)
            return doc, clean_pages(doc.pages), detect_chapters(doc, None, False)

        def failed(error: Exception) -> None:
            self._stop_spinner()
            self.doc = None
            self.detection = None
            self.info_var.set("Scegli un PDF per iniziare.")
            self._reset_chapter_state()
            self._fill_tree()
            self._load_editor()
            self.where_var.set("")
            self._show_error(error)

        self._in_background(work, self._on_pdf_loaded, failed)

    def _stop_spinner(self) -> None:
        self.progress.stop()
        self.progress.configure(mode="determinate", value=0)

    def _on_pdf_loaded(self, loaded: object) -> None:
        self._stop_spinner()
        self.doc, self.pages, detection = loaded  # type: ignore[misc]
        if self.include_all_var.get():
            for section in detection.sections:
                section.excluded = False
        self.detection = detection
        self.viewer.open(Path(self.pdf_var.get()))
        self._after_detection()
        self._set_busy(False)

    def _reset_chapter_state(self) -> None:
        self.chapters_dirty = False
        self.promoted = set()
        self.current = None
        self.checked = set()
        if self.detection:
            self.checked = {
                position
                for position, section in enumerate(self.detection.sections)
                if not section.excluded and not is_too_short(section, self.pages)
            }

    def _after_detection(self) -> None:
        assert self.doc is not None and self.detection is not None
        self._reset_chapter_state()
        if not self.output_is_custom:
            book_id = self.detection.book.get("id") or book_title(self.doc, self.detection)
            self.output_var.set(str(default_output_path(book_id)))
        for spin in (self.start_spin, self.end_spin):
            spin.configure(to=self.doc.page_count)
        self._update_info()
        self._fill_tree()
        self._load_editor()
        self._refresh_estimate()
        self._update_controls()
        self.tree.selection_set(())
        # Si parte dal primo capitolo spuntato: è la prima cosa da controllare
        if self.checked:
            self.tree.selection_set(f"s{min(self.checked)}")
            self._on_row_selected()
        else:
            self._update_where()

    def _update_info(self) -> None:
        assert self.doc is not None and self.detection is not None
        title = book_title(self.doc, self.detection)
        author = self.detection.book.get("author") or self.doc.author or "autore sconosciuto"
        method = METHOD_LABELS[self.detection.method]
        edited = " · modificata a mano, non salvata" if self.chapters_dirty else ""
        self.info_var.set(f"{title} · {author} · {self.doc.page_count} pagine · {method}{edited}")

    def _on_include_all(self) -> None:
        if not self._confirm_discard():
            self.include_all_var.set(not self.include_all_var.get())
            return
        self._redetect()

    def _redetect(self) -> None:
        if not self.doc:
            return
        toc = Path(self.toc_var.get()) if self.toc_var.get() else None
        try:
            self.detection = detect_chapters(self.doc, toc, self.include_all_var.get())
        except TocError as exc:
            self.toc_var.set("")
            self._show_error(exc)
            return
        self._after_detection()

    def _fill_tree(self) -> None:
        # Le righe si aggiornano sul posto: una modifica può arrivare mentre si clicca un'altra
        # riga (uscita dal campo di testo), e ricrearle annullerebbe quel clic
        sections = self.detection.sections if self.detection else []
        if len(self.tree.get_children()) != len(sections):
            self.tree.delete(*self.tree.get_children())
            for position in range(len(sections)):
                self.tree.insert("", "end", iid=f"s{position}")
        if not self.detection:
            return
        numbers = {id(section): index for index, section in numbered_chapters(self.detection)}
        overlaps = find_overlaps(self.detection.sections)
        for position, section in enumerate(self.detection.sections):
            short = is_too_short(section, self.pages)
            if section.excluded:
                note, tags = "esclusa", ("off",)
            elif position in overlaps:
                note, tags = "si sovrappone", ("warning",)
            elif short:
                note, tags = "troppo breve", ("off",)
            else:
                note, tags = "", ()
            values = (
                CHECKED if position in self.checked else UNCHECKED,
                "" if section.excluded else numbers[id(section)],
                section.title,
                f"{section.page_start}-{section.page_end}",
                f"{word_count(section, self.pages):,}",
                note,
            )
            self.tree.item(f"s{position}", values=values, tags=tags)

    def _selected(self) -> set[int] | None:
        """Numeri dei capitoli spuntati. None se i capitoli non sono ancora stati trovati."""
        if not self.detection or not self.detection.chapters:
            return None
        numbers = {id(section): index for index, section in numbered_chapters(self.detection)}
        return {
            numbers[id(section)]
            for position, section in enumerate(self.detection.sections)
            if position in self.checked and not section.excluded
        }

    # --- Caselle di spunta -------------------------------------------------------------------

    def _on_tree_click(self, event: tk.Event) -> str | None:
        if self.tree.identify_region(event.x, event.y) != "cell":
            return None
        if self.tree.identify_column(event.x) != "#1":
            return None
        row = self.tree.identify_row(event.y)
        if not row:
            return None
        self._toggle(int(row[1:]))
        return "break"  # la spunta non cambia la riga mostrata nell'anteprima

    def _on_tree_space(self, _event: tk.Event) -> str:
        if self.current is not None:
            self._toggle(self.current)
        return "break"

    def _toggle(self, position: int) -> None:
        """Togliere la spunta lascia il numero del capitolo: gli id restano stabili.

        Includere una sezione esclusa la rende un capitolo, quindi rinumera i successivi.
        """
        assert self.detection is not None
        section = self.detection.sections[position]
        short = is_too_short(section, self.pages)
        if section.excluded:
            section.excluded = False
            self.promoted.add(position)
            if not short:
                self.checked.add(position)
            self.chapters_dirty = True
            self._write_log(f"«{section.title}» è ora un capitolo: i successivi cambiano numero.")
        elif position in self.promoted and (position in self.checked or short):
            section.excluded = True
            self.promoted.discard(position)
            self.checked.discard(position)
            self.chapters_dirty = True
        elif short:
            self._write_log(
                f"«{section.title}» è troppo breve per generarla: allarga le sue pagine."
            )
            return
        elif position in self.checked:
            self.checked.discard(position)
        else:
            self.checked.add(position)
        self._after_chapter_change()

    def _toggle_all(self) -> None:
        if not self.detection:
            return
        available = {
            position
            for position, section in enumerate(self.detection.sections)
            if not section.excluded and not is_too_short(section, self.pages)
        }
        self.checked = set() if available <= self.checked else available
        self._after_chapter_change()

    def _after_chapter_change(self) -> None:
        self._update_info()
        self._fill_tree()
        self._refresh_estimate()
        self._update_where()

    # --- Verifica e correzione delle pagine ----------------------------------------------------

    def _current_section(self) -> Section | None:
        if self.current is None or not self.detection:
            return None
        return self.detection.sections[self.current]

    def _on_row_selected(self) -> None:
        selection = self.tree.selection()
        position = int(selection[0][1:]) if selection else None
        if position == self.current:
            return  # riga ridisegnata dopo una modifica: l'anteprima resta dov'è
        self.current = position
        self._load_editor()
        self._update_controls()
        section = self._current_section()
        if section:
            self.viewer.show_page(section.page_start)
        self._update_where()

    def _load_editor(self) -> None:
        section = self._current_section()
        self.editor_message_var.set("")
        self.title_var.set(section.title if section else "")
        self.start_var.set(str(section.page_start) if section else "")
        self.end_var.set(str(section.page_end) if section else "")

    def _apply_editor(self) -> None:
        section = self._current_section()
        if section is None:
            return
        title = self.title_var.get().strip()
        start, end = self.start_var.get().strip(), self.end_var.get().strip()
        if not title:
            self.editor_message_var.set("Il titolo non può essere vuoto.")
            return
        if not start.isdigit() or not end.isdigit():
            self.editor_message_var.set("Le pagine devono essere numeri.")
            return
        old_start, old_end = section.page_start, section.page_end
        self._change_section(title, int(start), int(end))
        # L'anteprima va al confine appena spostato: è lì che serve controllare
        if section.page_start != old_start:
            self.viewer.show_page(section.page_start)
        elif section.page_end != old_end:
            self.viewer.show_page(section.page_end)

    def _change_section(self, title: str, start: int, end: int) -> None:
        assert self.doc is not None and self.detection is not None and self.current is not None
        section = self.detection.sections[self.current]
        if (title, start, end) == (section.title, section.page_start, section.page_end):
            self.editor_message_var.set("")
            return
        was_short = {
            position: is_too_short(item, self.pages)
            for position, item in enumerate(self.detection.sections)
        }
        try:
            set_section_pages(
                self.detection.sections, self.current, start, end, self.doc.page_count
            )
        except TocError as exc:
            self.editor_message_var.set(str(exc))
            return
        section.title = title
        self.chapters_dirty = True
        # Anche i vicini possono aver cambiato pagine: la spunta segue la loro nuova lunghezza
        for position, item in enumerate(self.detection.sections):
            short = is_too_short(item, self.pages)
            if short and not was_short[position]:
                self.checked.discard(position)
            elif was_short[position] and not short and not item.excluded:
                self.checked.add(position)
        self._load_editor()
        self._after_chapter_change()

    def _show_boundary(self, which: str) -> None:
        section = self._current_section()
        if section:
            self.viewer.show_page(section.page_start if which == "start" else section.page_end)

    def _set_boundary(self, which: str) -> None:
        section = self._current_section()
        if section is None or not self.viewer.page:
            return
        page = self.viewer.page
        if which == "start":
            self._change_section(section.title, page, max(section.page_end, page))
        elif page < section.page_start:
            self.editor_message_var.set(
                f"La fine non può precedere l'inizio del capitolo (p. {section.page_start})."
            )
        else:
            self._change_section(section.title, section.page_start, page)

    def _update_where(self) -> None:
        """Dice a quale capitolo appartiene la pagina mostrata: serve a verificare i confini."""
        page = self.viewer.page
        if not page or not self.detection:
            self.where_var.set("")
            return
        numbers = {id(section): index for index, section in numbered_chapters(self.detection)}
        found = [s for s in self.detection.sections if s.page_start <= page <= s.page_end]
        if not found:
            self.where_var.set(f"Pagina {page}: in nessun capitolo.")
            return
        section = found[0]
        if section.excluded:
            self.where_var.set(f"Pagina {page}: sezione esclusa «{section.title}».")
            return
        count = section.page_end - section.page_start + 1
        inside = page - section.page_start + 1
        edge = (
            "prima e ultima pagina"
            if count == 1
            else "prima pagina"
            if inside == 1
            else "ultima pagina"
            if inside == count
            else f"pagina {inside} di {count}"
        )
        self.where_var.set(
            f"Pagina {page}: capitolo {numbers[id(section)]}, «{section.title}» ({edge})."
        )

    def _choose_toc(self) -> None:
        if not self._confirm_discard():
            return
        path = filedialog.askopenfilename(
            parent=self.root,
            title="File dei capitoli",
            filetypes=[("YAML", "*.yaml *.yml"), ("Tutti i file", "*.*")],
        )
        if path:
            self.toc_var.set(path)
            self._redetect()

    def _export_toc(self) -> None:
        if not self.doc or not self.detection:
            return
        stem = Path(self.pdf_var.get()).stem
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Salva i capitoli",
            initialdir=DEFAULT_OUTPUT_DIR if DEFAULT_OUTPUT_DIR.exists() else None,
            initialfile=f"{stem}.toc.yaml",
            defaultextension=".yaml",
            filetypes=[("YAML", "*.yaml *.yml")],
        )
        if not path:
            return
        write_toc_file(self.doc, self.detection, Path(path))
        self.toc_var.set(path)
        self.chapters_dirty = False
        self._update_info()
        self._write_log(f"Capitoli salvati in {path}. Si riaprono con «Apri…».")

    def _choose_output(self) -> None:
        current = Path(self.output_var.get() or DEFAULT_OUTPUT_DIR / "libro.bookpack.json")
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Salva il pack",
            initialdir=current.parent if current.parent.exists() else None,
            initialfile=current.name,
            defaultextension=".json",
            filetypes=[("Book pack", "*.bookpack.json"), ("JSON", "*.json")],
        )
        if path:
            self.output_var.set(path)
            self.output_is_custom = True

    # --- Modello e costo -----------------------------------------------------------------------

    def _on_catalog(self, models: object) -> None:
        self.catalog = models  # type: ignore[assignment]
        self.model_box.configure(values=[model.id for model in self.catalog])
        self._on_model_changed()

    def _on_model_typed(self, event: tk.Event) -> None:
        if event.keysym in ("Up", "Down", "Return", "Escape", "Tab"):
            return
        found = search_models(self.catalog, self.model_var.get())
        self.model_box.configure(values=[model.id for model in found])
        self._on_model_changed()

    def _current_model(self) -> ModelInfo | None:
        return find_model(self.catalog, self.model_var.get().strip())

    def _on_model_changed(self) -> None:
        info = self._current_model()
        if self.fake_var.get():
            self.model_info_var.set("Prova gratis: nessuna chiamata, contenuto meccanico.")
        elif not self.catalog:
            self.model_info_var.set("Catalogo non disponibile: costo non stimabile.")
        elif not info:
            self.model_info_var.set("Modello non presente nel catalogo di OpenRouter.")
        else:
            prices = (
                f"${info.input_price:.2f} / ${info.output_price:.2f} per milione di token"
                if info.prices
                else "prezzo variabile"
            )
            context = f"contesto {info.context_length:,}" if info.context_length else "contesto n/d"
            schema = "output strutturato" if info.structured else "senza output strutturato"
            parts = [prices, context, schema]
            if info.reasoning_effort:
                parts.append(f"ragionamento {info.reasoning_effort}")
            self.model_info_var.set(" · ".join(parts))
        self._refresh_estimate()

    def _refresh_estimate(self) -> None:
        if not self.detection:
            self.estimate_var.set("")
            return
        if not self.detection.chapters:
            self.estimate_var.set(
                "Capitoli non rilevati: servirà una chiamata all'LLM per trovarli."
            )
            return
        info = self._current_model()
        targets = target_sections(self.detection, self.pages, self._selected())
        if not targets:
            self.estimate_var.set("Nessun capitolo spuntato.")
            return
        prices = (0.0, 0.0) if self.fake_var.get() else info.prices if info else None
        budget = context_budget(self.settings.context_tokens, info)
        estimate = estimate_build(targets, self.pages, prices, budget)
        cost = "n/d" if estimate.cost is None else f"${estimate.cost:.2f}"
        self.estimate_var.set(
            f"{len(targets)} capitoli · circa {estimate.calls} chiamate · costo stimato {cost}"
        )

    def _save_env(self) -> None:
        ENV_PATH.touch(exist_ok=True)
        model = self.model_var.get().strip()
        key = self.key_var.get().strip()
        if model:
            set_key(ENV_PATH, "BOOKPACK_MODEL", model)
            os.environ["BOOKPACK_MODEL"] = model
        if key:
            set_key(ENV_PATH, "OPENROUTER_API_KEY", key)
            os.environ["OPENROUTER_API_KEY"] = key
        self._write_log(f"Modello e chiave salvati in {ENV_PATH}.")

    # --- Generazione ---------------------------------------------------------------------------

    def _request(self) -> BuildRequest | None:
        """Raccoglie i parametri e chiede conferma. None se manca qualcosa o si rinuncia."""
        fake = self.fake_var.get()
        model = self.model_var.get().strip()
        key = self.key_var.get().strip()
        info = self._current_model()
        output = self.output_var.get().strip()
        if not output:
            messagebox.showerror("Bookpack", "Indica dove salvare il pack.", parent=self.root)
            return None
        assert self.detection is not None
        if self.detection.chapters and not self._selected():
            messagebox.showerror("Bookpack", "Spunta almeno un capitolo.", parent=self.root)
            return None
        if not fake:
            if not key:
                messagebox.showerror(
                    "Bookpack",
                    "Serve una chiave OpenRouter: creala su https://openrouter.ai/keys "
                    "e incollala nel campo «Chiave API».",
                    parent=self.root,
                )
                return None
            if not model:
                messagebox.showerror("Bookpack", "Scegli un modello.", parent=self.root)
                return None
            if self.catalog and not info:
                hints = ", ".join(suggest_models(self.catalog, model))
                hint = f"\n\nForse: {hints}" if hints else ""
                messagebox.showerror(
                    "Bookpack",
                    f"Modello non presente nel catalogo: {model}{hint}",
                    parent=self.root,
                )
                return None
            if not messagebox.askyesno(
                "Bookpack",
                f"Generare con {model}?\n\n{self.estimate_var.get()}\n\n"
                "È una stima. Le risposte già in cache non si ripagano.",
                parent=self.root,
            ):
                return None
        lang = self.lang_var.get().strip()
        return BuildRequest(
            model=model,
            api_key=key,
            fake=fake,
            no_cache=self.no_cache_var.get(),
            selected=self._selected(),
            lang=None if lang in ("", AUTO_LANG) else lang,
            output=Path(output),
            info=info,
            detection=copy.deepcopy(self.detection),
        )

    def _start_build(self) -> None:
        request = self._request()
        if not request:
            return
        self.cancel.clear()
        self._set_busy(True)
        self.progress.configure(mode="determinate", value=0)
        self._write_log(f"Avvio con {'prova gratis' if request.fake else request.model}.")
        self._in_background(lambda: self._build(request), self._on_built, self._on_build_failed)

    def _build(self, request: BuildRequest) -> tuple[Path, object, object]:
        assert self.doc is not None
        settings = load_settings(request.model, request.fake)
        settings.api_key = request.api_key or settings.api_key
        provider = get_provider(settings, request.info)
        llm = StructuredLLM(
            provider, ResponseCache(settings.cache_dir, enabled=not request.no_cache)
        )

        detection = request.detection
        if not detection.chapters:
            self.events.put(lambda: self._write_log("Cerco i capitoli con l'LLM…"))
            detection = detect_with_llm(llm, self.doc, self.pages)

        steps = len(target_sections(detection, self.pages, request.selected)) + 1
        self.events.put(lambda: self.progress.configure(maximum=steps, value=0))

        def on_step(step: str) -> None:
            if self.cancel.is_set():
                raise BuildCancelled
            self.events.put(lambda: self._on_step(step))

        budget = context_budget(settings.context_tokens, request.info)
        result = build_pack(
            llm, self.doc, self.pages, detection, request.selected, request.lang, budget, on_step
        )
        if not result.report.ok:
            problems = "\n".join(result.report.errors)
            raise PackError(f"Il pack non rispetta i vincoli e non è stato scritto:\n{problems}")
        return write_pack(result.pack, request.output), result, llm.usage

    def _on_step(self, step: str) -> None:
        self._write_log(step)
        self.progress.step(1)

    def _on_built(self, built: object) -> None:
        path, result, usage = built  # type: ignore[misc]
        self.last_output = path
        self.progress.configure(value=self.progress["maximum"])
        for skipped in result.skipped:
            self._write_log(f"Saltato: {skipped}")
        for warning in result.report.warnings:
            self._write_log(f"Avviso: {warning}")
        spent = "" if usage.cost is None else f", costo effettivo ${usage.cost:.2f}"
        self._write_log(
            f"Fatto: {len(result.pack.chapters)} capitoli in {path}. "
            f"Chiamate {usage.calls}, dalla cache {usage.cached}, ritentativi {usage.retries}{spent}."
        )
        self._set_busy(False)
        messagebox.showinfo(
            "Bookpack",
            f"Pack pronto:\n{path}\n\nImportalo dall'app in «Importa».",
            parent=self.root,
        )

    def _on_build_failed(self, error: Exception) -> None:
        self.progress.configure(value=0)
        if isinstance(error, BuildCancelled):
            self._set_busy(False)
            self._write_log("Interrotto. Rilanciando, le risposte già ottenute non si ripagano.")
            return
        if isinstance(error, LLMError):
            self._write_log("Le risposte già ottenute sono in cache: rilanciando non si ripagano.")
        self._show_error(error)

    def _stop(self) -> None:
        self.cancel.set()
        self._write_log("Mi fermo alla fine della chiamata in corso…")
        self._update_controls()

    def _open_folder(self) -> None:
        if not self.last_output:
            return
        folder = self.last_output.parent
        if sys.platform == "win32":
            os.startfile(folder)  # noqa: S606
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(folder)])

    def _on_close(self) -> None:
        if self.busy and not messagebox.askyesno(
            "Bookpack",
            "C'è un lavoro in corso. Chiudere comunque?\nLe risposte già ottenute restano in cache.",
            parent=self.root,
        ):
            return
        if not self._confirm_discard():
            return
        self.cancel.set()
        self.viewer.close()
        self.root.destroy()


def run(pdf: Path | None = None) -> None:
    root = tk.Tk()
    App(root, pdf)
    root.mainloop()
