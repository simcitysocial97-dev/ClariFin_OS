#!/usr/bin/env bash
# Run one bounded mutation shard and emit a single result line.
# Usage: .venv/bin/python runtime/generated/m9-c71-mutation-trust/run-shard.sh <shard-id>
set -uo pipefail
# Run from the repository root regardless of the caller's working directory.
# This previously `cd`-ed into a hardcoded developer-local absolute path, so the
# shard could only ever run inside one person's checkout.
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${script_dir}/../../.."
shard="$1"
echo "=== SHARD ${shard} START $(date -Is) ==="
timeout 3600 .venv/bin/python -m runtime.verify mutation --shard "${shard}" --max-runtime 3000 2>&1 \
  | grep -E "Killed|Survived|Generated|No tests|Timeout|Suspicious|INFRASTRUCTURE" \
  | head -8
echo "=== SHARD ${shard} DONE $(date -Is) ==="
