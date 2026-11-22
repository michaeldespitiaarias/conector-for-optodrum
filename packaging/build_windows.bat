@echo off
rem Build the standalone Windows app.
rem
rem   Double-click this file, or run  packaging\build_windows.bat  from a
rem   command prompt in the repository folder.
rem
rem Needs internet the first time (it downloads a private Python and the
rem pinned packages into packaging\.build-cache\, which is never committed);
rem the app it produces needs neither Python nor internet.
rem
rem Output: dist\Windows\OptoDrum Connector-Windows.zip, holding a "OptoDrum Connector" folder with
rem OptoDrum Connector.exe inside. The build fails unless the packaged app passes its
rem own --selftest.
setlocal EnableExtensions
set "APP=OptoDrum Connector"
cd /d "%~dp0.."
set "REPO=%CD%"
set "CACHE=%REPO%\packaging\.build-cache"
set "ENV=%CACHE%\env-win64"
set "MM=%CACHE%\micromamba\Library\bin\micromamba.exe"
set "MAMBA_ROOT_PREFIX=%CACHE%\mamba-root"
if not exist "%CACHE%" mkdir "%CACHE%"

rem -- Private Python (conda-forge) ----------------------------------------
if not exist "%MM%" (
  echo Downloading micromamba...
  if not exist "%CACHE%\micromamba" mkdir "%CACHE%\micromamba"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing https://micro.mamba.pm/api/micromamba/win-64/latest -OutFile '%CACHE%\micromamba.tar.bz2'" || goto :fail
  tar -xjf "%CACHE%\micromamba.tar.bz2" -C "%CACHE%\micromamba" Library/bin/micromamba.exe || goto :fail
)
if not exist "%ENV%\python.exe" (
  echo Creating the build environment...
  "%MM%" create -y -q -p "%ENV%" -c conda-forge python=3.12.10 tk=8.6 pip || goto :fail
)
"%ENV%\python.exe" -m pip install -q --only-binary=:all: -r packaging\requirements-lock.txt pyinstaller==6.16.0 || goto :fail

rem -- Build ----------------------------------------------------------------
set "DIST=%CACHE%\dist-win64"
if exist "%DIST%" rmdir /s /q "%DIST%"
if exist "%CACHE%\work-win64" rmdir /s /q "%CACHE%\work-win64"
"%ENV%\python.exe" -m PyInstaller --noconfirm --clean --distpath "%DIST%" --workpath "%CACHE%\work-win64" packaging\build.spec || goto :fail

rem -- Self-test the packaged app itself ---------------------------------------
echo Running the packaged app's self-test...
start "" /wait "%DIST%\%APP%\%APP%.exe" --selftest
if errorlevel 1 (
  echo SELF-TEST FAILED. Log:
  powershell -NoProfile -Command "Get-Content -Tail 60 '%LOCALAPPDATA%\%APP%\Logs\%APP%.log'"
  goto :fail
)
powershell -NoProfile -Command "Get-Content -Tail 6 '%LOCALAPPDATA%\%APP%\Logs\%APP%.log'"

rem -- Package ---------------------------------------------------------------
if not exist "%REPO%\dist\Windows" mkdir "%REPO%\dist\Windows"
set "ZIP=%REPO%\dist\Windows\%APP%-Windows.zip"
if exist "%ZIP%" del "%ZIP%"
powershell -NoProfile -Command "Compress-Archive -Path '%DIST%\%APP%' -DestinationPath '%ZIP%'" || goto :fail
echo.
echo Done: %ZIP%
if not defined CI pause
exit /b 0

:fail
echo.
echo The build did not finish. See the messages above.
if not defined CI pause
exit /b 1
