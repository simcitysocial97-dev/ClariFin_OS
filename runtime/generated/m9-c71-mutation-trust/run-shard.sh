#!/usr/bin/env bash
# Run one bounded mutation shard and emit a single result line.
# Usage: .venv/bin/python runtime/generated/m9-c71-mutation-trust/run-shard.sh <shard-id>
set -uo pipefail
cd /home/vasantha/AI-Projects/ClariFin_OS
shard="$1"
echo "=== SHARD ${shard} START $(date -Is) ==="
timeout 3600 .venv/bin/python -m runtime.verify mutation --shard "${shard}" --max-runtime 3000 2>&1 \
  | grep -E "Killed|Survived|Generated|No tests|Timeout|Suspicious|INFRASTRUCTURE" \
  | head -8
echo "=== SHARD ${shard} DONE $(date -Is) ==="
