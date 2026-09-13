"""
Regression tests against the bundled sample project (samples/).

These guard the already generated samples/output/Demo Project/optodrum_report.csv
against silent drift: if the engine's own behaviour ever changes, this
fails loudly instead of leaving a stale, wrong "reference" output sitting
in the repo. Run `python3 samples/_fabricate_samples.py` again and commit
the result whenever a real engine change makes these fail on purpose.
"""
import os
import sys

import pandas as pd
import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "steps", "optodrum"))

import optodrum  # noqa: E402

_DATA_DIR = os.path.join(_ROOT, "samples", "data", "Demo Project")
_BAKED_REPORT = os.path.join(_ROOT, "samples", "output", "Demo Project",
                             "optodrum_report.csv")

pytestmark = pytest.mark.skipif(
    not os.path.isdir(_DATA_DIR),
    reason="samples/data/Demo Project not present, run "
          "samples/_fabricate_samples.py first")


def test_pre_baked_report_exists():
    assert os.path.isfile(_BAKED_REPORT)


def test_engine_reproduces_the_pre_baked_report(tmp_path):
    meta_path = os.path.join(_DATA_DIR, "_metadata.csv")
    fresh_path = optodrum.process_optodrum(
        _DATA_DIR, str(tmp_path), metadata_path=meta_path)

    fresh = pd.read_csv(fresh_path).sort_values("Mouse_ID").reset_index(
        drop=True)
    baked = pd.read_csv(_BAKED_REPORT).sort_values("Mouse_ID").reset_index(
        drop=True)
    pd.testing.assert_frame_equal(fresh, baked)


def test_report_shape_and_values():
    df = pd.read_csv(_BAKED_REPORT).set_index("Mouse_ID")
    assert set(df.index) == {"M001", "M002"}
    assert list(df.columns) == ["Genotype", "Group", "visual_acuity_cycles",
                                "contrast_0.011_cycles"]
    assert df.loc["M001", "visual_acuity_cycles"] == 0.52
    assert df.loc["M001", "contrast_0.011_cycles"] == 32.5
    # M002's own CONTRAST session is the real "below detection threshold"
    # value (-1 in the raw .summary), stored as 99.99.
    assert df.loc["M002", "contrast_0.011_cycles"] == 99.99
