"""
OptoDrum Connector: desktop front end.

Built to a consistent desktop app anatomy: welcome splash, then a Home
page, a persistent bottom nav row, and a "?" help control top right on
every page. OptoDrum Connector stays an independent tool with its own
grey identity, scoped to the connector's one existing job. There is no
Statistical Analysis mode and no Plots mode here. Its own
`optodrum_report.csv` is a plain wide format measurement table, ready
to be loaded into whatever statistics or plotting tool is needed.

No wizard: this app's own single engine call does not need one, so Home
carries everything, minimally. Four fields grouped into two sections
with a heading and a divider each: INPUT (Data folder, Metadata) and
OUTPUT (Output folder, Project), then one line of detected `.summary`
count feedback, then Back and Run in the bottom nav row. No inline
explanation, no warnings, no icon; that guidance lives in the "?" help
dialog instead, not on the page itself. Pressing Run switches to a
running page (progress, Cancel, then Back plus Open folder once it
finishes) and returns to Home when done, cancelled, or failed.

Structured as a proper class with bound run methods, not closures
inside one giant `launch_gui()` function, so a run can be driven
headlessly by tests with no live Tk event loop behind it.
"""
from __future__ import annotations

import os
import sys
import threading
import traceback
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_APP_DIR)
if getattr(sys, "frozen", False):
    # Packaged build (PyInstaller): sibling source folders are bundled
    # into the executable itself rather than sitting on disk next to
    # this script, so every path below has to resolve against the
    # bundle's own extraction root instead of __file__'s location.
    _ROOT_DIR = sys._MEIPASS
    _APP_DIR = _ROOT_DIR
for _p in (_APP_DIR,
           os.path.join(_ROOT_DIR, "_helper_skill"),
           os.path.join(_ROOT_DIR, "steps", "optodrum")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from theme import (  # noqa: E402
    C_BODY_BG, C_DIVIDER, C_MUTED, C_TEXT, C_TILE,
    FONT_BTN, FONT_LABEL, FONT_NORMAL, FONT_SMALL,
    PAD_X, PAD_Y_SEC, WIN_H, WIN_H_MIN, WIN_W,
    _MODE_THEMES,
)
from help_modal import show_help  # noqa: E402
from widgets import GradientProgressBar, RoundedButton, RoundedEntry  # noqa: E402

from metadata_io import find_metadata_path  # noqa: E402

from optodrum import count_files, process_optodrum  # noqa: E402

try:
    from PIL import Image, ImageTk
    _PIL = True
except Exception:                                   # pragma: no cover
    _PIL = False


APP_NAME = "OptoDrum Connector"
TAGLINE = "OptoDrum staircase exports, one structured report"

# Two levels above the app folder. Used only as a Browse dialog
# default, never to resolve a project path (Data folder / Output
# folder do that now).
_WORKSPACE_ROOT = os.path.abspath(os.path.join(_ROOT_DIR, "..", ".."))

_BTN_W, _BTN_H, _BTN_R = 118, 32, 16

_HOME_INTRO = (
    "Pick Data folder, Metadata, Output folder and a Project name, "
    "review the detected `.summary` count below, then Run.")


class OptoDrumApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry(f"{WIN_W}x{WIN_H}")
        self.root.minsize(760, WIN_H_MIN)
        self.root.configure(bg=C_BODY_BG)

        self.mode = None            # None on splash/Home, "home" while running

        # Home: Data folder / Metadata / Output folder / Project, all
        # with the same row anatomy (label, path entry, Browse where
        # applicable). Data folder and Output folder are browsable
        # folders; Project is a suggested but editable name.
        self.data_var = tk.StringVar()
        self.metadata_path_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.project_var = tk.StringVar()
        self._project_name_edited = False
        self.data_var.trace_add("write", lambda *_a: self._on_data_folder_change())
        self.output_var.trace_add("write", lambda *_a: self._sync_home_state())
        self.project_var.trace_add("write", lambda *_a: self._sync_home_state())
        self.data_var.trace_add("write", lambda *_a: self._suggest_project_name())
        self.output_var.trace_add("write", lambda *_a: self._suggest_project_name())

        self._file_count = 0

        self._running = False
        self._cancel_flag = threading.Event()
        self._fluid = []          # (widget, margin) for text that adapts to width
        self.output_csv_path = None

        self._build_chrome()
        self.root.bind("<Configure>", self._on_resize)
        self._show_welcome()

    # ── Persistent chrome ─────────────────────────────────────────────
    def _build_chrome(self):
        # Bottom nav first so it always owns its strip, then the body
        # fills what is left. Back and Run show on Home; Cancel (later
        # relabelled Back) shows during and after a run, never together.
        self.nav_wrap = tk.Frame(self.root, bg=C_BODY_BG)
        tk.Frame(self.nav_wrap, height=1, bg=C_DIVIDER).pack(fill="x", padx=PAD_X)
        nav_row = tk.Frame(self.nav_wrap, bg=C_BODY_BG)
        nav_row.pack(pady=(PAD_Y_SEC, PAD_Y_SEC))

        th = _MODE_THEMES["home"]
        self.back_btn = RoundedButton(
            nav_row, text="Back", command=self._show_welcome,
            bg=th["primary"], hover_bg=th["primary_dark"],
            width=_BTN_W, height=_BTN_H, radius=_BTN_R, font=FONT_BTN)
        self.back_btn.pack(side="left", padx=12)
        self.start_btn = RoundedButton(
            nav_row, text="Run", command=self._start_run,
            bg=th["primary"], hover_bg=th["primary_dark"],
            disabled_bg="#C6C9CC", disabled_fg="#F1F1F2",
            width=_BTN_W, height=_BTN_H, radius=_BTN_R, font=FONT_BTN)
        self.start_btn.pack(side="left", padx=12)
        self.cancel_btn = RoundedButton(
            nav_row, text="Cancel", command=self._cancel_run,
            bg="#8B9096", hover_bg="#6E7278",
            disabled_bg="#D4D6D9", disabled_fg="#F5F5F6",
            width=_BTN_W, height=_BTN_H, radius=_BTN_R, font=FONT_BTN)

        self.body = tk.Frame(self.root, bg=C_BODY_BG)
        self.body.pack(fill="both", expand=True)

    def _theme(self):
        return _MODE_THEMES["home"]

    def _clear_body(self):
        self._fluid.clear()
        for w in self.body.winfo_children():
            w.destroy()

    def _fluid_label(self, parent, text, margin=140, **kw):
        """A label whose wraplength follows the window width."""
        lbl = tk.Label(parent, text=text, justify="left", anchor="w", **kw)
        self._fluid.append((lbl, margin))
        lbl.configure(wraplength=max(360, self.root.winfo_width() - margin))
        return lbl

    def _on_resize(self, evt=None):
        if evt is not None and evt.widget is not self.root:
            return
        w = self.root.winfo_width()
        for lbl, margin in list(self._fluid):
            try:
                lbl.configure(wraplength=max(360, w - margin))
            except tk.TclError:
                self._fluid.remove((lbl, margin))

    # ── Header strip with the "?" control ─────────────────────────────
    def _page_header(self, parent, intro=""):
        """A short intro paragraph with the "?" help button on its
        own row above it. Everything else this app has to explain lives
        in that help dialog, not inline on the page."""
        th = self._theme()
        top = tk.Frame(parent, bg=C_BODY_BG)
        top.pack(fill="x", pady=(0, 4))
        RoundedButton(
            top, text="?", bg=th["light_bg"], hover_bg=th["light_hover"],
            fg=th["primary"], width=32, height=32, radius=16,
            font=("Helvetica", 16, "bold"),
            command=lambda: self._show_help("home")).pack(side="right")
        if intro:
            self._fluid_label(
                parent, intro, font=FONT_NORMAL, bg=C_BODY_BG,
                fg=C_MUTED).pack(fill="x", anchor="w", pady=(0, 14))
        return top

    def _show_help(self, key):
        show_help(self.root, key or "home", "home")

    # ── Welcome ───────────────────────────────────────────────────────
    def _show_welcome(self):
        """White field so the mark carries the visual weight, circular
        help control top right, centred logo / tagline / Start stack."""
        self.mode = None
        self._clear_body()
        self.nav_wrap.pack_forget()

        welcome = tk.Frame(self.body, bg=C_TILE)
        welcome.place(x=0, y=0, relwidth=1, relheight=1)
        welcome.lift()

        RoundedButton(
            welcome, text="?", bg="#EEEFF0", hover_bg="#DEE0E2",
            fg="#4B5157", width=36, height=36, radius=18,
            font=("Helvetica", 18, "bold"),
            command=lambda: self._show_help("welcome")).place(
            relx=1.0, x=-24, y=24, anchor="ne")

        inner = tk.Frame(welcome, bg=C_TILE)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        logo_path = os.path.join(_ROOT_DIR, "assets", "Optodrum_logo.png")
        LOGO_W = 320
        placed = False
        if _PIL:
            try:
                pil = Image.open(logo_path).convert("RGBA")
                aspect = pil.height / max(1, pil.width)
                pil = pil.resize((LOGO_W, int(LOGO_W * aspect)), Image.LANCZOS)
                photo = ImageTk.PhotoImage(pil)
                lbl = tk.Label(inner, image=photo, bg=C_TILE, bd=0,
                               highlightthickness=0)
                lbl._welcome_photo = photo      # prevent garbage collection
                lbl.pack(pady=(0, 10))
                placed = True
            except (FileNotFoundError, OSError):
                pass
        if not placed:
            tk.Label(inner, text=APP_NAME, font=("Helvetica", 34, "bold"),
                     fg=_MODE_THEMES["home"]["primary"],
                     bg=C_TILE).pack(pady=(4, 6))
        else:
            tk.Label(inner, text=APP_NAME, font=("Helvetica", 26, "bold"),
                     fg=_MODE_THEMES["home"]["primary"],
                     bg=C_TILE).pack(pady=(0, 6))

        tk.Label(inner, text=TAGLINE, font=("Helvetica", 16), fg=C_MUTED,
                 bg=C_TILE).pack()

        th = _MODE_THEMES["home"]

        def _on_start():
            welcome.destroy()
            self._show_home()

        RoundedButton(inner, text="Start", command=_on_start,
                      bg=th["primary"], hover_bg=th["primary_dark"],
                      fg="white", width=140, height=40, radius=20,
                      font=("Helvetica", 16, "bold")).pack(pady=(28, 0))

        tk.Label(welcome, text="v1.0", font=("Helvetica", 12), fg=C_MUTED,
                 bg=C_TILE).place(relx=0.5, rely=0.97, anchor="s")

    # ── Home ──────────────────────────────────────────────────────────
    def _show_home(self):
        self.mode = None
        self._clear_body()
        self.nav_wrap.pack(fill="x", side="bottom")
        self.cancel_btn.pack_forget()
        self.back_btn.pack(side="left", padx=12)
        self.start_btn.pack(side="left", padx=12)

        outer = tk.Frame(self.body, bg=C_BODY_BG)
        outer.pack(fill="both", expand=True, padx=PAD_X, pady=(10, 0))
        self._page_header(outer, intro=_HOME_INTRO)

        self._section_heading(outer, "INPUT")
        input_fields = tk.Frame(outer, bg=C_BODY_BG)
        input_fields.pack(fill="x", pady=(0, 8))
        self._labeled_entry(input_fields, "Data folder", self.data_var,
                            browse=self._browse_data_folder)
        self._labeled_entry(input_fields, "Metadata", self.metadata_path_var,
                            browse=self._browse_metadata)

        self._divider(outer)

        self._section_heading(outer, "OUTPUT")
        output_fields = tk.Frame(outer, bg=C_BODY_BG)
        output_fields.pack(fill="x", pady=(0, 8))
        self._labeled_entry(output_fields, "Output folder", self.output_var,
                            browse=self._browse_output_folder)
        self._labeled_entry(output_fields, "Project", self.project_var)

        self._divider(outer)

        self._file_count_lbl = self._fluid_label(
            outer, "", margin=60, font=FONT_NORMAL, bg=C_BODY_BG,
            fg=C_MUTED)
        self._file_count_lbl.pack(fill="x", anchor="w", pady=(14, 0))

        self._refresh_data_state()
        self._sync_home_state()

    def _section_heading(self, parent, title):
        th = self._theme()
        tk.Label(parent, text=title, font=FONT_LABEL, fg=th["primary"],
                bg=C_BODY_BG, anchor="w").pack(fill="x", anchor="w",
                                               pady=(4, 10))

    def _divider(self, parent):
        tk.Frame(parent, height=1, bg=C_DIVIDER).pack(fill="x",
                                                       pady=(10, 18))

    def _labeled_entry(self, parent, label, var, browse=None):
        row = tk.Frame(parent, bg=C_BODY_BG)
        row.pack(fill="x", pady=(0, 10))
        tk.Label(row, text=label, font=FONT_NORMAL, bg=C_BODY_BG, fg=C_TEXT,
                 width=14, anchor="w").pack(side="left")
        if browse is not None:
            th = self._theme()
            RoundedButton(row, text="Browse…", command=browse,
                         bg=th["light_bg"], hover_bg=th["light_hover"],
                         fg=th["primary"], width=110, height=_BTN_H,
                         radius=_BTN_R, font=FONT_BTN).pack(side="right",
                                                            padx=(10, 0))
        entry = RoundedEntry(row, textvariable=var, font=FONT_NORMAL)
        entry.pack(side="left", fill="x", expand=True)
        if var is self.project_var:
            def _mark_edited(_e=None):
                self._project_name_edited = True
            entry.entry.bind("<Key>", _mark_edited, add="+")

    def _browse_folder(self, var):
        # Starts wherever *var* already points, or Data folder as a
        # fallback for Output folder's own first Browse (the OS's own
        # "last used directory" memory otherwise leaves Output folder's
        # dialog opening inside whatever Data folder's own Browse last
        # visited, and vice versa). Falls back to this workspace's own
        # data/ folder, if any, as a last resort so the dialog does not
        # open at some arbitrary location the OS remembered from last time.
        start = var.get().strip()
        if not (start and os.path.isdir(start)):
            start = self.data_var.get().strip()
        if not (start and os.path.isdir(start)):
            candidate = os.path.join(_WORKSPACE_ROOT, "data")
            start = candidate if os.path.isdir(candidate) else ""
        kw = {"title": "Choose a folder"}
        if start and os.path.isdir(start):
            kw["initialdir"] = start
        folder = filedialog.askdirectory(**kw)
        if folder:
            var.set(folder)

    def _browse_data_folder(self):
        self._browse_folder(self.data_var)

    def _browse_output_folder(self):
        self._browse_folder(self.output_var)

    def _browse_metadata(self):
        kw = {"title": "Choose the metadata file",
             "filetypes": [("Tables (CSV / Excel / TSV)",
                            "*.csv *.xlsx *.xls *.txt"),
                           ("All files", "*.*")]}
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
        basename} results", the same wording and timing every sibling
        app's own Home page uses. Never overwrites a value the user has
        actually typed (self._project_name_edited, set by
        _labeled_entry's own binding) or a previous suggestion still
        sitting there unmodified."""
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
        """Data folder is read directly, with no domain named subfolder
        expected in between. Whatever is picked is assumed to already
        hold the `.summary` session subfolders unchanged."""
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
        """Recomputes the detected `.summary` count and attempts again to
        detect metadata automatically for whatever Data folder currently
        holds. Called on Home build and on every Data folder change."""
        input_dir = self._input_dir()
        self._file_count = count_files(input_dir) if input_dir else 0
        if not self.metadata_path_var.get().strip() and input_dir:
            found = find_metadata_path(input_dir)
            if found:
                self.metadata_path_var.set(found)

    def _on_data_folder_change(self):
        """A new Data folder invalidates any metadata path found under
        the previous one, so that is cleared first. _refresh_data_state
        then detects fresh metadata again against the new folder, or leaves the
        field empty for a manual Browse if nothing is found there
        either."""
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
        if not data_folder:
            text = "Pick this project's own data folder."
        elif input_dir is None:
            text = f'"{data_folder}" is not a folder.'
        elif self._file_count == 0:
            text = f"No .summary files found under {input_dir}."
        else:
            text = (f"{self._file_count} .summary "
                    f"file{'s' if self._file_count != 1 else ''} found "
                    f"under {input_dir}.")
        ready = bool(input_dir and self._folders_ready()
                    and self._file_count > 0)
        try:
            lbl.configure(text=text)
            btn.configure(state="normal" if ready else "disabled")
        except tk.TclError:
            pass

    def _cancel_run(self):
        """Leaves the running page. OptoDrum Connector's own
        `on_progress` callback checks `_cancel_flag` and raises
        `InterruptedError` at the next file, so a Cancel here actually
        stops the parse loop soon instead of letting it run to
        completion unattended."""
        if self._running:
            self._cancel_flag.set()
        self._show_home()

    # ── Run execution ─────────────────────────────────────────────────
    def _start_run(self):
        if self._running:
            return
        self._running = True
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
                self._post(pct, f"{current}/{total}: {filename}")

            self._post(0, "Starting...")
            result_path = process_optodrum(inp, out, metadata_path=meta,
                                           on_progress=on_progress)
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

    def _run_finished(self):
        self._running = False
        for action in (lambda: self.progress.set(100),
                      lambda: self._pct_lbl.config(text="100 %"),
                      lambda: self.status_lbl.config(text="Done."),
                      lambda: self.cancel_btn.configure(text="Back",
                                                        state="normal"),
                      self._show_run_links):
            try:
                action()
            except (AttributeError, tk.TclError):
                pass

    def _run_cancelled(self):
        self._running = False
        for action in (lambda: self.status_lbl.config(text="Cancelled."),
                      lambda: self.cancel_btn.configure(text="Back",
                                                        state="normal")):
            try:
                action()
            except (AttributeError, tk.TclError):
                pass

    def _run_failed(self, message):
        self._running = False
        for action in (lambda: self.progress.set(0),
                      lambda: self._pct_lbl.config(text=""),
                      lambda: self.cancel_btn.configure(text="Back",
                                                        state="normal"),
                      lambda: self.status_lbl.config(text=message)):
            try:
                action()
            except (AttributeError, tk.TclError):
                pass
        messagebox.showerror(f"{APP_NAME}: the run stopped", message)

    def _open_output_folder(self):
        path = self._output_dir()
        if path and os.path.isdir(path):
            webbrowser.open(f"file://{os.path.abspath(path)}")

    # ── Running page ──────────────────────────────────────────────────
    def _show_running(self):
        self._clear_body()
        self.nav_wrap.pack(fill="x", side="bottom")
        th = self._theme()

        self.back_btn.pack_forget()
        self.start_btn.pack_forget()
        self.cancel_btn.configure(text="Cancel")
        self.cancel_btn.pack(side="left", padx=12)
        self.cancel_btn.configure(state="normal")

        tk.Frame(self.body, bg=C_BODY_BG).pack(fill="both", expand=True)
        self._pct_lbl = tk.Label(self.body, text="0 %",
                                 font=("Helvetica", 16, "bold"),
                                 fg=th["primary"], bg=C_BODY_BG,
                                 anchor="center")
        self._pct_lbl.pack(pady=(0, 10), fill="x")
        bar_row = tk.Frame(self.body, bg=C_BODY_BG)
        bar_row.pack(fill="x")
        self.progress = GradientProgressBar(bar_row, bg=C_BODY_BG)
        self.progress.set_theme(th["primary_dark"], th["primary"])
        self.progress.pack(anchor="center")

        self._open_folder_btn = RoundedButton(
            self.body, text="Open folder", command=self._open_output_folder,
            bg=th["primary"], hover_bg=th["primary_dark"], fg="white",
            width=140, height=32, radius=16, font=FONT_BTN)

        self.status_lbl = tk.Label(self.body, text="Starting...",
                                   font=FONT_SMALL, fg=C_MUTED,
                                   bg=C_BODY_BG, wraplength=520,
                                   justify="center", anchor="center")
        self.status_lbl.pack(pady=(14, 0), fill="x")
        tk.Frame(self.body, bg=C_BODY_BG).pack(fill="both", expand=True)

    def _show_run_links(self):
        try:
            self._open_folder_btn.pack_forget()
        except tk.TclError:
            return
        if os.path.isdir(self._output_dir() or ""):
            self._open_folder_btn.pack(before=self.status_lbl, pady=(14, 0))

    def run(self):
        self.root.mainloop()


def launch_gui():
    OptoDrumApp().run()


if __name__ == "__main__":
    launch_gui()
