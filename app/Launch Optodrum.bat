@echo off
cd /d "%~dp0"

REM Prefer the isolated virtualenv that install\install.bat sets up
REM (Conector for Optodrum\.venv\ at the repo root), falling back to
REM whatever `python` is on PATH.
set "VENV_PY=%~dp0..\.venv\Scripts\python.exe"
if exist "%VENV_PY%" (
    set "PY=%VENV_PY%"
) else (
    set "PY=python"
)

set PYTHONDONTWRITEBYTECODE=1
"%PY%" "OptoDrum Connector GUI.py"
if errorlevel 1 pause
