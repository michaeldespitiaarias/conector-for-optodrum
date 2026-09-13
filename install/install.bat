@echo off
REM ────────────────────────────────────────────────────────────────────
REM  OptoDrum Connector installer: Windows
REM
REM  Creates an isolated virtual environment at ..\.venv\ (repo root),
REM  installs the packages in ..\docs\requirements.txt, and leaves you
REM  a Launch Optodrum.bat in this same folder, which you can double
REM  click and which always uses that isolated environment.
REM
REM  Layout convention:
REM    install\     ← this file lives here alongside INSTALL.md and
REM                    install.sh.
REM    docs\        ← requirements.txt.
REM    app\         ← the GUI (Launch Optodrum.{command,bat} sit next
REM                    to OptoDrum Connector GUI.py).
REM    (repo root)  ← code folders (app\, steps\, ...) and the venv it
REM                    creates when you run this script.
REM
REM  Requires Python 3.10 or newer already installed on this machine
REM  (https://www.python.org/downloads/, during install tick the
REM  "Add python.exe to PATH" checkbox).
REM ────────────────────────────────────────────────────────────────────
setlocal enabledelayedexpansion

REM %~dp0 is install\ (with trailing backslash). Everything the
REM installer touches hangs off the repo root, one level up.
set "INSTALL_DIR=%~dp0"
pushd "%INSTALL_DIR%.." >nul
set "REPO_ROOT=%CD%"
popd >nul

echo.
echo ============================================
echo   OptoDrum Connector installer
echo ============================================
echo.

REM ── 1. Detect Python ────────────────────────────────────────────────
set "PYTHON="
for %%p in (py python python3) do (
    where %%p >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=2" %%v in ('%%p --version 2^>^&1') do (
            set "ver=%%v"
            for /f "tokens=1,2 delims=." %%a in ("!ver!") do (
                if %%a GEQ 3 if %%b GEQ 10 (
                    set "PYTHON=%%p"
                    echo   [OK]  Found %%p !ver!
                    goto :python_ok
                )
            )
        )
    )
)

echo   [!!] Python 3.10 or newer not found.
echo.
echo   Install Python from:
echo     https://www.python.org/downloads/
echo   During installation, tick the "Add python.exe to PATH" box.
echo   Then run this installer again by double clicking it.
echo.
pause
exit /b 1

:python_ok

REM ── 2. Create virtual environment ──────────────────────────────────
set "VENV_DIR=%REPO_ROOT%\.venv"
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo   [OK]  Virtual environment already exists, reusing it
) else (
    echo   [..] Creating isolated virtual environment ...
    %PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo   [!!] Failed to create virtual environment.
        echo   On Debian or Ubuntu based systems you may need:
        echo     sudo apt install python3-venv
        pause
        exit /b 1
    )
)

REM ── 3. Install dependencies ────────────────────────────────────────
echo   [..] Installing packages from docs\requirements.txt
call "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip --quiet
call "%VENV_DIR%\Scripts\python.exe" -m pip install -r "%REPO_ROOT%\docs\requirements.txt" --quiet
if errorlevel 1 (
    echo   [!!] Package installation failed. See error above.
    pause
    exit /b 1
)
echo   [OK]  Packages installed
echo.

echo ============================================
echo   Installation complete
echo ============================================
echo.
echo   To open OptoDrum Connector:
echo     Double click  app\Launch Optodrum.bat
echo.
echo   On the first launch Windows SmartScreen may warn about an
echo   unknown publisher. Click "More info" ^> "Run anyway".
echo   You only need to do this once.
echo.
pause
