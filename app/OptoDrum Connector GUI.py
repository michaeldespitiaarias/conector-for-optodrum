"""
OptoDrum Connector: desktop front end.

The same visual language as the VisoLab applications (tokens in
design.py, controls in widgets.py) in the tool's own slate grey, scoped to
its one job: turn OptoDrum `.summary` staircase exports into one
`optodrum_report.csv`. There is no Statistical Analysis or Plots mode; the
report is a plain measurement table for whatever statistics or plotting
tool comes next.

Anatomy: a start screen, then one page. A slim top bar carries the name,
Help and the interface language; the page holds a single card with the
inputs and the output location, and a footer with Back and Run. Run turns
the page into a progress card that ends with what was written and the
button that opens it.

Structured as a class with bound run methods, so a run can be driven
headlessly by tests with no Tk event loop behind it.
"""
from __future__ import annotations

import contextlib
import io
import os
import re
import sys
import threading
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_APP_DIR)
if getattr(sys, "frozen", False):
    # Packaged build (PyInstaller): sibling source folders are bundled
    # into the executable itself, so every path resolves against the
    # bundle's extraction root instead of __file__'s location.
    _ROOT_DIR = sys._MEIPASS
    _APP_DIR = _ROOT_DIR
_SAMPLES_DATA_DIR = os.path.join(_ROOT_DIR, "samples", "data")
for _p in (_APP_DIR,
           os.path.join(_ROOT_DIR, "helpers"),
           os.path.join(_ROOT_DIR, "steps", "optodrum")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from theme import WIN_H, WIN_H_MIN, _MODE_THEMES  # noqa: E402
from design import (  # noqa: E402
    C_APP_BG, C_BORDER, C_DANGER, C_DIVIDER, C_SUCCESS, C_SURFACE, C_TEXT,
    C_TEXT_2, C_TEXT_3, C_WARN, CARD_PAD, CONTENT_MAX, CONTROL_H, F_BODY,
    F_BODY_B, F_DISPLAY, F_PAGE, F_SECTION, F_SMALL, F_SMALL_B, SP_1, SP_2,
    SP_3, SP_4, SP_6, SP_8,
)
from help_modal import show_help  # noqa: E402
from i18n import plural, set_language, tr, trf  # noqa: E402
from runtime_support import (  # noqa: E402
    apply_platform_scaling, bundled_examples, fit_to_screen,
    install_example, install_tk_error_handler, load_settings, open_path,
    save_settings, set_window_icon, start_logging,
)
from widgets import (GradientProgressBar, RoundedButton,  # noqa: E402
                     RoundedEntry, ScrollFrame, set_accent)

from design import set_appearance  # noqa: E402
from widgets import (adapt_image, apply_window_appearance,  # noqa: E402
                     show_settings_dialog, watch_system_appearance)
from metadata_io import find_metadata_path  # noqa: E402

from optodrum import count_files, process_optodrum  # noqa: E402

try:
    from PIL import Image, ImageTk
    _PIL = True
except Exception:                                   # pragma: no cover
    _PIL = False


APP_NAME = "OptoDrum Connector"
APP_VERSION = "1.1.0"
TAGLINE = "OptoDrum staircase exports, one structured report"

_WIN_W = 980
_WIN_MIN_W = 760
_FIELD_LABEL_W = 150

_HOME_INTRO = ("Pick the folder with the OptoDrum sessions and where the "
               "report goes, then press Run.")


class OptoDrumApp:
    def __init__(self):
        self.root = tk.Tk()
        apply_platform_scaling(self.root)
        self.root.title(APP_NAME)
        fit_to_screen(self.root, _WIN_W, WIN_H, _WIN_MIN_W, WIN_H_MIN)
        set_window_icon(self.root, os.path.join(_ROOT_DIR, "assets"))
        install_tk_error_handler(self.root, APP_NAME)
        self._settings = load_settings(APP_NAME)
        set_appearance(self._settings.get("appearance", "system"))
        self.root.configure(bg=C_APP_BG)
        apply_window_appearance(self.root)
        watch_system_appearance(self.root, self._rebuild_ui)
        set_language(self._settings.get("language", "en"))
        set_accent(_MODE_THEMES["home"])

        self.mode = None            # None on the start screen and Home
        self._view = "welcome"
        self._welcome = None

        self.data_var = tk.StringVar()
        self.metadata_path_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.project_var = tk.StringVar()
        self._project_name_edited = False
        self.data_var.trace_add("write",
                                lambda *_a: self._on_data_folder_change())
        self.output_var.trace_add("write", lambda *_a: self._sync_home_state())
        self.project_var.trace_add("write",
                                   lambda *_a: self._sync_home_state())
        self.data_var.trace_add("write",
                                lambda *_a: self._suggest_project_name())
        self.output_var.trace_add("write",
                                  lambda *_a: self._suggest_project_name())

        self._file_count = 0
        self._running = False
        self._cancel_flag = threading.Event()
        self._fluid = []          # (widget, margin) for width-adaptive text
        self.output_csv_path = None
        self._run_log = ""

        self._build_chrome()
        self.root.bind("<Configure>", self._on_resize)
        self._show_welcome()

    # ── Persistent chrome ─────────────────────────────────────────────
    def _build_chrome(self):
        """Top bar (name, Help, language), the page, and a footer with the
        page's buttons. The footer is packed before the page body whenever
        it is shown, so it always owns its strip."""
        self.topbar = tk.Frame(self.root, bg=C_SURFACE)
        self.topbar.pack(fill="x")
        self._topbar_line = tk.Frame(self.root, bg=C_BORDER, height=1)
        self._topbar_line.pack(fill="x")

        self.nav_wrap = tk.Frame(self.root, bg=C_SURFACE)
        tk.Frame(self.nav_wrap, height=1, bg=C_BORDER).pack(fill="x")
        nav_row = tk.Frame(self.nav_wrap, bg=C_SURFACE)
        nav_row.pack(fill="x", padx=SP_8, pady=SP_3)
        self.start_btn = RoundedButton(nav_row, text=tr("Run"),
                                       command=self._start_run,
                                       variant="primary", min_width=120)
        self.start_btn.pack(side="right")
        self.back_btn = RoundedButton(nav_row, text=tr("Back"),
                                      command=self._show_welcome,
                                      variant="secondary", min_width=96)
        self.back_btn.pack(side="right", padx=(0, SP_2))
        self.cancel_btn = RoundedButton(nav_row, text=tr("Cancel"),
                                        command=self._cancel_run,
                                        variant="secondary", min_width=96)
        self._nav_msg = tk.Label(nav_row, text="", font=F_SMALL,
                                 fg=C_TEXT_3, bg=C_SURFACE, anchor="w",
                                 justify="left", width=1)
        self._nav_msg.pack(side="left", fill="x", expand=True,
                           padx=(0, SP_4))

        self.body = tk.Frame(self.root, bg=C_APP_BG)
        self.body.pack(fill="both", expand=True)

    def _theme(self):
        return _MODE_THEMES["home"]

    def _clear_body(self):
        self._fluid.clear()
        for w in self.body.winfo_children():
            w.destroy()

    def _content_width(self):
        w = self.root.winfo_width()
        return max(400, w - 2 * SP_8)

    def _fluid_label(self, parent, text, margin=0, **kw):
        """A label whose wrap length follows the page width."""
        lbl = tk.Label(parent, text=text, justify="left", anchor="w", **kw)
        self._fluid.append((lbl, margin))
        lbl.configure(wraplength=min(CONTENT_MAX,
                                     max(300, self._content_width() - margin)))
        return lbl

    def _on_resize(self, evt=None):
        if evt is not None and evt.widget is not self.root:
            return
        width = self._content_width()
        for lbl, margin in list(self._fluid):
            try:
                lbl.configure(wraplength=min(CONTENT_MAX,
                                             max(300, width - margin)))
            except tk.TclError:
                self._fluid.remove((lbl, margin))

    def _render_topbar(self):
        bar = self.topbar
        for w in bar.winfo_children():
            w.destroy()
        row = tk.Frame(bar, bg=C_SURFACE)
        row.pack(fill="x", padx=SP_6, pady=SP_2)
        mark = self._icon_image(26)
        if mark is not None:
            lbl = tk.Label(row, image=mark, bg=C_SURFACE, bd=0)
            lbl._img = mark
            lbl.pack(side="left", padx=(0, SP_2))
        tk.Label(row, text=APP_NAME, font=F_BODY_B, fg=C_TEXT,
                 bg=C_SURFACE).pack(side="left")
        RoundedButton(row, text=tr("Help"), variant="ghost",
                      command=lambda: self._show_help("home")).pack(
            side="right")
        RoundedButton(row, text=tr("Settings"), variant="ghost",
                      command=self._show_settings).pack(side="right")

    def _icon_image(self, size):
        if not _PIL:
            return None
        try:
            pil = Image.open(os.path.join(_ROOT_DIR, "assets",
                                          "app_icon.png")).convert("RGBA")
            return ImageTk.PhotoImage(adapt_image(
                pil.resize((size, size), Image.LANCZOS)))
        except (FileNotFoundError, OSError):
            return None

    def _show_help(self, key):
        show_help(self.root, key or "home", "home")

    def _show_settings(self):
        show_settings_dialog(self.root, self._set_language,
                             self._set_appearance,
                             reopen=self._show_settings)

    def _set_language(self, code):
        code = set_language(code)
        self._settings["language"] = code
        save_settings(APP_NAME, self._settings)
        self._rebuild_ui()

    def _set_appearance(self, mode):
        mode = set_appearance(mode)
        self._settings["appearance"] = mode
        save_settings(APP_NAME, self._settings)
        self._rebuild_ui()

    def _rebuild_ui(self):
        """Redraw the window in the language and appearance in force, on
        the page the user was on, with every field kept."""
        view = self._view
        for w in self.root.winfo_children():
            w.destroy()
        self._welcome = None
        self._fluid.clear()
        self.root.configure(bg=C_APP_BG)
        apply_window_appearance(self.root)
        self._build_chrome()
        if view == "home":
            self._show_home()
        elif view == "run":
            self._show_running()
            end = getattr(self, "_run_end", None)
            if not self._running and end:
                if end[0] == "done":
                    self._run_finished()
                elif end[0] == "cancelled":
                    self._run_cancelled()
                else:
                    self._run_failed(end[1], notify=False)
        else:
            self._show_welcome()

    def _card(self, parent):
        return tk.Frame(parent, bg=C_SURFACE, highlightthickness=1,
                        highlightbackground=C_BORDER,
                        highlightcolor=C_BORDER)

    def _page_column(self):
        """A scrolling page with the standard margins."""
        page = ScrollFrame(self.body, bg=C_APP_BG)
        page.pack(fill="both", expand=True)
        column = tk.Frame(page.inner, bg=C_APP_BG)
        column.pack(fill="x", pady=(SP_6, SP_6), padx=SP_8)
        return column

    # ── Welcome ───────────────────────────────────────────────────────
    def _show_welcome(self):
        """Start screen: the mark, one sentence, and the way in."""
        self.mode = None
        self._view = "welcome"
        self._clear_body()
        self.nav_wrap.pack_forget()
        old = getattr(self, "_welcome", None)
        if old is not None:
            try:
                old.destroy()
            except tk.TclError:
                pass

        welcome = tk.Frame(self.root, bg=C_SURFACE)
        welcome.place(x=0, y=0, relwidth=1, relheight=1)
        welcome.lift()
        self._welcome = welcome

        corner = tk.Frame(welcome, bg=C_SURFACE)
        corner.place(relx=1.0, x=-SP_6, y=SP_6, anchor="ne")
        RoundedButton(corner, text=tr("Settings"), variant="secondary",
                      height=28, command=self._show_settings).pack(
            side="left", padx=(0, SP_2))
        RoundedButton(corner, text="?", variant="secondary", width=30,
                      min_width=30, padding=0, height=28,
                      command=lambda: self._show_help("welcome")).pack(
            side="left")

        inner = tk.Frame(welcome, bg=C_SURFACE)
        inner.place(relx=0.5, rely=0.46, anchor="center")
        logo_path = os.path.join(_ROOT_DIR, "assets", "Optodrum_logo.png")
        if _PIL:
            try:
                pil = Image.open(logo_path).convert("RGBA")
                logo_w = 220
                pil = pil.resize((logo_w, int(logo_w * pil.height
                                              / max(1, pil.width))),
                                 Image.LANCZOS)
                photo = ImageTk.PhotoImage(adapt_image(pil))
                lbl = tk.Label(inner, image=photo, bg=C_SURFACE, bd=0)
                lbl._welcome_photo = photo
                lbl.pack(pady=(0, SP_4))
            except (FileNotFoundError, OSError):
                pass
        tk.Label(inner, text=APP_NAME, font=F_DISPLAY, fg=C_TEXT,
                 bg=C_SURFACE).pack()
        tk.Label(inner, text=tr(TAGLINE), font=F_BODY, fg=C_TEXT_2,
                 bg=C_SURFACE).pack(pady=(SP_1, 0))
        RoundedButton(inner, text=tr("Get started"), command=self._show_home,
                      variant="primary", min_width=150,
                      height=34).pack(pady=(SP_6, 0))

        tk.Label(welcome, text=f"{APP_NAME} {APP_VERSION}", font=F_SMALL,
                 fg=C_TEXT_3, bg=C_SURFACE).place(relx=0.5, rely=1.0,
                                                  y=-SP_4, anchor="s")

    # ── Home ──────────────────────────────────────────────────────────
    def _show_home(self):
        self.mode = None
        self._view = "home"
        old = getattr(self, "_welcome", None)
        if old is not None:
            try:
                old.destroy()
            except tk.TclError:
                pass
            self._welcome = None
        self._clear_body()
        self._render_topbar()
        self.cancel_btn.pack_forget()
        self.start_btn.pack(side="right")
        self.back_btn.pack(side="right", padx=(0, SP_2))
        self.nav_wrap.pack(fill="x", side="bottom", before=self.body)

        column = self._page_column()
        head = tk.Frame(column, bg=C_APP_BG)
        head.pack(fill="x")
        tk.Label(head, text=tr("Convert OptoDrum exports"), font=F_PAGE,
                 fg=C_TEXT, bg=C_APP_BG, anchor="w").pack(side="left")
        self._fluid_label(column, tr(_HOME_INTRO), font=F_BODY, bg=C_APP_BG,
                          fg=C_TEXT_2).pack(fill="x", anchor="w",
                                            pady=(SP_1, SP_4))

        card = self._card(column)
        card.pack(fill="x")
        self._section(card, "Input", first=True)
        self._labeled_entry(card, "Data folder", self.data_var,
                            browse=self._browse_data_folder)
        self._labeled_entry(card, "Metadata", self.metadata_path_var,
                            browse=self._browse_metadata,
                            hint="Optional. Found automatically when it "
                                 "sits in the data folder.")
        self._section(card, "Output")
        self._labeled_entry(card, "Output folder", self.output_var,
                            browse=self._browse_output_folder)
        self._labeled_entry(card, "Project name", self.project_var,
                            hint="The report is written to Output folder, "
                                 "in a subfolder with this name.")

        status = tk.Frame(card, bg=C_SURFACE)
        status.pack(fill="x", padx=CARD_PAD, pady=(SP_2, CARD_PAD))
        tk.Frame(status, bg=C_DIVIDER, height=1).pack(fill="x",
                                                      pady=(0, SP_3))
        self._file_count_lbl = self._fluid_label(
            status, "", margin=2 * CARD_PAD, font=F_BODY_B, bg=C_SURFACE,
            fg=C_TEXT)
        self._file_count_lbl.pack(fill="x", anchor="w")
        self._example_link(column)

        self._refresh_data_state()
        self._suggest_project_name()
        self._sync_home_state()

    def _section(self, card, title, first=False):
        if not first:
            tk.Frame(card, bg=C_DIVIDER, height=1).pack(
                fill="x", padx=CARD_PAD, pady=(SP_2, 0))
        tk.Label(card, text=tr(title), font=F_SECTION, fg=C_TEXT,
                 bg=C_SURFACE, anchor="w").pack(
            fill="x", padx=CARD_PAD,
            pady=(CARD_PAD if first else SP_4, SP_2))

    def _labeled_entry(self, parent, label, var, browse=None, hint=None):
        row = tk.Frame(parent, bg=C_SURFACE)
        row.pack(fill="x", padx=CARD_PAD, pady=(0, SP_1 if hint else SP_3))
        lab = tk.Frame(row, bg=C_SURFACE, width=_FIELD_LABEL_W,
                       height=CONTROL_H)
        lab.pack(side="left")
        lab.pack_propagate(False)
        tk.Label(lab, text=tr(label), font=F_BODY, bg=C_SURFACE, fg=C_TEXT,
                 anchor="w").pack(side="left", fill="y")
        if browse is not None:
            RoundedButton(row, text=tr("Browse…"), command=browse,
                          variant="secondary").pack(side="right",
                                                    padx=(SP_2, 0))
        entry = RoundedEntry(row, textvariable=var,
                             show_end=var is not self.project_var)
        entry.pack(side="left", fill="x", expand=True)
        if var is self.project_var:
            def _mark_edited(_e=None):
                self._project_name_edited = True
            entry.entry.bind("<Key>", _mark_edited, add="+")
        if hint:
            self._fluid_label(
                parent, tr(hint), margin=2 * CARD_PAD + _FIELD_LABEL_W,
                font=F_SMALL, fg=C_TEXT_3, bg=C_SURFACE).pack(
                fill="x", anchor="w",
                padx=(CARD_PAD + _FIELD_LABEL_W, CARD_PAD), pady=(0, SP_3))

    def _browse_folder(self, var):
        # Starts wherever *var* already points, then Data folder, then the
        # last folder picked in any session, so Browse never opens inside
        # an unrelated directory the OS happened to remember.
        start = var.get().strip()
        if not (start and os.path.isdir(start)):
            start = self.data_var.get().strip()
        if not (start and os.path.isdir(start)):
            start = self._settings.get("last_folder", "")
        folder = filedialog.askdirectory(
            title=tr("Choose a folder"),
            initialdir=start if start and os.path.isdir(start) else None)
        if folder:
            var.set(folder)
            self._settings["last_folder"] = os.path.dirname(folder)
            save_settings(APP_NAME, self._settings)

    def _browse_data_folder(self):
        self._browse_folder(self.data_var)

    def _browse_output_folder(self):
        self._browse_folder(self.output_var)

    def _browse_metadata(self):
        kw = {"title": tr("Choose the metadata file"),
              "filetypes": [(tr("Tables (CSV / Excel / TSV)"),
                             "*.csv *.xlsx *.xls *.txt"),
                            (tr("All files"), "*.*")]}
        start = self.metadata_path_var.get().strip()
        if start and os.path.isfile(start):
            kw["initialdir"] = os.path.dirname(start)
        else:
            input_dir = self._input_dir()
            if input_dir and os.path.isdir(input_dir):
                kw["initialdir"] = input_dir
        path = filedialog.askopenfilename(**kw)
        if path:
            self.metadata_path_var.set(path)

    def _suggest_project_name(self):
        """Waits for both folders, then proposes "{data folder's own
        basename} results". Never overwrites a name the user typed
        (self._project_name_edited) or a value already there."""
        if self._project_name_edited:
            return
        if self.project_var.get().strip():
            return
        if not self.output_var.get().strip():
            return
        data_folder = self.data_var.get().strip()
        if not data_folder or not os.path.isdir(data_folder):
            return
        name = os.path.basename(data_folder.rstrip(os.sep))
        if name:
            self.project_var.set(f"{name} results")

    def _input_dir(self):
        """Data folder is read directly: whatever is picked is assumed to
        hold the `.summary` session subfolders."""
        data_folder = self.data_var.get().strip()
        return data_folder if data_folder and os.path.isdir(data_folder) \
            else None

    def _output_dir(self):
        """{Output folder}/{Project}/, with no extra domain subfolder."""
        out = self.output_var.get().strip()
        proj = self.project_var.get().strip()
        if not out or not proj:
            return None
        return os.path.join(out, proj)

    def _folders_ready(self):
        return bool(self.data_var.get().strip()
                    and self.output_var.get().strip()
                    and self.project_var.get().strip())

    def _refresh_data_state(self):
        """Counts the `.summary` files under Data folder and looks for the
        metadata table there when none is set."""
        input_dir = self._input_dir()
        self._file_count = count_files(input_dir) if input_dir else 0
        if not self.metadata_path_var.get().strip() and input_dir:
            found = find_metadata_path(input_dir)
            if found:
                self.metadata_path_var.set(found)

    def _on_data_folder_change(self):
        """A new Data folder invalidates metadata found under the previous
        one, so that is cleared before looking again."""
        self.metadata_path_var.set("")
        self._refresh_data_state()
        self._sync_home_state()

    def _sync_home_state(self):
        lbl = getattr(self, "_file_count_lbl", None)
        btn = getattr(self, "start_btn", None)
        if lbl is None or btn is None:
            return   # traces can fire before Home has finished building
        input_dir = self._input_dir()
        data_folder = self.data_var.get().strip()
        colour = C_TEXT
        if not data_folder:
            text, colour = tr("Pick the data folder to begin."), C_TEXT_2
        elif input_dir is None:
            text = trf("\"{folder}\" is not a folder.", folder=data_folder)
            colour = C_WARN
        elif self._file_count == 0:
            text = tr("No .summary files were found in this folder or the "
                      "folders inside it.")
            colour = C_WARN
        else:
            text = plural(self._file_count, "{n} .summary file found",
                          "{n} .summary files found")
        ready = bool(input_dir and self._folders_ready()
                     and self._file_count > 0)
        why = ""
        if input_dir and self._file_count and not self._folders_ready():
            why = tr("Set the output folder and a project name to run.")
        try:
            lbl.configure(text=text, fg=colour)
            btn.configure(state="normal" if ready else "disabled")
            self._nav_msg.configure(text=why)
        except tk.TclError:
            pass

    def _cancel_run(self):
        """Leaves the running page. The engine's progress callback checks
        `_cancel_flag` and stops at the next file, so a Cancel here really
        stops the conversion instead of letting it finish unattended."""
        if self._running:
            self._cancel_flag.set()
        self._show_home()

    # ── Run execution ─────────────────────────────────────────────────
    def _start_run(self):
        if self._running:
            return
        self._running = True
        self._run_end = None
        self._cancel_flag.clear()
        self._show_running()
        threading.Thread(target=self._do_run, daemon=True).start()

    def _post(self, pct, message):
        def apply():
            try:
                self.progress.set(pct)
                self._pct_lbl.config(text=f"{int(pct)} %")
                self.status_lbl.config(text=message)
            except (AttributeError, tk.TclError):
                pass
        self.root.after(0, apply)

    def _do_run(self):
        try:
            inp = self._input_dir()
            out = self._output_dir()
            meta = self.metadata_path_var.get().strip() or None

            def on_progress(current, total, filename):
                if self._cancel_flag.is_set():
                    raise InterruptedError("Cancelled by user.")
                pct = (current / max(1, total)) * 100
                self._post(pct, trf("Reading {file}  ·  {current} of {total}",
                                    file=filename, current=current,
                                    total=total))

            self._post(0, tr("Starting…"))
            # The engine reports skipped folders and unreadable files only
            # by printing them; keep that text to say so on the page.
            log = io.StringIO()
            with contextlib.redirect_stdout(log):
                result_path = process_optodrum(inp, out, metadata_path=meta,
                                               on_progress=on_progress)
            self._run_log = log.getvalue()
            sys.stdout.write(self._run_log)
            self.output_csv_path = result_path
            self.root.after(0, self._run_finished)
        except InterruptedError:
            self.root.after(0, self._run_cancelled)
        except Exception as exc:                       # noqa: BLE001
            try:
                out_dir = self._output_dir() or "."
                os.makedirs(out_dir, exist_ok=True)
                with open(os.path.join(out_dir, "error.log"), "w",
                          encoding="utf-8") as fh:
                    fh.write(traceback.format_exc())
            except OSError:
                pass
            self.root.after(0, self._run_failed, str(exc))

    def _run_outcome(self):
        """What the run produced, and what it had to leave out."""
        skipped = len(re.findall(r"unexpected folder name format",
                                 self._run_log))
        unreadable = len(re.findall(r"could not read", self._run_log))
        parts = []
        path = self.output_csv_path
        if path and os.path.isfile(path):
            try:
                import pandas as pd
                report = pd.read_csv(path)
                parts.append(plural(len(report), "{n} row written",
                                    "{n} rows written"))
                parts.append(plural(report["Mouse_ID"].nunique(),
                                    "{n} animal", "{n} animals"))
            except Exception:                           # noqa: BLE001
                parts.append(tr("Report written."))
        else:
            parts.append(tr("No results could be extracted, so no report "
                            "was written."))
        line = "  ·  ".join(parts)
        notes = []
        if skipped:
            notes.append(plural(skipped,
                                "{n} file skipped: its folder name does not "
                                "follow <year>_mouse_<Mouse_ID>_<Experiment>"
                                "_<Test_Type>",
                                "{n} files skipped: their folder names do "
                                "not follow <year>_mouse_<Mouse_ID>_"
                                "<Experiment>_<Test_Type>"))
        if unreadable:
            notes.append(plural(unreadable, "{n} file could not be read",
                                "{n} files could not be read"))
        return line, notes

    def _run_finished(self):
        self._running = False
        self._run_end = ("done", None)
        line, notes = self._run_outcome()
        ok = bool(self.output_csv_path and
                  os.path.isfile(self.output_csv_path))
        for action in (lambda: self.progress.set(100 if ok else 0),
                       lambda: self._pct_lbl.config(text="100 %" if ok
                                                    else ""),
                       lambda: self._run_title.config(
                           text=tr("Report ready" if ok else
                                   "Nothing to report"),
                           fg=C_SUCCESS if ok else C_WARN),
                       lambda: self.status_lbl.config(text=line),
                       lambda: self._show_notes(notes),
                       lambda: self.cancel_btn.configure(text=tr("Back"),
                                                         state="normal"),
                       self._show_run_links):
            try:
                action()
            except (AttributeError, tk.TclError):
                pass

    def _run_cancelled(self):
        self._running = False
        self._run_end = ("cancelled", None)
        for action in (lambda: self._run_title.config(text=tr("Cancelled"),
                                                      fg=C_TEXT_2),
                       lambda: self.status_lbl.config(text=""),
                       lambda: self.cancel_btn.configure(text=tr("Back"),
                                                         state="normal")):
            try:
                action()
            except (AttributeError, tk.TclError):
                pass

    def _run_failed(self, message, notify=True):
        self._running = False
        self._run_end = ("failed", message)
        for action in (lambda: self.progress.set(0),
                       lambda: self._pct_lbl.config(text=""),
                       lambda: self._run_title.config(
                           text=tr("The conversion stopped"), fg=C_DANGER),
                       lambda: self.cancel_btn.configure(text=tr("Back"),
                                                         state="normal"),
                       lambda: self.status_lbl.config(text=message)):
            try:
                action()
            except (AttributeError, tk.TclError):
                pass
        if notify:
            messagebox.showerror(
                f"{APP_NAME}: " + tr("the conversion stopped"), message)

    def _open_output_folder(self):
        path = self._output_dir()
        if path and os.path.isdir(path):
            open_path(os.path.abspath(path))

    # ── Running page ──────────────────────────────────────────────────
    def _show_running(self):
        self._view = "run"
        self._clear_body()
        self._render_topbar()
        th = self._theme()
        for btn in (self.back_btn, self.start_btn):
            btn.pack_forget()
        self.cancel_btn.configure(text=tr("Cancel"), state="normal")
        self.cancel_btn.pack(side="right")
        self._nav_msg.configure(text="")
        self.nav_wrap.pack(fill="x", side="bottom", before=self.body)

        holder = tk.Frame(self.body, bg=C_APP_BG)
        holder.pack(fill="both", expand=True)
        card = self._card(holder)
        card.place(relx=0.5, rely=0.42, anchor="center", width=600)
        inner = tk.Frame(card, bg=C_SURFACE)
        inner.pack(fill="both", expand=True, padx=SP_8, pady=SP_8)

        self._run_title = tk.Label(inner, text=tr("Converting the exports"),
                                   font=F_SECTION, fg=C_TEXT, bg=C_SURFACE,
                                   anchor="w")
        self._run_title.pack(fill="x")
        self.status_lbl = tk.Label(inner, text=tr("Starting…"),
                                   font=F_SMALL, fg=C_TEXT_2, bg=C_SURFACE,
                                   wraplength=520, justify="left",
                                   anchor="w")
        self.status_lbl.pack(fill="x", pady=(SP_1, SP_4))
        bar_row = tk.Frame(inner, bg=C_SURFACE)
        bar_row.pack(fill="x")
        self.progress = GradientProgressBar(bar_row, width=472, height=6,
                                            bg=C_SURFACE)
        self.progress.set_theme(th["primary_dark"], th["primary"])
        self.progress.pack(side="left")
        self._pct_lbl = tk.Label(bar_row, text="0 %", font=F_SMALL_B,
                                 fg=C_TEXT_2, bg=C_SURFACE, width=6,
                                 anchor="e")
        self._pct_lbl.pack(side="right")

        self._notes = tk.Frame(inner, bg=C_SURFACE)
        self._run_links = tk.Frame(inner, bg=C_SURFACE)
        self._open_folder_btn = RoundedButton(
            self._run_links, text=tr("Open folder"),
            command=self._open_output_folder, variant="primary")

    def _show_notes(self, notes):
        for w in self._notes.winfo_children():
            w.destroy()
        for note in notes:
            tk.Label(self._notes, text=note, font=F_SMALL, fg=C_WARN,
                     bg=C_SURFACE, anchor="w", justify="left",
                     wraplength=520).pack(fill="x", anchor="w")
        if notes:
            self._notes.pack(fill="x", pady=(SP_3, 0))

    def _show_run_links(self):
        try:
            self._open_folder_btn.pack_forget()
        except tk.TclError:
            return
        if os.path.isdir(self._output_dir() or ""):
            self._open_folder_btn.pack(side="left")
            self._run_links.pack(fill="x", pady=(SP_6, 0))

    # ── Bundled example ───────────────────────────────────────────────
    def _example_link(self, parent):
        """Fills every field from the demo shipped with the app, copied to
        a writable folder first (see runtime_support.install_example).
        Hidden when no example is bundled."""
        names = bundled_examples(_SAMPLES_DATA_DIR)
        if not names:
            return
        th = self._theme()
        link = tk.Label(parent, text=tr("No data at hand? Load an example "
                                        "project") + "  ▸",
                        font=F_SMALL_B, bg=C_APP_BG, fg=th["accent"])
        link.pack(anchor="w", pady=(SP_3, 0))
        link.bind("<Enter>", lambda _e: link.configure(fg=th["accent_hover"]))
        link.bind("<Leave>", lambda _e: link.configure(fg=th["accent"]))

        def _choose(name):
            try:
                info = install_example(APP_NAME, _SAMPLES_DATA_DIR, name)
            except Exception as exc:
                messagebox.showerror(APP_NAME,
                                     tr("Could not prepare the example:")
                                     + f"\n{exc}")
                return
            self.project_var.set("")
            self.data_var.set(info["data"])
            self.output_var.set(info["output"])
            self.project_var.set(info["project"])

        def _open(event):
            if len(names) == 1:
                _choose(names[0])
                return
            menu = tk.Menu(self.root, tearoff=0)
            for name in names:
                menu.add_command(label=name, command=lambda n=name: _choose(n))
            menu.tk_popup(event.x_root, event.y_root)

        link.bind("<Button-1>", _open)

    def run(self):
        self.root.mainloop()


def launch_gui():
    OptoDrumApp().run()


if __name__ == "__main__":
    # Must come first in a packaged build; see multiprocessing's docs.
    import multiprocessing
    multiprocessing.freeze_support()
    start_logging(APP_NAME, APP_VERSION)
    if "--selftest" in sys.argv:
        import selftest
        sys.exit(selftest.main())
    launch_gui()
