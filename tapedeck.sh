#!/usr/bin/env bash
# Linux/macOS equivalent of tapedeck.cmd - opens tapedeck in its own window.
# Double-clickable if your file manager runs .sh files, or point a .desktop
# launcher at it (see tapedeck.desktop).
cd "$(dirname "${BASH_SOURCE[0]}")"

PYTHON="python3"
[ -x .venv/bin/python ] && PYTHON=.venv/bin/python

exec "$PYTHON" app.py
