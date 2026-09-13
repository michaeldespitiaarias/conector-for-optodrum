"""
Help dialog and its content.

A centred, square, modal Toplevel with a scrollable body of
collapsible sections, themed to the (single) working colour. The
first section starts expanded so the dialog says something useful
immediately.

OptoDrum Connector has only two pages worth documenting: welcome and
home (there is no wizard; Home carries everything). `mode` is accepted
for interface parity with the vendored `show_help` call sites but always
resolves to the single "home" theme.
"""
from __future__ import annotations

import tkinter as tk

from theme import (
    C_BODY_BG, C_DIVIDER, C_MUTED, C_TEXT,
    FONT_BTN, FONT_SECTION, FONT_SMALL, _MODE_THEMES,
)
from widgets import RoundedButton

_WIZARD_LABELS = {
    "welcome": "OptoDrum Connector", "home": "Home",
}

# (section title, body) per page. Written as what the control does and
# why it matters, not as a restatement of its label.
_HELP_CONTENT = {
    "welcome": [
        ("What OptoDrum Connector is",
         "A small, standalone tool that turns OptoDrum's own "
         "`.summary` staircase exports into one structured "
         "`optodrum_report.csv`: a wide table, one row per animal, with "
         "the visual acuity threshold and the contrast sensitivity "
         "threshold at every spatial frequency tested."),
        ("What it is not",
         "It does not run any statistics or draw any plots. It only "
         "extracts and tabulates. Its own `optodrum_report.csv` is a "
         "regular measurement table, so if you need statistics or "
         "figures on top of it, load it into whatever statistics or "
         "plotting tool you already use."),
        ("Getting started",
         "Press Start, then pick the Data folder holding your OptoDrum "
         "`.summary` sessions, an Output folder, and a Project name."),
    ],
    "home": [
        ("Data folder",
         "Read directly. Point it at the folder that holds your "
         "session subfolders (or a parent folder that contains exactly "
         "one such folder, if that is easier). Each session lives in "
         "its own subfolder named "
         "`<year>_mouse_<Mouse_ID>_<Experiment>_<Test_Type>`; folders "
         "that do not follow this convention are skipped and reported "
         "at the end of the run."),
        ("Metadata",
         "`_metadata.csv` (or `.xlsx`/`.txt`) is detected automatically "
         "under Data folder if present there; Browse otherwise (e.g. "
         "when it sits one level up instead). Every column beyond the "
         "first (Mouse ID) is merged into the final report by Mouse ID, "
         "so Genotype, Gender or Group travel straight through to "
         "`optodrum_report.csv`. Optional; the report is still produced "
         "without it. Changing Data folder clears any metadata found "
         "under the previous one and detects fresh metadata again."),
        ("Output folder / Project",
         "Together decide where the report is written: "
         "`{Output folder}/{Project}/optodrum_report.csv`. Project is "
         "suggested from Data folder's own name and stays freely "
         "editable."),
        ("Detected files",
         "Every `.summary` file found anywhere under Data folder, "
         "counted recursively: an ACUITY staircase when the session's "
         "own folder name ends in `visualacuity`, a CONTRAST staircase "
         "otherwise. Scans again automatically whenever Data folder "
         "changes; Run stays disabled at zero."),
        ("Run",
         "Every detected `.summary` file is parsed and combined into one "
         "row per (Mouse_ID, Experiment). A contrast value of −1 is "
         "stored as 99.99 (below the detectable threshold); any other "
         "negative value is stored as missing. Once the run finishes, "
         "use Open folder to reveal `optodrum_report.csv`."),
    ],
}


def show_help(root, page_id: str, mode: str = None):
    theme = _MODE_THEMES.get(mode or "home", _MODE_THEMES["home"])
    primary = theme["primary"]
    label = _WIZARD_LABELS.get(page_id, page_id or "Project")
    entries = _HELP_CONTENT.get(page_id, [])
    if not entries:
        entries = [("Not documented yet",
                    "This step is still under construction, so there is "
                    "nothing to explain about it yet.")]

    win = tk.Toplevel(root)
    win.title("OptoDrum Connector  ·  Help")
    win.configure(bg=C_BODY_BG)

    root_w = max(600, root.winfo_width())
    root_h = max(480, root.winfo_height())
    side = min(600, int(min(root_w, root_h) * 0.75))
    try:
        x = root.winfo_x() + (root_w - side) // 2
        y = root.winfo_y() + (root_h - side) // 2
        win.geometry(f"{side}x{side}+{x}+{y}")
    except tk.TclError:
        # Reachable before the root window is fully realized; a geometry
        # failure must not escape a button's command.
        win.geometry(f"{side}x{side}")
    win.transient(root)
    win.grab_set()

    header = tk.Frame(win, bg=C_BODY_BG)
    header.pack(fill="x", padx=24, pady=(20, 4))
    tk.Label(header, text=label.upper(), font=FONT_SECTION, fg=primary,
             bg=C_BODY_BG, anchor="w").pack(anchor="w")
    tk.Label(header,
             text="What each control on this page does and how to use it.",
             font=FONT_SMALL, fg=C_MUTED, bg=C_BODY_BG,
             anchor="w").pack(anchor="w", pady=(4, 0))
    tk.Frame(win, height=1, bg=C_DIVIDER).pack(fill="x", padx=24,
                                               pady=(10, 4))

    body_wrap = tk.Frame(win, bg=C_BODY_BG)
    body_wrap.pack(fill="both", expand=True)
    canvas = tk.Canvas(body_wrap, bg=C_BODY_BG, bd=0, highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)
    scroll = tk.Scrollbar(body_wrap, orient="vertical", command=canvas.yview,
                          width=16)
    scroll.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scroll.set)
    body = tk.Frame(canvas, bg=C_BODY_BG)
    win_id = canvas.create_window((0, 0), window=body, anchor="nw")

    body_labels = []

    def _on_resize(event):
        canvas.itemconfig(win_id, width=event.width)
        wrap = max(200, event.width - 90)
        for lbl in body_labels:
            lbl.configure(wraplength=wrap)

    canvas.bind("<Configure>", _on_resize)
    body.bind("<Configure>",
              lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))

    for i, (title_bit, body_bit) in enumerate(entries):
        section = tk.Frame(body, bg=C_BODY_BG)
        section.pack(fill="x", padx=28, pady=(12 if i == 0 else 6, 0))
        state = {"open": (i == 0)}

        title_row = tk.Frame(section, bg=C_BODY_BG)
        title_row.pack(fill="x")
        indicator = tk.Label(title_row, text=("▾" if state["open"] else "▸"),
                             font=("Helvetica", 13, "bold"), fg=primary,
                             bg=C_BODY_BG, width=2, anchor="w")
        indicator.pack(side="left")
        title_lbl = tk.Label(title_row, text=title_bit,
                             font=("Helvetica", 15, "bold"), fg=primary,
                             bg=C_BODY_BG, anchor="w", justify="left")
        title_lbl.pack(side="left", fill="x", expand=True)

        body_lbl = tk.Label(section, text=body_bit, font=("Helvetica", 15),
                            fg=C_TEXT, bg=C_BODY_BG, anchor="w",
                            justify="left", wraplength=side - 90)
        body_labels.append(body_lbl)
        if state["open"]:
            body_lbl.pack(anchor="w", pady=(4, 0), fill="x")

        def _toggle(_e=None, st=state, lbl=body_lbl, ind=indicator):
            st["open"] = not st["open"]
            ind.config(text="▾" if st["open"] else "▸")
            if st["open"]:
                lbl.pack(anchor="w", pady=(4, 0), fill="x")
            else:
                lbl.pack_forget()
            canvas.configure(scrollregion=canvas.bbox("all"))

        for w in (title_row, indicator, title_lbl):
            w.bind("<Button-1>", _toggle)

    foot = tk.Frame(win, bg=C_BODY_BG)
    foot.pack(fill="x", pady=(6, 18))
    RoundedButton(foot, text="Close", command=win.destroy,
                  bg=primary, hover_bg=theme["primary_dark"],
                  width=118, height=32, radius=16,
                  font=FONT_BTN).pack()
    win.bind("<Escape>", lambda _e: win.destroy())
