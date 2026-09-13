"""
Regenerates samples/data/Demo Project/ and samples/output/Demo Project/.

Idempotent: safe to run again any time the engine or the sample's own
shape changes, always producing the exact same files from scratch.

Two animals, two sessions each (one ACUITY, one CONTRAST), light enough
to ship in the repo and read in one sitting, but real enough to exercise
the whole pipeline: folder name parsing, both staircase types, the
metadata merge, and the `contrast == -1 → 99.99` below threshold rule
(M002's own CONTRAST session deliberately hits it).

Run directly to regenerate:  python3 samples/_fabricate_samples.py
"""
import os
import shutil
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "steps", "optodrum"))

import optodrum  # noqa: E402

_DATA_DIR = os.path.join(_HERE, "data", "Demo Project")
_OUTPUT_DIR = os.path.join(_HERE, "output", "Demo Project")

# (Mouse_ID, Genotype, Group, acuity_cycle, contrast_frequency, contrast_value)
# M002's contrast_value of -1 is the real OptoDrum "below detection
# threshold" reading. process_optodrum stores it as 99.99.
_ANIMALS = [
    ("M001", "WT", "Control", 0.52, "0.011", 32.5),
    ("M002", "WT", "Control", 0.47, "0.011", -1),
]


def _acuity_line(cycle):
    return (f'<ContrastSensitivityFunction typeOfStaircase="ACUITY" '
            f'cycle="{cycle}"/>')


def _contrast_line(cycle, contrast):
    return (f'<ContrastSensitivityFunction typeOfStaircase="CONTRAST" '
            f'cycle="{cycle}" contrast="{contrast}"/>')


def _write_summary(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="latin-1") as fh:
        for line in lines:
            fh.write(line + "\n")


def build():
    if os.path.isdir(_DATA_DIR):
        shutil.rmtree(_DATA_DIR)
    if os.path.isdir(_OUTPUT_DIR):
        shutil.rmtree(_OUTPUT_DIR)

    for mouse_id, _genotype, _group, acuity, freq, contrast in _ANIMALS:
        acuity_dir = os.path.join(
            _DATA_DIR,
            f"2025_mouse_{mouse_id}_optomotor_visualacuity")
        _write_summary(os.path.join(acuity_dir, "trial1.summary"),
                       [_acuity_line(acuity)])

        contrast_dir = os.path.join(
            _DATA_DIR, f"2025_mouse_{mouse_id}_optomotor_{freq}")
        _write_summary(os.path.join(contrast_dir, "trial1.summary"),
                       [_contrast_line(freq, contrast)])

    meta_path = os.path.join(_DATA_DIR, "_metadata.csv")
    with open(meta_path, "w", encoding="utf-8") as fh:
        fh.write("Mouse_ID,Genotype,Group\n")
        for mouse_id, genotype, group, *_rest in _ANIMALS:
            fh.write(f"{mouse_id},{genotype},{group}\n")

    report_path = optodrum.process_optodrum(
        _DATA_DIR, _OUTPUT_DIR, metadata_path=meta_path)
    print(f"Sample project rebuilt: {_DATA_DIR}")
    print(f"Generated report:       {report_path}")


if __name__ == "__main__":
    build()
