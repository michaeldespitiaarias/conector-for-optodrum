# Installing OptoDrum Connector, for users new to Python

OptoDrum Connector is written in Python, but you do **not** need to know
Python to use it. This guide walks through installation in plain steps
for **macOS** and **Windows**.

Total time: **2 to 5 minutes** on your first machine.

***

## Overview

1. Download OptoDrum Connector (or receive the folder from a colleague)
2. Install **Python 3.10 or newer**, one time per computer
3. Run the **installer script** that ships with it
4. Double click **Launch Optodrum** whenever you want to open the app

***

## macOS

### Step 1. Install Python

* Open https://www.python.org/downloads/
* Click the big yellow **Download Python 3.x** button
* Open the downloaded `.pkg` file and run through the installer with
  all the default settings

### Step 2. Run the installer

* Open the "Conector for Optodrum" folder in Finder
* Go into the `install/` subfolder
* **Double click** `install.sh` (if it opens as text instead of
  running, open Terminal.app, drag `install.sh` onto it and press
  Return)
* Wait a minute while the packages download. You should see
  `✓ Installation complete` at the end.

### Step 3. Open OptoDrum Connector

* Go into the `app/` subfolder
* **Double click** `Launch Optodrum.command`

The **first time only**, macOS may show:
> "Launch Optodrum.command" can't be opened because it is from an
> unidentified developer.

Right click (or Ctrl click) the file, choose **Open**, then **Open**
in the dialog. From then on, double clicking works normally.

***

## Windows

### Step 1. Install Python

* Open https://www.python.org/downloads/
* Click **Download Python 3.x**
* Run the installer. **IMPORTANT:** on the first screen, tick the
  **"Add python.exe to PATH"** checkbox before clicking "Install Now".

### Step 2. Run the installer

* Open the "Conector for Optodrum" folder in Windows Explorer
* Go into the `install\` subfolder
* **Double click** `install.bat`
* Wait a minute for the packages to install. A message
  `Installation complete` will appear.

### Step 3. Open OptoDrum Connector

* Open the `app\` subfolder
* **Double click** `Launch Optodrum.bat`

The **first time only**, Windows SmartScreen may say:
> Windows protected your PC.

Click **More info**, then **Run anyway**.

***

## Everyday use

After the first install you never need Terminal again: double click
`Launch Optodrum.command` (macOS) or `Launch Optodrum.bat` (Windows)
inside the `app/` folder.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Python 3.10 or newer not found" | Install Python from python.org. On Windows remember the **Add to PATH** tick box |
| "tkinter is missing" (Linux) | `sudo apt install python3-tk` (Debian and Ubuntu). This ships with Python on macOS and Windows |
| Launcher opens Terminal but the GUI never appears | Run the installer script again; it will finish any interrupted setup |
| No projects listed on Home | Create a `data/{Project}/Behavior (OptoDrum)/` folder with your session subfolders, then press Refresh |
| Everything looks broken after an update | Delete the hidden `.venv/` folder, then run the installer again |
