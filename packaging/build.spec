# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for OptoDrum Connector: a self-contained build that needs no Python
# and no internet on the machine that runs it.
#
#   macOS:   dist/OptoDrum Connector.app          (build on the architecture to target:
#                                      Apple Silicon or Intel)
#   Windows: dist\OptoDrum Connector\OptoDrum Connector.exe   (the whole OptoDrum Connector folder is the app)
#
# Use packaging/build_macos.sh or packaging\build_windows.bat, which set up
# the pinned environment (packaging/requirements-lock.txt), run this spec,
# run the packaged app's own --selftest and zip the result.
#
# Both platforms build a folder ("onedir"), not a single self-extracting
# file: a single file has to unpack a few hundred MB to a temporary folder
# on every launch (slow from a USB stick, and a common antivirus trigger),
# and a macOS .app is a folder anyway.
#
# Module search paths below mirror the sys.path bootstrap at the top of
# app/OptoDrum Connector GUI.py; a folder added there must be added here too. If the
# packaged app reports ModuleNotFoundError for a submodule loaded by
# name, add it to hiddenimports.

import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(SPEC)), ".."))
APP_NAME = "OptoDrum Connector"
ENTRY = os.path.join(ROOT, "app", "OptoDrum Connector GUI.py")

with open(ENTRY, encoding="utf-8") as fh:
    VERSION = re.search(r'^APP_VERSION = "([^"]+)"', fh.read(), re.M).group(1)

# Example projects offered by "Try an example project" on Home.
EXAMPLES = ['Demo Project']

datas = [(os.path.join(ROOT, "assets"), "assets")]
for example in EXAMPLES:
    datas.append((os.path.join(ROOT, "samples", "data", example),
                  os.path.join("samples", "data", example)))

a = Analysis(
    [ENTRY],
    pathex=[os.path.join(ROOT, p) for p in ['app', 'helpers', 'steps/optodrum']],
    binaries=[],
    datas=datas,
    hiddenimports=["selftest", "locale_es"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter.test', 'pytest', 'IPython', 'jupyter', 'notebook', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'sphinx', 'docutils', 'scipy', 'matplotlib', 'statsmodels', 'sklearn', 'pingouin', 'seaborn', 'plotly', 'xarray'],
    noarchive=False,
)
pyz = PYZ(a.pure)

version_info = None
if sys.platform == "win32":
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo, StringFileInfo, StringStruct, StringTable,
        VarFileInfo, VarStruct, VSVersionInfo)
    nums = tuple(int(n) for n in (VERSION.split(".") + ["0"] * 4)[:4])
    version_info = VSVersionInfo(
        ffi=FixedFileInfo(filevers=nums, prodvers=nums),
        kids=[
            StringFileInfo([StringTable("040904B0", [
                StringStruct("LegalCopyright", "Copyright 2026 Michael D. Espitia Arias"),
                StringStruct("FileDescription", "OptoDrum Connector - optomotor staircase results"),
                StringStruct("FileVersion", VERSION),
                StringStruct("InternalName", APP_NAME),
                StringStruct("OriginalFilename", APP_NAME + ".exe"),
                StringStruct("ProductName", APP_NAME),
                StringStruct("ProductVersion", VERSION)])]),
            VarFileInfo([VarStruct("Translation", [1033, 1200])]),
        ])

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(ROOT, "assets",
                      "app_icon.ico" if sys.platform == "win32"
                      else "app_icon.icns"),
    version=version_info,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=APP_NAME,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=APP_NAME + ".app",
        icon=os.path.join(ROOT, "assets", "app_icon.icns"),
        bundle_identifier="com.despitiaarias.optodrumconnector",
        version=VERSION,
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "CFBundleShortVersionString": VERSION,
            "CFBundleVersion": VERSION,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": (
                "12.0" if os.uname().machine == "arm64" else "11.0"),
            "LSApplicationCategoryType": "public.app-category.education",
            "NSHumanReadableCopyright": "Copyright 2026 Michael D. Espitia Arias",
        },
    )
