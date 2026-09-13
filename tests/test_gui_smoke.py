"""
Smoke tests: the GUI must actually construct.

These cannot judge whether the interface *looks* right; that needs a
human running it. What they do catch is the class of failure that makes
it not run at all: a missing theme token, a widget option tkinter
rejects, a typo in a page builder. Every page is built, then the root is
destroyed without ever entering the event loop.

Skipped automatically where no display is available, so a headless CI
run reports honestly instead of failing for the wrong reason.
"""
import os
import sys

import pandas as pd
import pytest

_APP = os.path.join(os.path.dirname(__file__), "..", "app")
sys.path.insert(0, _APP)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                               "_helper_skill"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..",
                               "steps", "optodrum"))

tk = pytest.importorskip("tkinter")


def _display_available():
    try:
        r = tk.Tk()
        r.destroy()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _display_available(), reason="no display available for tkinter")


def _load_gui_module():
    """The module has a space in its filename, so it cannot be imported
    by name. Load it directly from its file path instead."""
    import importlib.util
    path = os.path.join(_APP, "OptoDrum Connector GUI.py")
    spec = importlib.util.spec_from_file_location("optodrum_gui", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def gui():
    return _load_gui_module()


@pytest.fixture
def app(gui):
    a = gui.OptoDrumApp()
    yield a
    try:
        a.root.destroy()
    except Exception:
        pass


@pytest.fixture
def project(tmp_path):
    """A Data folder and an Output folder as two independent locations
    (never a shared workspace root), exactly what a real Browse pick
    produces. Data folder is read directly, with no folder named after
    the domain sitting in between it and the session subfolders.
    Returns (data_folder, output_folder, project_name)."""
    data_folder = tmp_path / "data_root" / "Demo"
    session = data_folder / "2025_mouse_M001_optomotor_visualacuity"
    session.mkdir(parents=True)
    (session / "trial1.summary").write_text(
        '<ContrastSensitivityFunction typeOfStaircase="ACUITY" '
        'cycle="0.5"/>\n', encoding="latin-1")
    pd.DataFrame({"Mouse_ID": ["M001"], "Genotype": ["WT"]}).to_csv(
        data_folder / "_metadata.csv", index=False)
    output_folder = tmp_path / "output_root"
    output_folder.mkdir()
    return str(data_folder), str(output_folder), "Demo"


def _enter(app, project):
    """Fill in Home's fields the way a user must: Data folder, Output
    folder, Project (Metadata is detected automatically, not set here)."""
    data_folder, output_folder, name = project
    app.data_var.set(data_folder)
    app.output_var.set(output_folder)
    app.project_var.set(name)


class TestConstruction:
    def test_app_builds_and_shows_splash(self, app):
        assert app.root.title() == "OptoDrum Connector"
        assert app.mode is None

    def test_home_builds(self, app):
        app._show_home()
        app.root.update_idletasks()

    def test_home_builds_with_a_project_already_filled_in(self, app,
                                                           project):
        _enter(app, project)
        app._show_home()
        app.root.update_idletasks()
        assert app._file_count == 1


class TestHome:
    def test_run_disabled_with_no_folders_set(self, app):
        app._show_home()
        assert app.start_btn._state == "disabled"

    def test_run_enabled_once_all_fields_are_set(self, app, project):
        app._show_home()
        _enter(app, project)
        assert app.start_btn._state == "normal"

    def test_run_disabled_when_data_folder_does_not_exist(
            self, app, tmp_path):
        app._show_home()
        app.data_var.set(str(tmp_path / "nope"))
        app.output_var.set(str(tmp_path))
        app.project_var.set("Whatever")
        assert app.start_btn._state == "disabled"

    def test_run_disabled_when_no_summary_files_are_found(
            self, app, tmp_path):
        app._show_home()
        data_folder = tmp_path / "data_root" / "Empty"
        data_folder.mkdir(parents=True)
        app.data_var.set(str(data_folder))
        app.output_var.set(str(tmp_path))
        app.project_var.set("Empty")
        assert app.start_btn._state == "disabled"

    def test_project_name_is_suggested_once_both_folders_are_set(
            self, app, tmp_path):
        data = tmp_path / "My Experiment"
        data.mkdir()
        app._show_home()
        app.data_var.set(str(data))
        assert app.project_var.get() == ""       # withheld: no output yet
        app.output_var.set(str(tmp_path))
        assert app.project_var.get() == "My Experiment results"

    def test_a_typed_project_name_is_never_overwritten(self, app, tmp_path):
        data = tmp_path / "Study A"
        data.mkdir()
        app._show_home()
        app._project_name_edited = True
        app.project_var.set("my own name")
        app.data_var.set(str(data))
        app.output_var.set(str(tmp_path))
        assert app.project_var.get() == "my own name"

    def test_data_folder_is_read_directly_with_no_domain_subfolder(
            self, app, project):
        """Data folder IS the folder holding the session subfolders,
        with no extra nesting expected."""
        data_folder, _out, _name = project
        app.data_var.set(data_folder)
        assert app._input_dir() == data_folder

    def test_metadata_is_auto_detected_reactively(self, app, project):
        data_folder, _output_folder, _name = project
        app._show_home()
        app.data_var.set(data_folder)
        assert app._file_count == 1
        assert app.metadata_path_var.get() == os.path.join(
            data_folder, "_metadata.csv")

    def test_changing_data_folder_clears_stale_metadata(
            self, app, project, tmp_path):
        data_folder, _out, _name = project
        app._show_home()
        app.data_var.set(data_folder)
        assert app.metadata_path_var.get()

        other = tmp_path / "no_metadata_here"
        (other / "2025_mouse_M002_optomotor_visualacuity").mkdir(
            parents=True)
        app.data_var.set(str(other))
        assert app.metadata_path_var.get() == ""


_SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "samples",
                                "data", "Demo Project")


class TestBundledSample:
    """Drives the GUI against the real bundled sample project (not a
    throwaway tmp_path fixture), the one a user opens by following
    samples/README.md, so it has to actually work through the app, not
    just through the engine directly (see tests/test_samples.py)."""

    pytestmark = pytest.mark.skipif(
        not os.path.isdir(_SAMPLE_DATA_DIR),
        reason="samples/data/Demo Project not present, run "
              "samples/_fabricate_samples.py first")

    def test_sample_project_runs_end_to_end_through_the_gui(self, app,
                                                             tmp_path):
        app._show_home()
        app.data_var.set(_SAMPLE_DATA_DIR)
        app.output_var.set(str(tmp_path))
        app.project_var.set("Demo run")
        assert app._file_count == 4          # 2 animals x 2 sessions each
        assert app.metadata_path_var.get()   # detected automatically
        assert app.start_btn._state == "normal"

        app._do_run()
        df = pd.read_csv(app.output_csv_path).set_index("Mouse_ID")
        assert set(df.index) == {"M001", "M002"}
        assert df.loc["M002", "contrast_0.011_cycles"] == 99.99


class TestRun:
    def test_end_to_end_run_produces_the_report(self, app, project):
        app._show_home()
        _enter(app, project)
        app._do_run()          # the worker body, synchronously

        assert app.output_csv_path is not None
        df = pd.read_csv(app.output_csv_path)
        assert df.loc[0, "Mouse_ID"] == "M001"
        assert df.loc[0, "visual_acuity_cycles"] == 0.5
        # Output lands directly under {Output folder}/{Project}/, with
        # no extra folder named after the domain.
        _data_folder, output_folder, name = project
        assert app.output_csv_path == os.path.join(
            output_folder, name, "optodrum_report.csv")

    def test_running_page_shows_only_cancel(self, app):
        app._show_running()
        app.root.update_idletasks()
        assert app.cancel_btn.winfo_manager() == "pack"
        assert not app.back_btn.winfo_ismapped()
        assert not app.start_btn.winfo_ismapped()

    def test_cancel_returns_to_home(self, app, project):
        app._show_home()
        _enter(app, project)
        app._show_running()
        app._cancel_run()
        app.root.update_idletasks()
        assert app.back_btn.winfo_ismapped()

    def test_finished_run_shows_only_open_folder_link(self, app, project):
        app._show_home()
        _enter(app, project)
        app._show_running()
        out_dir = app._output_dir()
        os.makedirs(out_dir, exist_ok=True)
        app.output_csv_path = os.path.join(out_dir, "optodrum_report.csv")
        app._run_finished()
        app.root.update_idletasks()
        assert app._open_folder_btn.winfo_ismapped()
        assert app._open_folder_btn._text == "Open folder"
