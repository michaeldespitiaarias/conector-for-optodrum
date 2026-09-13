# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for OptoDrum Connector, one portable build needing
# no Python or internet on the machine that runs it.
#
#   macOS:   pyinstaller packaging/build.spec        → dist/OptoDrum Connector.app
#   Windows: pyinstaller packaging\build.spec         → dist\OptoDrum Connector.exe
#
# Run from the repo root (so relative paths below resolve correctly),
# or use the wrapper scripts in this same folder.
#
# macOS builds onedir, not onefile: a onefile build extracts itself again
# to a temp folder on every launch, which PyInstaller itself warns
# clashes with wrapping the result in a real .app bundle (a .app is
# already a folder, so a single file inside it defeats the purpose,
# and in testing this combination produced an app that launched a
# process but never rendered a window). Windows keeps onefile: on
# that platform there is no bundle step, so a single portable .exe is
# both possible and what "one executable" means there.

import sys
import os

_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(SPEC)), ".."))
_APP_ENTRY = os.path.join(_ROOT, "app", "OptoDrum Connector GUI.py")
_ONEFILE = sys.platform != "darwin"

a = Analysis(
    [_APP_ENTRY],
    pathex=[
        os.path.join(_ROOT, "app"),
        os.path.join(_ROOT, "_helper_skill"),
        os.path.join(_ROOT, "steps", "optodrum"),
    ],
    binaries=[],
    datas=[
        (os.path.join(_ROOT, "assets"), "assets"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries if _ONEFILE else [],
    a.datas if _ONEFILE else [],
    [],
    exclude_binaries=not _ONEFILE,
    name="OptoDrum Connector",
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
)

if _ONEFILE:
    # Windows (and any other target): the EXE above already
    # carries every binary/data file, so there is nothing left to
    # collect or bundle. dist/OptoDrum Connector.exe is the whole
    # deliverable.
    pass
else:
    # macOS: onedir. Collect binaries/datas alongside the thin
    # bootloader executable, then wrap the pair into a real .app
    # bundle a user can double click, with its own Dock icon and
    # process identity.
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name="OptoDrum Connector",
    )
    app = BUNDLE(
        coll,
        name="OptoDrum Connector.app",
        icon=None,
        bundle_identifier="com.despitiaarias.optodrumconnector",
        info_plist={
            "NSHighResolutionCapable": "True",
            "CFBundleShortVersionString": "1.0.0",
        },
    )
