"""
OptoDrum Connector: processing engine.

Parses OptoDrum `.summary` exports (visual acuity / contrast sensitivity
staircase results) into one wide format `optodrum_report.csv`, one row
per (Mouse_ID, Experiment). One step, no further stages, so there is no
`steps/optodrum/config_template.json`: DEFAULT_CONFIG below is the only
configuration surface, keeping its defaults internal rather than
editable from the GUI.

Path resolution (Data folder, Output folder, Project) lives entirely in
the GUI; this module only takes a folder to read from, a folder to
write to, and an optional metadata path. `_load_metadata` dispatches by
extension (`.csv`, `.xlsx`/`.xls`, `.txt`) rather than assuming `.csv`,
so any of those formats the GUI can load is also one this engine can
read back.
"""
import os
import re
import xml.etree.ElementTree as ET

import pandas as pd

DEFAULT_CONFIG = {
    "encoding": "latin-1",
    "output_filename": "optodrum_report.csv",
}


def count_files(folder: str) -> int:
    """Counts .summary files recursively under folder."""
    n = 0
    for _, _, files in os.walk(folder):
        n += sum(1 for f in files if f.endswith(".summary"))
    return n


# ── Column helpers ────────────────────────────────────────────────────────────

def _extract_cycle_num(colname: str):
    m = re.search(r"([\d.]+)", colname)
    return float(m.group(1)) if m else float("inf")


def _reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    fixed    = ["Mouse_ID"] if "Mouse_ID" in df.columns else []
    va       = [c for c in df.columns if c == "visual_acuity_cycles"]
    contrast = sorted(
        [c for c in df.columns if c.startswith("contrast_") and c.endswith("_cycles")],
        key=_extract_cycle_num,
    )
    return df[fixed + va + contrast]


def _read_metadata_table(metadata_path: str) -> pd.DataFrame:
    """Dispatch by extension: `.xlsx`/`.xls` via pandas' Excel reader,
    `.txt` with tabs as the separator, everything else (`.csv` and
    no or unknown extension) with commas. Mirrors
    `_helper_skill/metadata_io.py`'s own dispatch closely enough for
    this engine's single use, without depending on it; this module has
    no GUI dependency of its own."""
    ext = os.path.splitext(metadata_path)[1].lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(metadata_path)
    if ext == ".txt":
        return pd.read_csv(metadata_path, sep="\t")
    return pd.read_csv(metadata_path)


def _load_metadata(metadata_path: str) -> dict:
    """
    Load a metadata table keyed by its first column (Mouse ID / Mouse_ID /
    whatever it is named). Returns {mouse_id: {col: val}} for all
    remaining columns. Empty dict if the file is not found or unreadable.
    """
    if not metadata_path or not os.path.isfile(metadata_path):
        return {}
    try:
        meta = _read_metadata_table(metadata_path)
        meta.columns = [c.strip() for c in meta.columns]
        id_col = meta.columns[0]
        rest   = [c for c in meta.columns if c != id_col]
        ids    = meta[id_col].astype(str).str.strip().tolist()
        records = meta[rest].to_dict(orient="records")
        return dict(zip(ids, records))
    except Exception:
        return {}


# ── Core processing ───────────────────────────────────────────────────────────

def process_optodrum(
    input_folder: str,
    output_folder: str,
    metadata_path: str = None,
    on_progress=None,
    config: dict = None,
):
    """
    Processes all .summary files under input_folder and writes a CSV report.

    Parameters:
        input_folder  : Root folder containing one subdirectory per session.
        output_folder : Destination folder for the output CSV.
        on_progress   : Optional callback(current: int, total: int, filename: str).
        config        : Config dict (keys: encoding, output_filename).

    Returns:
        The output CSV path, or None if no data was extracted.
    """
    cfg             = {**DEFAULT_CONFIG, **(config or {})}
    encoding        = cfg["encoding"]
    output_filename = cfg["output_filename"]

    os.makedirs(output_folder, exist_ok=True)

    # Collect all .summary files
    summary_files = []
    for dirpath, _, filenames in os.walk(input_folder):
        for fname in sorted(filenames):
            if fname.endswith(".summary"):
                summary_files.append((dirpath, fname))

    total   = len(summary_files)
    results = {}   # (Mouse_ID, Experiment) -> {col: value}

    for i, (dirpath, fname) in enumerate(summary_files):
        folder_name = os.path.basename(dirpath)
        parts       = folder_name.split("_")

        if len(parts) < 5:
            print(f"Warning: unexpected folder name format '{folder_name}', skipping.")
            if on_progress:
                on_progress(i + 1, total, fname)
            continue

        mouse_id     = parts[2]
        experiment   = parts[3]
        session_type = parts[4] if len(parts) > 4 else ""

        key = (mouse_id, experiment)
        if key not in results:
            results[key] = {"Mouse_ID": mouse_id}

        filepath = os.path.join(dirpath, fname)
        try:
            with open(filepath, "r", encoding=encoding) as f:
                for line in f:
                    if "ContrastSensitivityFunction" not in line:
                        continue
                    try:
                        elem = ET.fromstring(line.strip())
                    except ET.ParseError:
                        print(f"Warning: XML parse error in {fname}, line skipped.")
                        continue

                    staircase = elem.get("typeOfStaircase", "")

                    # Acuity sessions: only extract ACUITY staircase result
                    # Contrast sessions: only extract CONTRAST staircase result
                    if session_type == "visualacuity":
                        if staircase == "ACUITY":
                            cycle = elem.get("cycle")
                            if cycle is not None and float(cycle) > 0:
                                results[key]["visual_acuity_cycles"] = float(cycle)
                    else:
                        if staircase == "CONTRAST":
                            cycle    = elem.get("cycle")
                            contrast = elem.get("contrast")
                            if cycle is not None and contrast is not None:
                                c = float(contrast)
                                if c == -1:
                                    c = 99.99
                                elif c < 0:
                                    c = None
                                col = f"contrast_{cycle}_cycles"
                                results[key][col] = c

        except Exception as e:
            print(f"Warning: could not read {fname}: {e}")

        if on_progress:
            on_progress(i + 1, total, fname)

    if not results:
        print("No data extracted. Check that input folder contains valid .summary files.")
        return None

    df = pd.DataFrame(list(results.values()))

    # Merge metadata (Genotype, Gender, Group, …) if available
    meta = _load_metadata(metadata_path)
    if meta:
        meta_df = pd.DataFrame([{"Mouse_ID": k, **v} for k, v in meta.items()])
        df = df.merge(meta_df, on="Mouse_ID", how="left")
        meta_cols = [c for c in meta_df.columns if c != "Mouse_ID"]
        va       = [c for c in df.columns if c == "visual_acuity_cycles"]
        contrast = sorted(
            [c for c in df.columns if c.startswith("contrast_") and c.endswith("_cycles")],
            key=_extract_cycle_num,
        )
        df = df[["Mouse_ID"] + meta_cols + va + contrast]
    else:
        df = _reorder_columns(df)

    output_path = os.path.join(output_folder, output_filename)
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}")
    return output_path
