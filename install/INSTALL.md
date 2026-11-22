# Installing OptoDrum Connector from source

This guide describes the installation of OptoDrum Connector from its
source code on macOS and Windows; no prior knowledge of Python is
required. The standalone application, which requires neither Python nor
a network connection, is described in the
[README](../README.md#standalone-application).

The installation takes 2 to 5 minutes and comprises four stages:

1. Download of OptoDrum Connector from GitHub.
2. Installation of Python 3.12, once per computer (Python 3.10, 3.11
   and 3.13 are also supported; 3.14 and later are not).
3. Execution of the installer script included with the application.
4. Start of the application with the **Launch Optodrum** launcher.

---

## macOS

### 1. Download

https://github.com/michaeldespitiaarias/conector-for-optodrum →
**Code** → **Download ZIP**; the unpacked folder is placed in any
location.

### 2. Python

1. https://www.python.org/downloads/release/python-31210/ → *Files* →
   **macOS 64-bit universal2 installer**.
2. The downloaded `.pkg` is run with its default settings.

### 3. Installer

1. In Finder, `install/install.sh` is opened with a double click. If it
   opens as text, the file is dragged onto a Terminal window and run
   with Return.
2. The packages are downloaded in about one minute; the script ends
   with `✓ Installation complete`.

### 4. Start

`app/Launch Optodrum.command` is opened with a double click. On first
use macOS may report that the file comes from an unidentified
developer; it is then opened from the context menu (**Open** →
**Open**), and subsequent double clicks open it directly.

---

## Windows

### 1. Download

https://github.com/michaeldespitiaarias/conector-for-optodrum →
**Code** → **Download ZIP**; the archive is unpacked (**Extract All**)
to any location.

### 2. Python

1. https://www.python.org/downloads/release/python-31210/ → *Files* →
   **Windows installer (64-bit)**.
2. On the first screen of the installer, **Add python.exe to PATH** is
   selected before **Install Now**.

### 3. Installer

`install\install.bat` is opened with a double click; the packages are
downloaded in about one minute and the script ends with
`Installation complete`.

### 4. Start

`app\Launch Optodrum.bat` is opened with a double click. On first use
Windows SmartScreen may display *Windows protected your PC*; **More
info** → **Run anyway** allows it.

---

## Use

The launchers inside `app/` start the application without a terminal:
`Launch Optodrum.command` (macOS) and `Launch Optodrum.bat` (Windows).

## Troubleshooting

| Symptom | Resolution |
|---|---|
| *Python 3.10 to 3.13 not found* | Python 3.12 is installed (stage 2); on Windows, with **Add python.exe to PATH** selected |
| *tkinter is missing* (Linux) | `sudo apt install python3-tk` (Debian, Ubuntu); tkinter is included with Python on macOS and Windows |
| The launcher opens a terminal but no window appears | The installer script is run again; it completes an interrupted installation |
| Home reports 0 `.summary` files | The Data folder is the folder that directly contains the session folders (`<year>_mouse_<ID>_<Experiment>_<Test_Type>/`) |
| Errors after an update | The hidden `.venv/` folder is deleted and the installer script is run again |
