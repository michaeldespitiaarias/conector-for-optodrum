#!/bin/bash
# ────────────────────────────────────────────────────────────────────
#  OptoDrum Connector installer: macOS / Linux
#
#  What it does (nothing sudo):
#    1. Checks that Python 3.10+ is installed. If not, tells you how
#       to get it.
#    2. Creates an isolated virtual environment at ./.venv at the
#       repo root (so this app's dependencies don't touch your other
#       Python projects).
#    3. Installs the packages listed in docs/requirements.txt.
#    4. Makes `app/Launch Optodrum.command` executable so a
#       double click in Finder just works from now on.
#
#  Layout convention:
#    install/     ← this file lives here alongside INSTALL.md and
#                    install.bat.
#    docs/        ← requirements.txt.
#    app/         ← the GUI (Launch Optodrum.{command,bat} sit next
#                    to OptoDrum Connector GUI.py so the launcher's
#                    `cd "$(dirname "$0")"` also cd's into the app
#                    code).
#    (repo root)  ← code folders (app/, steps/, ...) and the venv it
#                    creates when you run this script.
# ────────────────────────────────────────────────────────────────────
set -e

# This script lives in install/. Everything the installer touches
# hangs off the repo root, so resolve that first.
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$INSTALL_DIR/.." && pwd)"

# Terminal colours
GREEN="\033[0;32m"; BLUE="\033[0;34m"; RED="\033[0;31m"
BOLD="\033[1m"; RESET="\033[0m"

echo
echo -e "${BOLD}${BLUE}════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${BLUE}  OptoDrum Connector installer${RESET}"
echo -e "${BOLD}${BLUE}════════════════════════════════════════════${RESET}"
echo

# ── 1. Detect Python 3.10+ ─────────────────────────────────────────
PYTHON=""
for py in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$py" >/dev/null 2>&1; then
        version=$("$py" --version 2>&1 | awk '{print $2}')
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON="$py"
            echo -e "  ${GREEN}✓${RESET} Found $PYTHON ($version)"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "  ${RED}✗ Python 3.10 or newer not found${RESET}"
    echo
    echo "  Please install Python first:"
    echo "    macOS: download from https://www.python.org/downloads/"
    echo "           (the installer adds Python to your PATH)"
    echo "    Linux: sudo apt install python3.11 python3.11-venv"
    echo "           (or the equivalent for your distro)"
    echo
    echo "  Then run this installer again."
    exit 1
fi

# ── 2. Create virtual environment ──────────────────────────────────
VENV_DIR="$REPO_ROOT/.venv"
if [ -d "$VENV_DIR" ]; then
    echo -e "  ${GREEN}✓${RESET} Virtual environment already exists, reusing it"
else
    echo -e "  ${BLUE}▸${RESET} Creating isolated virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

# ── 3. Install dependencies ────────────────────────────────────────
echo -e "  ${BLUE}▸${RESET} Installing packages from docs/requirements.txt"
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -r "$REPO_ROOT/docs/requirements.txt" --quiet
echo -e "  ${GREEN}✓${RESET} Packages installed"

# ── 4. Ensure launcher is executable ───────────────────────────────
chmod +x "$REPO_ROOT/app/Launch Optodrum.command"

# ── Done ───────────────────────────────────────────────────────────
echo
echo -e "${BOLD}${GREEN}✓ Installation complete${RESET}"
echo
echo "  To open OptoDrum Connector:"
echo -e "    Double click ${BOLD}app/Launch Optodrum.command${RESET} in Finder,"
echo "    or run it from Terminal:"
echo "      bash \"$REPO_ROOT/app/Launch Optodrum.command\""
echo
echo "  On the first launch macOS may show a warning"
echo "  \"can't be opened because it is from an unidentified developer\"."
echo "  Right click (or Ctrl click) the .command file, then Open, then Open."
echo "  You only need to do this once."
echo
