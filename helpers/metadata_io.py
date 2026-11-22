"""
Metadata I/O for several file formats.

Metadata is most simply read as `_metadata.csv` via `pd.read_csv(...)`.
Real users work with Excel or tab separated text just as often, so this
module hides the extension detail behind a single pair of helpers:

    find_metadata_path(project_dir)
        Return the first metadata file found under *project_dir*, or
        None. Extension precedence favours the more structured
        formats when several exist side by side:
            _metadata.xlsx  →  _metadata.xls  →  _metadata.csv  →
            _metadata.txt   →  metadata.csv   →  metadata.txt

    read_metadata_any(path) -> pandas.DataFrame
        Dispatch by extension. `.xlsx`/`.xls` use pandas' Excel
        reader (first sheet). `.csv` uses the standard CSV reader.
        `.txt` detects the separator automatically by peeking at the
        first data line: TAB when the line has more tabs than commas,
        else comma. This handles both TSV exports and plain
        comma delimited files with a `.txt` extension.

    write_metadata_any(df, path) -> str
        Dispatch by extension. Returns the path that was written.
        `.xlsx` uses openpyxl; `.csv` / `.txt` write UTF-8 with the
        matching delimiter (comma for csv, tab for txt).

    detect_delimiter(path, default=",") -> str
        Used internally by read_metadata_any for `.txt` files, but
        exposed for other callers (e.g. a preview dialog).

Design rules:
* No pandas import at module top level; only imported inside the
  helpers so unrelated tools that import this module for its path
  helpers don't pay the pandas import tax.
* Every function accepts str or pathlib.Path; internally converted
  to str with os.fspath for compatibility with pandas.
* Excel support depends on `openpyxl` for xlsx and `xlrd` for xls.
  Both are listed in docs/requirements.txt; if missing we surface a
  clear ImportError that names the package the user needs.
"""

from __future__ import annotations

import os
from typing import Optional


# Precedence order used by find_metadata_path. Structured formats
# come first so a project carrying both `_metadata.xlsx` and a stale
# `_metadata.csv` returns the Excel file.
_METADATA_CANDIDATES = (
    "_metadata.xlsx",
    "_metadata.xls",
    "_metadata.csv",
    "_metadata.txt",
    "metadata.csv",
    "metadata.txt",
)


def find_metadata_path(project_dir) -> Optional[str]:
    """Return the first metadata file present under *project_dir*, or
    None if no candidate exists.

    Search order (highest precedence first):
        _metadata.xlsx, _metadata.xls, _metadata.csv, _metadata.txt,
        metadata.csv, metadata.txt

    Nothing is opened here. If the resolved candidate turns out to be
    unreadable at parse time (corrupt xlsx, locked file, wrong
    delimiter, ...), the caller is expected to catch the exception and
    ask the user for a different file, rather than silently skipping to
    another candidate.
    """
    project_dir = os.fspath(project_dir)
    if not os.path.isdir(project_dir):
        return None
    for name in _METADATA_CANDIDATES:
        p = os.path.join(project_dir, name)
        if os.path.isfile(p):
            return p
    return None


def detect_delimiter(path, default: str = ",") -> str:
    """Peek at the first line that is not blank in *path* and choose ``\\t`` if
    it contains more tabs than commas, else ``default``. Reads the
    file with a short byte budget so it stays cheap for large
    metadata files."""
    path = os.fspath(path)
    try:
        with open(path, "rb") as f:
            head = f.read(4096)
    except OSError:
        return default
    # Find the first text line that is not empty.
    for raw in head.splitlines():
        if not raw.strip():
            continue
        # Decode with a permissive fallback so exotic encodings do
        # not derail delimiter detection.
        try:
            line = raw.decode("utf-8")
        except UnicodeDecodeError:
            line = raw.decode("latin1", errors="replace")
        n_tab   = line.count("\t")
        n_comma = line.count(",")
        return "\t" if n_tab > n_comma else default
    return default


def list_sheets(path) -> list:
    """Return the list of sheet names for an Excel workbook, or a
    list with one element, ``[None]``, for CSV / TXT / anything else.

    ``[None]`` is the "single implicit sheet" sentinel: callers can
    branch on ``len(list_sheets(p)) == 1`` to decide whether to show
    a sheet picker (`>= 2` sheets) or skip it silently.

    Empty workbooks (zero sheets) also return `[None]` so downstream
    read code can raise a normal read error instead of trying to
    pick from an empty list.
    """
    path = os.fspath(path)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xlsm"):
        try:
            from openpyxl import load_workbook
            wb = load_workbook(path, read_only=True, data_only=True)
            names = list(wb.sheetnames)
            wb.close()
            return names if names else [None]
        except Exception:
            return [None]
    if ext == ".xls":
        try:
            import xlrd
            wb = xlrd.open_workbook(path, on_demand=True)
            names = list(wb.sheet_names())
            wb.release_resources()
            return names if names else [None]
        except Exception:
            return [None]
    return [None]


def read_metadata_any(path, sheet=None):
    """Read *path* as a pandas DataFrame, dispatching by extension.

    * `.xlsx` / `.xls` → the sheet named / indexed by *sheet* (or
                          the first sheet when *sheet* is None).
    * `.csv`           → `pd.read_csv` (comma delimiter, UTF-8).
    * `.txt`           → `pd.read_csv` with the delimiter picked by
                          `detect_delimiter` (favouring tab).
    * Any other extension → tried as CSV first, then as TSV if the
                          first attempt raises a ParserError.

    Parameters
    ----------
    path : str or Path
        The file to read.
    sheet : str, int or None, optional
        Which Excel sheet to consume. Accepts a sheet name (string)
        or a positional index (int). Ignored for formats other than Excel.
        Default: 0 (first sheet).

    Raises:
        FileNotFoundError  when *path* does not exist.
        ImportError        with a clear hint when Excel support
                           needs `openpyxl` (xlsx) or `xlrd` (xls)
                           and neither is installed.
    """
    import pandas as pd

    path = os.fspath(path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"metadata file not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    sheet_arg = 0 if sheet is None else sheet

    if ext in (".xlsx", ".xlsm"):
        try:
            return pd.read_excel(path, sheet_name=sheet_arg,
                                    engine="openpyxl")
        except ImportError as e:
            raise ImportError(
                "Reading .xlsx metadata requires openpyxl. Install it "
                "with `pip install openpyxl` and try again."
            ) from e
    if ext == ".xls":
        try:
            return pd.read_excel(path, sheet_name=sheet_arg,
                                    engine="xlrd")
        except ImportError as e:
            raise ImportError(
                "Reading legacy .xls metadata requires xlrd. Install it "
                "with `pip install xlrd` and try again."
            ) from e
    if ext == ".csv":
        return pd.read_csv(path)
    if ext == ".txt":
        sep = detect_delimiter(path, default=",")
        return pd.read_csv(path, sep=sep)

    # Unknown extension: try comma, then tab, so files without a
    # recognized extension still have a chance to parse.
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.read_csv(path, sep="\t")


def write_metadata_any(df, path) -> str:
    """Write *df* to *path*, dispatching by extension. Returns the
    path that was written.

    * `.xlsx`   → single sheet named 'metadata' via openpyxl
    * `.csv`    → UTF-8 comma separated, no index
    * `.txt`    → UTF-8 tab separated, no index (TSV convention)
    * Others    → treated as CSV
    """
    path = os.fspath(path)
    ext = os.path.splitext(path)[1].lower()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    if ext in (".xlsx", ".xlsm"):
        try:
            df.to_excel(path, index=False, sheet_name="metadata",
                         engine="openpyxl")
        except ImportError as e:
            raise ImportError(
                "Writing .xlsx metadata requires openpyxl. Install it "
                "with `pip install openpyxl` and try again."
            ) from e
        return path
    if ext == ".txt":
        df.to_csv(path, sep="\t", index=False, encoding="utf-8")
        return path
    # Default to CSV for .csv and any unknown extension.
    df.to_csv(path, index=False, encoding="utf-8")
    return path


# ── Path helpers for the standard project layout ──────────────────────────────

def resolve_project_metadata(project_root) -> Optional[str]:
    """Convenience wrapper for callers that already know the project
    root (the folder that contains `Export files/`, `_metadata.*`
    and `.channels.json`). Returns the metadata file inside that
    root using the same precedence as `find_metadata_path`.
    """
    return find_metadata_path(project_root)
