"""
Tests for steps/optodrum/optodrum.py, the processing engine.
"""
import os
import sys

import pandas as pd
import pytest

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT_DIR, "steps", "optodrum"))

import optodrum  # noqa: E402


def _write_summary(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="latin-1") as fh:
        for line in lines:
            fh.write(line + "\n")


def _acuity_line(cycle):
    return (f'<ContrastSensitivityFunction typeOfStaircase="ACUITY" '
            f'cycle="{cycle}"/>')


def _contrast_line(cycle, contrast):
    return (f'<ContrastSensitivityFunction typeOfStaircase="CONTRAST" '
            f'cycle="{cycle}" contrast="{contrast}"/>')


class TestFolderNameParsing:
    def test_conforming_folder_is_parsed(self, tmp_path):
        data = tmp_path / "data"
        _write_summary(
            str(data / "2025_mouse_M001_optomotor_visualacuity" /
               "trial1.summary"),
            [_acuity_line(0.5)])
        out = tmp_path / "out"
        path = optodrum.process_optodrum(str(data), str(out))
        assert path == str(out / "optodrum_report.csv")
        df = pd.read_csv(path)
        assert df.loc[0, "Mouse_ID"] == "M001"
        assert df.loc[0, "visual_acuity_cycles"] == 0.5

    def test_short_folder_name_is_skipped(self, tmp_path, capsys):
        data = tmp_path / "data"
        _write_summary(str(data / "too_short" / "trial1.summary"),
                      [_acuity_line(0.5)])
        out = tmp_path / "out"
        result = optodrum.process_optodrum(str(data), str(out))
        assert result is None
        assert "unexpected folder name format" in capsys.readouterr().out


class TestAcuityAndContrastExtraction:
    def test_acuity_session_ignores_contrast_lines(self, tmp_path):
        data = tmp_path / "data"
        _write_summary(
            str(data / "2025_mouse_M002_optomotor_visualacuity" /
               "trial1.summary"),
            [_acuity_line(0.4), _contrast_line(0.2, 50)])
        out = tmp_path / "out"
        df = pd.read_csv(optodrum.process_optodrum(str(data), str(out)))
        assert df.loc[0, "visual_acuity_cycles"] == 0.4
        assert "contrast_0.2_cycles" not in df.columns

    def test_contrast_session_ignores_acuity_lines(self, tmp_path):
        data = tmp_path / "data"
        _write_summary(
            str(data / "2025_mouse_M003_optomotor_0.011" / "trial1.summary"),
            [_contrast_line(0.011, 30), _acuity_line(0.9)])
        out = tmp_path / "out"
        df = pd.read_csv(optodrum.process_optodrum(str(data), str(out)))
        assert df.loc[0, "contrast_0.011_cycles"] == 30
        assert "visual_acuity_cycles" not in df.columns

    def test_zero_or_negative_acuity_cycle_is_discarded(self, tmp_path):
        data = tmp_path / "data"
        _write_summary(
            str(data / "2025_mouse_M004_optomotor_visualacuity" /
               "trial1.summary"),
            [_acuity_line(0)])
        out = tmp_path / "out"
        # The row is still produced (its key is seeded from the folder
        # name before any value is read) but carries no acuity column:
        # a cycle of 0 is not a real threshold.
        df = pd.read_csv(optodrum.process_optodrum(str(data), str(out)))
        assert df.loc[0, "Mouse_ID"] == "M004"
        assert "visual_acuity_cycles" not in df.columns

    @pytest.mark.parametrize("raw,expected", [
        (-1, 99.99),      # below detection threshold
        (-5, None),       # any other negative value is missing
        (25, 25.0),       # a real positive threshold passes through
    ])
    def test_contrast_special_values(self, tmp_path, raw, expected):
        data = tmp_path / "data"
        _write_summary(
            str(data / "2025_mouse_M005_optomotor_0.5" / "trial1.summary"),
            [_contrast_line(0.5, raw)])
        out = tmp_path / "out"
        df = pd.read_csv(optodrum.process_optodrum(str(data), str(out)))
        value = df.loc[0, "contrast_0.5_cycles"]
        if expected is None:
            assert pd.isna(value)
        else:
            assert value == expected


class TestColumnOrdering:
    def test_contrast_columns_sorted_ascending_by_cycle(self, tmp_path):
        data = tmp_path / "data"
        _write_summary(
            str(data / "2025_mouse_M006_optomotor_0.5" / "trial1.summary"),
            [_contrast_line(0.5, 10)])
        _write_summary(
            str(data / "2025_mouse_M006_optomotor_0.1" / "trial2.summary"),
            [_contrast_line(0.1, 20)])
        _write_summary(
            str(data / "2025_mouse_M006_optomotor_0.3" / "trial3.summary"),
            [_contrast_line(0.3, 30)])
        out = tmp_path / "out"
        df = pd.read_csv(optodrum.process_optodrum(str(data), str(out)))
        contrast_cols = [c for c in df.columns if c.startswith("contrast_")]
        assert contrast_cols == ["contrast_0.1_cycles", "contrast_0.3_cycles",
                                 "contrast_0.5_cycles"]


class TestMetadataMerge:
    def test_metadata_columns_are_merged_by_first_column(self, tmp_path):
        data = tmp_path / "data"
        _write_summary(
            str(data / "2025_mouse_M007_optomotor_visualacuity" /
               "trial1.summary"),
            [_acuity_line(0.6)])
        meta_path = tmp_path / "_metadata.csv"
        pd.DataFrame({"Mouse_ID": ["M007"], "Genotype": ["WT"],
                     "Group": ["Control"]}).to_csv(meta_path, index=False)
        out = tmp_path / "out"
        df = pd.read_csv(optodrum.process_optodrum(
            str(data), str(out), metadata_path=str(meta_path)))
        assert list(df.columns) == ["Mouse_ID", "Genotype", "Group",
                                    "visual_acuity_cycles"]
        assert df.loc[0, "Genotype"] == "WT"

    def test_missing_metadata_file_is_tolerated(self, tmp_path):
        data = tmp_path / "data"
        _write_summary(
            str(data / "2025_mouse_M008_optomotor_visualacuity" /
               "trial1.summary"),
            [_acuity_line(0.6)])
        out = tmp_path / "out"
        df = pd.read_csv(optodrum.process_optodrum(
            str(data), str(out),
            metadata_path=str(tmp_path / "nope.csv")))
        assert df.loc[0, "Mouse_ID"] == "M008"


class TestNoData:
    def test_empty_input_folder_writes_nothing(self, tmp_path):
        data = tmp_path / "data"
        data.mkdir()
        out = tmp_path / "out"
        assert optodrum.process_optodrum(str(data), str(out)) is None
        assert not (out / "optodrum_report.csv").exists()


class TestPathHelpers:
    def test_count_files_counts_recursively(self, tmp_path):
        _write_summary(str(tmp_path / "a" / "x.summary"), ["x"])
        _write_summary(str(tmp_path / "a" / "b" / "y.summary"), ["y"])
        (tmp_path / "not_a_summary.txt").write_text("x")
        assert optodrum.count_files(str(tmp_path)) == 2


class TestMetadataFormats:
    """The GUI resolves paths itself (Data folder / Output folder /
    Project fields); the engine's own remaining metadata responsibility
    is reading whatever format it is handed, which includes .xlsx/.txt,
    not just .csv."""

    def test_xlsx_metadata_is_merged(self, tmp_path):
        pytest.importorskip("openpyxl")
        data = tmp_path / "data"
        _write_summary(
            str(data / "2025_mouse_M009_optomotor_visualacuity" /
               "trial1.summary"),
            [_acuity_line(0.6)])
        meta_path = tmp_path / "_metadata.xlsx"
        pd.DataFrame({"Mouse_ID": ["M009"], "Genotype": ["KO"]}).to_excel(
            meta_path, index=False)
        out = tmp_path / "out"
        df = pd.read_csv(optodrum.process_optodrum(
            str(data), str(out), metadata_path=str(meta_path)))
        assert df.loc[0, "Genotype"] == "KO"

    def test_tab_separated_txt_metadata_is_merged(self, tmp_path):
        data = tmp_path / "data"
        _write_summary(
            str(data / "2025_mouse_M010_optomotor_visualacuity" /
               "trial1.summary"),
            [_acuity_line(0.6)])
        meta_path = tmp_path / "_metadata.txt"
        meta_path.write_text("Mouse_ID\tGenotype\nM010\tWT\n")
        out = tmp_path / "out"
        df = pd.read_csv(optodrum.process_optodrum(
            str(data), str(out), metadata_path=str(meta_path)))
        assert df.loc[0, "Genotype"] == "WT"
