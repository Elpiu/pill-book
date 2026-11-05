"""La finestra vera, senza dialoghi. Senza display (es. in CI) i test vengono saltati."""

import gc
import json
import threading
import time

import pytest

tk = pytest.importorskip("tkinter")

from bookpack import gui as gui_module  # noqa: E402
from bookpack.gui import App  # noqa: E402
from bookpack.validate import validate_data  # noqa: E402


@pytest.fixture
def dialogs(monkeypatch):
    calls = {"errors": [], "infos": [], "questions": [], "answer": True}

    def error(_title, message, **_):
        calls["errors"].append(message)

    def info(_title, message, **_):
        calls["infos"].append(message)

    def ask(_title, message, **_):
        calls["questions"].append(message)
        return calls["answer"]

    monkeypatch.setattr(gui_module.messagebox, "showerror", error)
    monkeypatch.setattr(gui_module.messagebox, "showinfo", info)
    monkeypatch.setattr(gui_module.messagebox, "askyesno", ask)
    return calls


@pytest.fixture
def root():
    # Creando più finestre nello stesso processo Tcl a volte non trova tk.tcl: si riprova.
    # Si salta solo se manca davvero il display, così un guasto vero non passa inosservato.
    for attempt in range(5):
        try:
            window = tk.Tk()
            break
        except tk.TclError as exc:
            if "display" in str(exc).lower():
                pytest.skip(f"Nessun display: {exc}")
            if attempt == 4:
                raise
            time.sleep(0.2)
    window.withdraw()
    yield window
    # Variabili e interprete Tcl vanno raccolti nel thread principale, non in un thread qualsiasi
    for thread in threading.enumerate():
        if thread is not threading.current_thread() and thread.daemon:
            thread.join(10)
    window.destroy()
    del window
    gc.collect()


def pump(root, until, timeout=30.0):
    end = time.monotonic() + timeout
    while not until():
        root.update()
        assert time.monotonic() < end, "timeout"
        time.sleep(0.01)
    root.update()


@pytest.fixture
def app(root, dialogs):
    instance = App(root)
    pump(root, lambda: instance.catalog)
    return instance


def load(app, root, pdf):
    app._load_pdf(pdf)
    pump(root, lambda: not app.busy)


def test_catalog_fills_model_list_and_shows_prices(app):
    assert "test/buono" in app.model_box.cget("values")
    app.model_var.set("test/buono")
    app._on_model_changed()
    assert "$2.00 / $10.00" in app.model_info_var.get()

    app.model_var.set("inesistente/x")
    app._on_model_changed()
    assert "non presente" in app.model_info_var.get()


def test_loading_a_pdf_fills_chapters_and_estimate(app, root, pdf_with_outline):
    assert app.build_button.instate(["disabled"])
    load(app, root, pdf_with_outline)

    rows = app.tree.get_children()
    assert len(rows) == 6  # Copyright e Bibliografia sono escluse ma visibili
    assert app.tree.set(rows[0], "state") == "esclusa"
    assert app.tree.set(rows[0], "check") == gui_module.UNCHECKED
    assert app.tree.set(rows[1], "check") == gui_module.CHECKED
    assert app._selected() == {1, 2, 3, 4}
    assert "Manuale di prova" in app.info_var.get()
    assert app.output_var.get().endswith("manuale-di-prova.bookpack.json")
    assert app.build_button.instate(["!disabled"])

    app.model_var.set("test/buono")
    app._on_model_changed()
    assert "4 capitoli" in app.estimate_var.get()

    app._toggle(2)  # capitolo 2
    app._toggle(4)  # capitolo 4
    root.update()
    assert app._selected() == {1, 3}
    assert "2 capitoli" in app.estimate_var.get()
    assert "$" in app.estimate_var.get()


def test_scan_shows_an_error_and_keeps_the_window_usable(app, root, dialogs, tmp_path):
    import pymupdf

    path = tmp_path / "scan.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(path)
    load(app, root, path)
    assert "scansione" in dialogs["errors"][0]
    assert app.doc is None
    assert app.pdf_button.instate(["!disabled"])


def test_include_all_shows_excluded_sections(app, root, pdf_with_outline):
    load(app, root, pdf_with_outline)
    app.include_all_var.set(True)
    app._redetect()
    assert len(app.tree.get_children()) == 6
    assert all(app.tree.set(row, "index") != "" for row in app.tree.get_children())


def test_toc_file_overrides_detection(app, root, pdf_with_outline, tmp_path, monkeypatch, dialogs):
    load(app, root, pdf_with_outline)
    toc = tmp_path / "libro.toc.yaml"
    toc.write_text(
        "book: {title: Altro titolo}\nchapters:\n- {title: Unico, pageStart: 3, pageEnd: 10}\n",
        "utf-8",
    )
    monkeypatch.setattr(gui_module.filedialog, "askopenfilename", lambda **_: str(toc))
    app._choose_toc()
    assert app.tree.get_children() == ("s0",)
    assert app.tree.set("s0", "index") == "1"
    assert "Altro titolo" in app.info_var.get()

    toc.write_text("foo: bar", "utf-8")
    app._choose_toc()
    assert dialogs["errors"] and "chapters" in dialogs["errors"][-1]
    assert app.toc_var.get() == ""


def test_fake_build_writes_a_valid_pack(app, root, pdf_with_outline, tmp_path, dialogs):
    load(app, root, pdf_with_outline)
    output = tmp_path / "pack.bookpack.json"
    app.output_var.set(str(output))
    app.fake_var.set(True)
    app.key_var.set("")
    app.lang_var.set("fr")
    for position in (1, 3, 4):  # resta spuntato solo il capitolo 2
        app._toggle(position)
    root.update()
    assert app._selected() == {2}

    app._start_build()
    assert app.busy
    pump(root, lambda: not app.busy)

    assert dialogs["errors"] == []
    assert dialogs["questions"] == []  # la prova gratis non chiede conferma di spesa
    pack, report = validate_data(json.loads(output.read_text("utf-8")))
    assert report.ok, report.errors
    assert [chapter.id for chapter in pack.chapters] == ["ch-02"]
    assert pack.book.lang == "fr"
    assert app.last_output == output
    assert app.open_button.instate(["!disabled"])
    assert "Pack pronto" in dialogs["infos"][0]


def test_real_build_requires_key_and_known_model(app, root, pdf_with_outline, dialogs, tmp_path):
    load(app, root, pdf_with_outline)
    app.output_var.set(str(tmp_path / "x.json"))

    app.key_var.set("")
    app.model_var.set("test/buono")
    app._start_build()
    assert "chiave" in dialogs["errors"][-1].lower()
    assert not app.busy

    app.key_var.set("sk-or-test")
    app.model_var.set("test/buon")
    app._start_build()
    assert "test/buono" in dialogs["errors"][-1]
    assert not app.busy


def test_declining_the_cost_does_not_start(app, root, pdf_with_outline, dialogs, tmp_path):
    load(app, root, pdf_with_outline)
    app.output_var.set(str(tmp_path / "x.json"))
    app.key_var.set("sk-or-test")
    app.model_var.set("test/buono")
    app._on_model_changed()
    dialogs["answer"] = False
    app._start_build()
    assert "test/buono" in dialogs["questions"][0]
    assert "costo stimato" in dialogs["questions"][0]
    assert not app.busy


def test_stop_interrupts_and_the_rerun_uses_the_cache(
    app, root, pdf_with_outline, tmp_path, dialogs, monkeypatch
):
    load(app, root, pdf_with_outline)
    output = tmp_path / "pack.bookpack.json"
    app.output_var.set(str(output))
    app.fake_var.set(True)

    started = threading.Event()
    real_build_pack = gui_module.build_pack

    def build_pack(*args, **kwargs):
        on_step = args[7]

        def step(message):
            on_step(message)
            started.set()
            time.sleep(0.05)

        return real_build_pack(*args[:7], step)

    monkeypatch.setattr(gui_module, "build_pack", build_pack)
    app._start_build()
    pump(root, started.is_set)
    app._stop()
    pump(root, lambda: not app.busy)

    assert not output.exists()
    assert dialogs["errors"] == []
    assert "Interrotto" in app.log.get("1.0", "end")

    app._start_build()
    pump(root, lambda: not app.busy)
    assert output.exists()
    assert "dalla cache" in app.log.get("1.0", "end")


def test_save_env_writes_model_and_key(app, tmp_path, monkeypatch):
    env = tmp_path / ".env"
    monkeypatch.setattr(gui_module, "ENV_PATH", env)
    monkeypatch.setenv("BOOKPACK_MODEL", "prima")
    monkeypatch.setenv("OPENROUTER_API_KEY", "prima")
    app.model_var.set("test/buono")
    app.key_var.set("sk-or-nuova")
    app._save_env()
    text = env.read_text("utf-8")
    assert "BOOKPACK_MODEL" in text and "test/buono" in text
    assert "sk-or-nuova" in text
    assert "sk-or-nuova" not in app.log.get("1.0", "end")


# --- Caselle di spunta ---------------------------------------------------------------------------


def test_unchecking_keeps_chapter_numbers_stable(app, root, pdf_with_outline):
    load(app, root, pdf_with_outline)
    app._toggle(1)
    assert app.tree.set("s1", "check") == gui_module.UNCHECKED
    assert app.tree.set("s2", "index") == "2"  # il capitolo dopo non cambia numero
    assert app._selected() == {2, 3, 4}
    app._toggle(1)
    assert app._selected() == {1, 2, 3, 4}


def test_checking_an_excluded_section_makes_it_a_chapter_and_back(app, root, pdf_with_outline):
    load(app, root, pdf_with_outline)
    last = len(app.tree.get_children()) - 1  # Bibliografia, troppo breve
    app._toggle(last)
    assert app.detection.sections[last].excluded is False
    assert app.tree.set(f"s{last}", "index") == "5"
    assert app.tree.set(f"s{last}", "check") == gui_module.UNCHECKED  # non si può generare
    assert "modificata a mano" in app.info_var.get()

    app._toggle(last)
    assert app.detection.sections[last].excluded is True
    assert app.tree.set(f"s{last}", "index") == ""


def test_too_short_section_cannot_be_checked(app, root, pdf_with_outline):
    load(app, root, pdf_with_outline)
    section = app.detection.sections[1]
    section.page_end = section.page_start
    app.pages[section.page_start] = "poche parole"
    app.checked.discard(1)
    app._toggle(1)
    assert 1 not in app.checked
    assert "troppo breve" in app.log.get("1.0", "end")


def test_toggle_all_and_build_refuses_empty_selection(
    app, root, pdf_with_outline, dialogs, tmp_path
):
    load(app, root, pdf_with_outline)
    app.output_var.set(str(tmp_path / "x.json"))
    app.fake_var.set(True)
    app._toggle_all()
    assert app._selected() == set()
    assert app.estimate_var.get() == "Nessun capitolo spuntato."
    app._start_build()
    assert "almeno un capitolo" in dialogs["errors"][-1]
    assert not app.busy
    app._toggle_all()
    assert app._selected() == {1, 2, 3, 4}


def test_real_click_toggles_the_box_and_not_the_row(app, root, pdf_with_outline):
    root.deiconify()
    load(app, root, pdf_with_outline)
    root.update()
    assert app.current == 1  # parte dal primo capitolo spuntato
    x, y, width, height = app.tree.bbox("s2", "check")
    app.tree.event_generate("<Button-1>", x=x + width // 2, y=y + height // 2)
    root.update()
    assert 2 not in app.checked
    assert app.current == 1

    x, y, width, height = app.tree.bbox("s3", "title")
    app.tree.event_generate("<Button-1>", x=x + width // 2, y=y + height // 2)
    root.update()
    assert 3 in app.checked
    assert app.current == 3
    assert app.viewer.page == app.detection.sections[3].page_start


# --- Anteprima e pagine ----------------------------------------------------------------------------


def test_viewer_renders_pages_and_clamps_navigation(app, root, pdf_with_outline):
    load(app, root, pdf_with_outline)
    viewer = app.viewer
    assert viewer.page_count > 10
    assert viewer.image is not None and viewer.image.width() > 50
    assert viewer.page == app.detection.sections[1].page_start
    assert "capitolo 1" in app.where_var.get()
    assert "prima pagina" in app.where_var.get()

    viewer.show_page(9999)
    assert viewer.page == viewer.page_count
    viewer.show_page(-3)
    assert viewer.page == 1
    viewer.previous_page()
    assert viewer.page == 1
    viewer.next_page()
    assert viewer.page == 2
    assert "esclusa" in app.where_var.get()  # la pagina di copyright

    viewer.page_var.set("5")
    viewer._go_to_typed_page()
    assert viewer.page == 5
    viewer.page_var.set("abc")
    viewer._go_to_typed_page()
    assert viewer.page == 5 and viewer.page_var.get() == "5"

    before = viewer.image.width()
    viewer._change_zoom(2)
    assert viewer.image.width() > before
    viewer.reset_zoom()
    assert viewer.image.width() == before


def test_selecting_a_row_shows_its_first_page_and_boundary_buttons_jump(
    app, root, pdf_with_outline
):
    load(app, root, pdf_with_outline)
    app.tree.selection_set("s2")
    root.update()
    section = app.detection.sections[2]
    assert app.viewer.page == section.page_start
    assert app.title_var.get() == section.title
    app._show_boundary("end")
    assert app.viewer.page == section.page_end
    assert "ultima pagina" in app.where_var.get()
    app._show_boundary("start")
    assert app.viewer.page == section.page_start


def test_buttons_set_boundaries_from_the_shown_page_and_neighbours_follow(
    app, root, pdf_with_outline
):
    load(app, root, pdf_with_outline)
    sections = app.detection.sections
    app.tree.selection_set("s2")
    root.update()
    start = sections[2].page_start

    app.viewer.show_page(start + 1)
    app._set_boundary("start")
    assert sections[2].page_start == start + 1
    assert sections[1].page_end == start  # il capitolo prima arriva fin lì
    assert app.start_var.get() == str(start + 1)
    assert app.tree.set("s2", "pages").startswith(str(start + 1))
    assert app.viewer.page == start + 1  # l'anteprima non salta
    assert app.chapters_dirty
    assert "modificata a mano" in app.info_var.get()

    app.viewer.show_page(start - 2)
    app._set_boundary("end")
    assert "non può precedere" in app.editor_message_var.get()


def test_editor_validates_and_applies_title_and_pages(app, root, pdf_with_outline):
    load(app, root, pdf_with_outline)
    section = app.detection.sections[1]
    app.title_var.set("  ")
    app._apply_editor()
    assert "vuoto" in app.editor_message_var.get()

    app.title_var.set("Titolo nuovo")
    app.end_var.set("abc")
    app._apply_editor()
    assert "numeri" in app.editor_message_var.get()

    app.end_var.set("99999")
    app._apply_editor()
    assert "pagine devono" in app.editor_message_var.get()
    assert section.title != "Titolo nuovo"

    app.end_var.set(str(section.page_end))
    app._apply_editor()
    assert section.title == "Titolo nuovo"
    assert app.tree.set("s1", "title") == "Titolo nuovo"
    assert app.editor_message_var.get() == ""


def test_shrinking_a_chapter_too_much_unchecks_it_and_growing_restores(app, root, pdf_with_outline):
    load(app, root, pdf_with_outline)
    position = 1
    section = app.detection.sections[position]
    start, end = section.page_start, section.page_end
    for page in range(start, end + 1):
        app.pages[page] = "testo " * 100  # 100 parole a pagina
    app.tree.selection_set(f"s{position}")
    root.update()
    app.start_var.set(str(start))
    app.end_var.set(str(start))
    app._apply_editor()
    assert position not in app.checked
    assert app.tree.set(f"s{position}", "state") == "troppo breve"
    app.end_var.set(str(end))
    app._apply_editor()
    assert position in app.checked


def test_edits_reach_the_generated_pack_and_saved_file(
    app, root, pdf_with_outline, tmp_path, monkeypatch
):
    load(app, root, pdf_with_outline)
    app.tree.selection_set("s1")
    root.update()
    app.title_var.set("Corretto a mano")
    app._apply_editor()

    saved = tmp_path / "corretti.toc.yaml"
    monkeypatch.setattr(gui_module.filedialog, "asksaveasfilename", lambda **_: str(saved))
    app._export_toc()
    assert "Corretto a mano" in saved.read_text("utf-8")
    assert app.toc_var.get() == str(saved)
    assert not app.chapters_dirty

    output = tmp_path / "pack.bookpack.json"
    app.output_var.set(str(output))
    app.fake_var.set(True)
    app._start_build()
    pump(root, lambda: not app.busy)
    pack, report = validate_data(json.loads(output.read_text("utf-8")))
    assert report.ok, report.errors
    assert pack.chapters[0].title == "Corretto a mano"


def test_changes_during_a_build_do_not_affect_it(app, root, pdf_with_outline, tmp_path):
    load(app, root, pdf_with_outline)
    output = tmp_path / "pack.bookpack.json"
    app.output_var.set(str(output))
    app.fake_var.set(True)
    original = app.detection.sections[1].title
    app._start_build()
    app.detection.sections[1].title = "Cambiato durante"
    pump(root, lambda: not app.busy)
    pack, _ = validate_data(json.loads(output.read_text("utf-8")))
    assert pack.chapters[0].title == original


def test_unsaved_edits_ask_before_being_discarded(app, root, pdf_with_outline, dialogs):
    load(app, root, pdf_with_outline)
    app.tree.selection_set("s1")
    root.update()
    app.title_var.set("Modificato")
    app._apply_editor()
    dialogs["answer"] = False

    app.include_all_var.set(True)
    app._on_include_all()
    assert app.include_all_var.get() is False
    assert app.detection.sections[1].title == "Modificato"
    assert "senza salvarli" in dialogs["questions"][-1]

    dialogs["answer"] = True
    app.include_all_var.set(True)
    app._on_include_all()
    assert app.detection.sections[1].title != "Modificato"
    assert not app.chapters_dirty


def test_changing_a_page_field_moves_the_preview_to_that_boundary(app, root, pdf_with_outline):
    load(app, root, pdf_with_outline)
    section = app.detection.sections[1]
    app.end_var.set(str(section.page_end - 1))
    app._apply_editor()
    assert app.viewer.page == section.page_end
    assert "ultima pagina" in app.where_var.get()

    app.start_var.set(str(section.page_start + 1))
    app._apply_editor()
    assert app.viewer.page == section.page_start
    assert "prima pagina" in app.where_var.get()


def test_typed_page_is_applied_to_the_old_row_when_clicking_another(app, root, pdf_with_outline):
    root.deiconify()
    load(app, root, pdf_with_outline)
    root.update()
    sections = app.detection.sections
    old_end = sections[1].page_end

    app.end_spin.focus_force()
    root.update()
    app.end_var.set(str(old_end - 1))
    x, y, width, height = app.tree.bbox("s3", "title")
    app.tree.event_generate("<Button-1>", x=x + width // 2, y=y + height // 2)
    root.update()

    assert sections[1].page_end == old_end - 1  # la modifica va alla riga di prima
    assert sections[2].page_start == old_end  # il vicino segue il confine
    assert app.current == 3
    assert app.end_var.get() == str(sections[3].page_end)
