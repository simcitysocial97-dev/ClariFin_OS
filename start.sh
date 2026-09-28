#!/bin/bash
# ClariFin OS - Personal Finance MVP v1.0.0
# One-Click Launch Script for Unix/Linux/Mac
# ==========================================
#
# M9-C57 migration: this script delegates to the canonical launcher
# (scripts/launch.sh) rather than duplicating business logic. The
# single source of truth for start/backend/frontend is launch.sh.

set -e

echo "═══════════════════════════════════════════════════════════"
echo "  ClariFin OS - Personal Finance MVP v1.0.0"
echo "═══════════════════════════════════════════════════════════"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Canonical launcher lives under scripts/.
LAUNCHER="$SCRIPT_DIR/scripts/launch.sh"
if [ ! -x "$LAUNCHER" ]; then
    echo "ERROR: scripts/launch.sh not found. Run bootstrap first:"
    echo "       bash scripts/bootstrap.sh"
    exit 1
fi

exec bash "$LAUNCHER" start
