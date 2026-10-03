#!/bin/bash
# ClariFin OS - canonical startup entry point for Unix/Linux/macOS.
# ==========================================
#
# This script is a thin wrapper. It owns no logic of its own: every command is
# delegated to scripts/launch.sh, which is the single canonical operational
# entry point for the repository. Windows users get the same behaviour through
# start.bat, which delegates to the same launcher.
#
# Usage:
#   ./start.sh                    Start the full application (canonical start)
#   ./start.sh stop               Canonical shutdown
#   ./start.sh console            Platform Console only (independent)
#   ./start.sh status | health | logs | check-env | restart
#   ./start.sh platform-status    Platform API readiness only, in the four
#                                 states the console renders
#   ./start.sh help               Full command list
#
# Startup performs, in order: environment validation -> backend -> frontend ->
# readiness verification -> URL printout. Shutdown is idempotent.
#
# The startup banner reports the financial application's readiness and the
# Platform API's readiness separately: the first is cheap (GET /ready measured
# 5-24 ms), the second is a snapshot build (13.8-37.8 s cold). Only the first
# gates startup.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Canonical launcher lives under scripts/. It is the single source of truth for
# start / stop / status / console / health.
LAUNCHER="$SCRIPT_DIR/scripts/launch.sh"
if [ ! -f "$LAUNCHER" ]; then
    echo "ERROR: scripts/launch.sh not found at $LAUNCHER" >&2
    echo "       The repository is incomplete. Run:" >&2
    echo "         bash scripts/bootstrap.sh" >&2
    exit 1
fi

# Default to `start` only when no argument was supplied. Arguments are forwarded
# verbatim so that `./start.sh stop` stops the application instead of starting
# it a second time.
if [ "$#" -eq 0 ]; then
    exec bash "$LAUNCHER" start
fi

exec bash "$LAUNCHER" "$@"