# OptoDrum Connector

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22734758.svg)](https://doi.org/10.5281/zenodo.22734758)

OptoDrum Connector is a desktop application that converts the
`.summary` staircase exports of the OptoDrum optomotor system into one
wide table, `optodrum_report.csv`, with one row per animal and session:
the visual acuity threshold and the contrast sensitivity threshold at
every spatial frequency tested, joined with the metadata. The table can
be analysed in any statistical or plotting software. The application
performs no statistical analysis and draws no plots.

## Installation

### Standalone application

Self-contained builds are published on the repository's
[Releases](../../releases) page:

| Platform | Archive |
|---|---|
| macOS, Apple silicon (macOS 12 or later) | `OptoDrum Connector-macOS-Apple-Silicon.zip` |
| macOS, Intel processor (macOS 11 or later) | `OptoDrum Connector-macOS-Intel.zip` |
| Windows 10 or 11, 64-bit | `OptoDrum Connector-Windows.zip` |

Each archive contains Python, every required package and the example
project; no installation and no network connection are required. The
application is `OptoDrum Connector.app` on macOS and
`OptoDrum Connector.exe`, inside the unpacked folder, on Windows; the
Windows executable depends on the files beside it and remains in that
folder.

The builds are not signed. On first launch macOS requests confirmation
through the context menu (**Open** → **Open**) or, when only *Move to
Trash* is offered, through **System Settings → Privacy & Security →
Open Anyway**; Windows SmartScreen requests **More info → Run anyway**.
Each session is logged to
`~/Library/Logs/OptoDrum Connector/OptoDrum Connector.log` (macOS) or
`%LOCALAPPDATA%\OptoDrum Connector\Logs\OptoDrum Connector.log`
(Windows).

### From source

Python 3.10 to 3.13 with tkinter is required.
[`install/INSTALL.md`](install/INSTALL.md) describes the procedure;
`bash install/install.sh` (macOS, Linux) or `install\install.bat`
(Windows) creates a virtual environment with the tested package
versions, and `app/Launch Optodrum.command` or `app\Launch Optodrum.bat`
starts the application.

### Building the standalone application

`bash packaging/build_macos.sh arm64` (or `x86_64`, under Rosetta on
Apple silicon) and `packaging\build_windows.bat` build the application
with a private Python 3.12 and the pinned package set in
`packaging/requirements-lock.txt`, run the packaged application's
`--selftest` and write the archive to `dist/macOS/` or `dist/Windows/`
only when the self-test passes. Signing and notarisation are described
in [`packaging/SIGNING.md`](packaging/SIGNING.md).

## Use

The application consists of one page with two sections:

- **Input**: **Data folder**, containing the session folders with their
  `.summary` files, and **Metadata**, detected in the Data folder or
  selected with **Browse**.
- **Output**: **Output folder** and **Project name** (proposed from the
  name of the Data folder and editable).

A status line reports the number of `.summary` files detected; **Run**
is enabled when it is above zero. At the end of the run the page states
the number of animals written and lists every file skipped (folder name
not following the convention below) or unreadable. The interface is
available in English and Spanish, with a light, a dark or a
system-matched appearance, selected under **Settings**; **Help**
describes every field.

**No data at hand? Load an example project** on Home copies the
bundled Demo Project (two animals, both staircase types) to
`~/Documents/OptoDrum Connector examples/` and fills in every field;
see [`samples/README.md`](samples/README.md).

## Input data

```
{Data folder}/
├── 2025_mouse_M001_optomotor_visualacuity/
│   └── trial1.summary
├── 2025_mouse_M001_optomotor_0.011/
│   └── trial1.summary
├── …
└── _metadata.{csv|xlsx|txt}         optional
```

Each `.summary` file lies in a session folder whose name is read by
position: `<year>_mouse_<Mouse_ID>_<Experiment>_<Test_Type>`.

| Field | Content |
|---|---|
| `Mouse_ID` | Animal identifier, matched exactly against the identifier column of the metadata |
| `Experiment` | Copied to `optodrum_report.csv` |
| `Test_Type` | Determines whether the files are read as an ACUITY or a CONTRAST staircase; not stored |

A folder whose name does not follow this pattern is skipped. Files are
read with Latin-1 encoding.

## Output

```
{Output folder}/{Project}/
└── optodrum_report.csv
```

| Column | Content |
|---|---|
| `Mouse_ID` | From the folder name |
| `Experiment` | From the folder name |
| metadata columns | From the metadata table, joined by the identifier |
| `visual_acuity_cycles` | Threshold of the ACUITY staircase |
| `contrast_<n>_cycles` | Contrast threshold at each spatial frequency, in ascending order of frequency |

A contrast value of −1 (below the detection threshold) is stored as
99.99; other negative values are stored as missing. An `Experiment`
column of the metadata is ignored in favour of the folder name.

## Repository layout

```
├── app/                      Graphical interface, launchers, self-test,
│                             interface text (English, Spanish)
├── steps/optodrum/           Conversion engine
├── helpers/            Metadata input/output
├── samples/                  Example project with its output
├── tests/                    pytest suite (see tests/README.md)
├── assets/                   Logo and application icons
├── install/                  Installation guide and installer scripts
├── packaging/                Standalone build, pinned package versions, signing
└── docs/                     Requirements
```

## Requirements

Python 3.10 to 3.13 with tkinter and the packages listed in
`docs/requirements.txt` (`pandas`, `pillow`, `openpyxl`, `xlrd`); the
exact tested versions are listed in `packaging/requirements-lock.txt`.

## License

[PolyForm Noncommercial License 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0)
(see [`LICENSE`](LICENSE)): use for any noncommercial purpose
(research, teaching, peer review, personal study) is permitted.
Commercial use requires a separate license, requested as an issue at
https://github.com/michaeldespitiaarias/conector-for-optodrum/issues.
