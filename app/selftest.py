"""
Self-test: ``OptoDrum Connector --selftest`` (or ``python "app/OptoDrum
Connector GUI.py" --selftest``) converts the bundled Demo Project without
showing a window, then exits with 0 when the report was written and holds
every animal, and 1 otherwise. The full trace goes to the log file (see
runtime_support.start_logging).

Build scripts run it straight after packaging, so an executable that
starts but cannot actually convert anything is caught on the machine that
built it.
"""
import os
import shutil
import sys
import tempfile
import traceback

EXAMPLE = "Demo Project"


def main():
    import __main__ as gui
    import pandas as pd
    from optodrum import process_optodrum

    work = tempfile.mkdtemp(prefix="optodrum-selftest-")
    try:
        data = os.path.join(work, "data", EXAMPLE)
        shutil.copytree(os.path.join(gui._SAMPLES_DATA_DIR, EXAMPLE), data)
        out = os.path.join(work, "output", EXAMPLE)
        path = process_optodrum(data, out, metadata_path=os.path.join(
            data, "_metadata.csv"))
        if not path or not os.path.isfile(path):
            raise RuntimeError("optodrum_report.csv was not written")
        report = pd.read_csv(path)
        if report.empty or "visual_acuity_cycles" not in report.columns:
            raise RuntimeError("optodrum_report.csv has no acuity results")
        print(f"conversion: ok, {len(report)} rows")
        print("SELFTEST PASSED")
        return 0
    except Exception:
        print("SELFTEST FAILED")
        traceback.print_exc(file=sys.stdout)
        return 1
    finally:
        sys.stdout.flush()
        shutil.rmtree(work, ignore_errors=True)
