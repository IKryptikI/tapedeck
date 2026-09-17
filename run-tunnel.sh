#!/usr/bin/env bash
# Linux/macOS equivalent of run-tunnel.cmd - launched by the
# tapedeck-tunnel.service systemd user unit (see systemd/), or run directly.
# --wait rides out the race with the server unit; startup order isn't guaranteed.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

LOGDIR="${XDG_STATE_HOME:-$HOME/.local/state}/tapedeck"
mkdir -p "$LOGDIR"
echo "---- $(date) starting tunnel ----" >> "$LOGDIR/tunnel.log"

PYTHON="python3"
[ -x .venv/bin/python ] && PYTHON=.venv/bin/python

exec "$PYTHON" tunnel.py --wait 300 >> "$LOGDIR/tunnel.log" 2>&1
