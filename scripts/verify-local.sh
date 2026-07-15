#!/usr/bin/env bash
set -uo pipefail
# This script is automatically run by Cline after every change. All failures must be fixed before commit.
# Delegates to Validation Orchestrator for unified validation pipeline.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
START=$(date +%s)

echo "=== Running verify-local (via Validation Orchestrator) ==="

# Run full validation via orchestrator
cd "$BACKEND_DIR"
./venv/bin/python3 ../backend/tools/validation_orchestrator.py --full

echo "Completed in $(( $(date +%s)-START )) seconds"
