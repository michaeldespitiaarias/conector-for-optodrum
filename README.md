# OptoDrum Connector

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22734759.svg)](https://doi.org/10.5281/zenodo.22734759)

Turns OptoDrum `.summary` staircase exports into one structured,
wide format `optodrum_report.csv`: one row per animal, with the visual
acuity threshold and the contrast sensitivity threshold at every
spatial frequency tested.

A standalone desktop app with its own grey identity, focused on doing
one job well: no statistics, no plots. No wizard either, since its
single engine call doesn't need one, so Home carries everything
(folders, detected files, metadata, Run). `optodrum_report.csv` is a
plain wide format measurement table. Load it into whatever statistics
or plotting tool you already use.

## Overview

One step only, no further steps required.

| Input | Output |
|-------|--------|
| `.summary` files exported by OptoDrum software | `optodrum_report.csv` |

## Structure

```
├── app/                     GUI (splash, Home, theme, help modal)
│   ├── OptoDrum Connector GUI.py
│   ├── theme.py             grey identity, own colour family (eight tokens)
│   ├── widgets.py           vendored rounded tk widgets
│   ├── help_modal.py
│   ├── Launch Optodrum.command
│   └── Launch Optodrum.bat
├── steps/optodrum/optodrum.py   processing engine
├── _helper_skill/metadata_io.py vendored metadata I/O for several formats
├── assets/                  logo + its regenerator script
├── install/                 INSTALL.md, install.sh, install.bat
├── docs/requirements.txt
├── samples/                 bundled demo project, see samples/README.md
└── tests/                   pytest suite
```

## Usage

Double click `app/Launch Optodrum.command` (macOS) or `app\Launch
Optodrum.bat` (Windows); `install/INSTALL.md` covers the setup you
only do once. Home has four fields in two sections:

* **INPUT**: **Data folder** (holds your `.summary` session
  subfolders, read directly) and **Metadata** (detected automatically
  under Data folder, Browse otherwise).
* **OUTPUT**: **Output folder** and **Project** (suggested from the
  data folder's own name, freely editable).

Below that, one line reports the detected `.summary` count; press
**Run** once it's above zero. See the "?" help dialog for what each
field does in detail.

**No Python at all, or installing on a machine with no internet
access?** Grab the standalone build from this repo's
[**Releases**](../../releases) page instead: `OptoDrum
Connector-macOS.zip` or `OptoDrum Connector-Windows.zip`. Unzip it,
double click `OptoDrum Connector.app` (or `OptoDrum Connector.exe`),
and it runs on its own: Python and every dependency are already
bundled inside. Copy the unzipped app to a USB drive to carry it to an
offline machine. (Maintainers: `packaging/build.spec` builds this
locally with PyInstaller; `.github/workflows/build-release.yml` builds
both platforms and attaches them to a release automatically whenever a
`v*` tag is pushed.)

## How OptoDrum Connector identifies your data

Every `.summary` file lives inside a session subfolder, and that
subfolder's own name is parsed positionally:

`<year>_mouse_<Mouse_ID>_<Experiment>_<Test_Type>` → e.g.
`2025_mouse_M001_optomotor_visualacuity`

| Field | Meaning |
|---|---|
| `Mouse_ID` | Joined against `_metadata`'s own identifier column using an exact match |
| `Experiment` | Carried through to `optodrum_report.csv` unchanged |
| `Test_Type` | Not stored. Only tells the parser whether to read this folder's `.summary` files as an ACUITY or a CONTRAST staircase |

A subfolder that doesn't match this exact shape is skipped outright,
not partially parsed.

```
{Data folder}/
├── 2025_mouse_M001_optomotor_visualacuity/
│   └── trial1.summary
├── 2025_mouse_M001_optomotor_0.011/
│   └── trial1.summary
├── ...
└── _metadata.csv                    optional, .xlsx/.txt also read
```

## Output

```
{Output folder}/{Project}/
└── optodrum_report.csv
```

| Column | Description |
|--------|-------------|
| `Mouse_ID` | Extracted from folder name |
| `Experiment` | Extracted from folder name |
| `visual_acuity_cycles` | Threshold from ACUITY staircase |
| `contrast_<n>_cycles` | Contrast threshold per spatial frequency, sorted ascending |

Contrast = -1 is stored as 99.99 (below detection threshold); other
negative values as NaN. Any metadata columns (Genotype, Gender, Group,
...) are merged in by the identifier column.

## Trying it

No real data on hand? `samples/data/Demo Project` is a bundled demo
with two animals; see `samples/README.md`.

## Dependencies

`pandas`, `pillow` (splash logo). See `docs/requirements.txt`.

## License

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0),
see [`LICENSE`](LICENSE). Free for any noncommercial purpose (academic
research, teaching, peer review, personal study). Commercial use
requires a separate license from the author; contact
esspitia@gmail.com.
