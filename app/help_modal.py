"""
Help dialog and its content.

The same dialog as the VisoLab applications (widgets.show_help_dialog):
centred, modal, a scrollable body of collapsible sections, the first one
open. OptoDrum Connector has two pages to document: the start screen and
Home, which carries everything.
"""
from __future__ import annotations

from i18n import tr
from theme import _MODE_THEMES
from widgets import set_accent, show_help_dialog

_WIZARD_LABELS = {
    "welcome": "OptoDrum Connector", "home": "Convert OptoDrum exports",
}

# (section title, body) per page. Written as what the control does and
# why it matters, not as a restatement of its label.
_HELP_CONTENT = {
    "welcome": [
        ("What OptoDrum Connector is",
         "A small, standalone tool that turns OptoDrum's .summary "
         "staircase exports into one table, optodrum_report.csv: one row "
         "per animal and experiment, with the visual acuity threshold and "
         "the contrast sensitivity threshold at every spatial frequency "
         "tested."),
        ("What it is not",
         "It performs no statistical analysis and draws no plots; it "
         "extracts and tabulates. optodrum_report.csv is an ordinary "
         "measurement table for any statistical or plotting software."),
        ("Getting started",
         "Get started leads to the data folder holding the OptoDrum "
         "sessions, the output folder and the project name."),
    ],
    "home": [
        ("Data folder",
         "The folder holding the session subfolders, read as it is. Each "
         "session is a subfolder named "
         "<year>_mouse_<Mouse_ID>_<Experiment>_<Test_Type>. Files inside "
         "a folder whose name does not follow this pattern are skipped, "
         "and the run reports how many."),
        ("Metadata",
         "An optional table (.csv, .xlsx or .txt) naming each animal's "
         "group. It is found automatically when it sits in the data "
         "folder; use Browse when it is somewhere else. Its first column "
         "is the Mouse ID, and every other column (Genotype, Gender, "
         "Group...) is added to the report for that animal. Changing the "
         "data folder clears the metadata found in the previous one."),
        ("Output folder and project name",
         "Together they decide where the report is written: "
         "{Output folder}/{Project name}/optodrum_report.csv. The project "
         "name is suggested from the data folder's name and can be "
         "changed freely."),
        ("Files found",
         "Every .summary file under the data folder, including folders "
         "inside it. A session whose test type is visualacuity is read as "
         "an ACUITY staircase; any other test type as a CONTRAST "
         "staircase. The count updates whenever the data folder changes, "
         "and Run stays unavailable while it is zero."),
        ("Run",
         "Every file found is read and combined into one row per animal "
         "and experiment. A contrast value of -1 is stored as 99.99 "
         "(below the detectable threshold); any other negative value is "
         "left empty. When the run finishes, the page shows how many rows "
         "were written and any files it had to skip, and Open folder "
         "shows optodrum_report.csv."),
    ],
}


def show_help(root, page_id: str, mode: str = None):
    label = _WIZARD_LABELS.get(page_id, page_id or "OptoDrum Connector")
    entries = _HELP_CONTENT.get(page_id) or [
        ("Not documented yet",
         "This page is still under construction, so there is nothing to "
         "explain about it yet.")]
    set_accent(_MODE_THEMES.get(mode or "home", _MODE_THEMES["home"]))
    return show_help_dialog(
        root, tr(label),
        tr("What each control on this page does and how to use it."),
        [(tr(t), tr(b)) for t, b in entries],
        window_title=f"OptoDrum Connector  ·  {tr('Help')}",
        close_text=tr("Close"))
