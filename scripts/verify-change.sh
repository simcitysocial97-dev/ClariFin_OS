#!/usr/bin/env bash
set -euo pipefail
# Change Confidence Pipeline - Staged verification wrapper
# REUSES existing validation tooling (does NOT duplicate FVF or replace VOF)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"

# Usage: ./scripts/verify-change.sh [level]
# Level: A (current files), B (affected capability), C (full)
LEVEL="${1:-}"

echo "=== Change Confidence Pipeline ==="

# Determine verification level
if [ -z "$LEVEL" ]; then
    # Auto-detect based on changed files
    CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null || echo "")
    
    # Level A: Only docs/config changes
    if echo "$CHANGED_FILES" | grep -qE '\.(md|txt|rst|json|yaml|toml)$'; then
        # Check if any code files changed
        if ! echo "$CHANGED_FILES" | grep -qE '\.(py|ts|tsx|js|jsx)$'; then
            LEVEL="A"
        fi
    fi
    
    # Level C: Schema or layer boundary changes
    if echo "$CHANGED_FILES" | grep -qE '(migration|schema|\.sql)$'; then
        LEVEL="C"
    elif echo "$CHANGED_FILES" | grep -qE 'src/(routers|services|engines/repositories)/'; then
        LEVEL="C"
    elif echo "$CHANGED_FILES" | grep -qE 'src/engines/(cashflow|loan|credit_card|behaviour)'; then
        LEVEL="C"
    fi
    
    # Default: Level B for code changes
    [ -z "$LEVEL" ] && LEVEL="B"
fi

# Level A: Current Files (docs, config only)
if [ "$LEVEL" = "A" ]; then
    echo "Level A: Verifying current files only (docs/config changes)"
    echo "Running fast verification (ruff + mypy)..."
    "$ROOT_DIR/scripts/verify-fast.sh"
    exit 0
fi

# Level B: Affected Capability
if [ "$LEVEL" = "B" ]; then
    echo "Level B: Selective verification (affected capability)"
    echo "Running selective verification..."
    VERIFY_MODE=selective "$ROOT_DIR/scripts/verify-local.sh"
    exit 0
fi

# Level C: Full Validation
if [ "$LEVEL" = "C" ]; then
    echo "Level C: Full validation (schema/layer changes)"
    echo "Running full verification pipeline..."
    "$ROOT_DIR/scripts/verify-local.sh"
    exit 0
fi

echo "Invalid level: $LEVEL (use A, B, or C)"
exit 1