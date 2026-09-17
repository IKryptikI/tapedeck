#!/usr/bin/env bash
# Linux/macOS equivalent of run-server.cmd - launched by the
# tapedeck-server.service systemd user unit (see systemd/), or run directly.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

LOGDIR="${XDG_STATE_HOME:-$HOME/.local/state}/tapedeck"
mkdir -p "$LOGDIR"
echo "---- $(date) starting server ----" >> "$LOGDIR/server.log"

PYTHON="python3"
[ -x .venv/bin/python ] && PYTHON=.venv/bin/python

exec "$PYTHON" server.py >> "$LOGDIR/server.log" 2>&1
