#!/bin/bash
cd "$(dirname "$0")"

# Prefer the isolated virtualenv that install/install.sh sets up
# (Conector for Optodrum/.venv/ at the repo root). Falls back to the
# system `python3` if no venv is present, which lets developers who
# installed the dependency globally keep using their existing setup.
VENV_PY="$(cd .. && pwd)/.venv/bin/python"
if [ -x "$VENV_PY" ]; then
    PY="$VENV_PY"
else
    PY="python3"
fi

# PYTHONDONTWRITEBYTECODE=1 keeps every subprocess from creating
# __pycache__/*.pyc under this tree.
PYTHONDONTWRITEBYTECODE=1 "$PY" "OptoDrum Connector GUI.py"
