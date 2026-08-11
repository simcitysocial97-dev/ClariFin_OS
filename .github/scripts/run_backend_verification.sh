#!/usr/bin/env bash
# .github/scripts/run_backend_verification.sh
# Backend verification: contract, invariant and property-based tests.
# (Lint + unit are covered by the quick/fast-checks gate, so this focuses on
#  backend-specific test suites.)
#
# The four test directories are independent and run in parallel to reduce
# wall-clock time. Each directory uses its own isolated test database via
# the session-scoped pristine template.
#
# VEA-2 Phase 2 (M4): per-phase structured evidence, keyed by verification unit.
#
# Previously this script emitted only a single exit code and raw concatenated
# pytest output. A failure could not be attributed to a suite, and no JUnit XML
# was produced anywhere in the repository — so EvidenceAggregator's
# _collect_test_results(), which has always looked for junit.xml, never found
# anything (finding E-1).
#
# This script now emits, per suite phase: status, exit code, duration, log path
# and a JUnit XML file, plus a machine-readable JSON summary mirroring the
# frontend script's `frontend-verification/v1` shape.
#
# Unchanged by design:
#   * the exit-code contract — 0 when every phase passes, 1 when any fails;
#   * parallel execution of the four suites;
#   * the pytest commands themselves.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT/backend" || { echo "backend/ not found"; exit 1; }

EVIDENCE_DIR="${BACKEND_EVIDENCE_DIR:-$REPO_ROOT/runtime/generated/evidence/backend}"
mkdir -p "$EVIDENCE_DIR"

# Also emit JUnit to the path EvidenceAggregator's TestResultCollector probes,
# so E-1 is closed for the existing consumer as well as the new evidence dir.
LEGACY_JUNIT_DIR="$REPO_ROOT/backend/tests/generated"
mkdir -p "$LEGACY_JUNIT_DIR"

# The verification unit this execution belongs to, so evidence self-identifies.
# Empty (rather than a guessed value) when the caller does not supply one.
VERIFICATION_UNIT_ID="${VERIFICATION_UNIT_ID:-}"

fail=0
pids=()
names=()
outputs=()
codes=()
starts=()

# Phase name for a test directory. Explicit mapping, not derived by string
# munging, so a renamed directory fails loudly rather than silently producing a
# differently-named phase.
phase_name_for() {
  case "$1" in
    tests/contract)      echo "contract" ;;
    tests/invariants)    echo "invariants" ;;
    tests/properties)    echo "properties" ;;
    tests/unit/engines)  echo "unit-engines" ;;
    *)                   echo "unknown" ;;
  esac
}

for tdir in tests/contract tests/invariants tests/properties tests/unit/engines; do
  if [ -d "$tdir" ]; then
    name="$(phase_name_for "$tdir")"
    out="$EVIDENCE_DIR/${name}.log"
    junit="$EVIDENCE_DIR/${name}-junit.xml"
    echo ">> pytest $tdir (parallel, phase=$name)"
    starts+=("$(date +%s)")
    # --junitxml is additive: it changes no selection, no assertion, no exit code.
    python3 -m pytest "$tdir" -q --no-header --tb=short \
      --junitxml="$junit" > "$out" 2>&1 &
    pids+=($!)
    names+=("$name")
    outputs+=("$out")
  fi
done

# Collect exit codes positionally so each phase's status is known individually,
# rather than collapsing everything into one flag.
for i in "${!pids[@]}"; do
  if wait "${pids[$i]}"; then
    codes+=(0)
  else
    codes+=($?)
    fail=1
  fi
done

now=$(date +%s)
phase_json=""

for i in "${!names[@]}"; do
  name="${names[$i]}"
  out="${outputs[$i]}"
  code="${codes[$i]}"
  duration=$(( now - ${starts[$i]} ))
  junit="$EVIDENCE_DIR/${name}-junit.xml"

  echo "--- phase: $name ---"
  cat "$out"

  if [ "$code" -eq 0 ]; then
    status="pass"
  else
    status="fail"
  fi
  echo "<< $name: $status (exit=$code, ${duration}s)"

  if [ -n "$phase_json" ]; then
    phase_json="$phase_json,"
  fi
  phase_json="$phase_json{\"phase\":\"$name\",\"status\":\"$status\",\"exit_code\":$code,\"duration_seconds\":$duration,\"log\":\"$out\",\"junit\":\"$junit\"}"
done

# Merge per-suite JUnit into the single file the existing collector expects.
python3 - "$EVIDENCE_DIR" "$LEGACY_JUNIT_DIR/junit.xml" <<'PY' 2>/dev/null || true
import sys, glob, os
import xml.etree.ElementTree as ET

evidence_dir, target = sys.argv[1], sys.argv[2]
merged = ET.Element("testsuites")
found = False
for path in sorted(glob.glob(os.path.join(evidence_dir, "*-junit.xml"))):
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        continue
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    for suite in suites:
        merged.append(suite)
        found = True
if found:
    ET.ElementTree(merged).write(target, encoding="utf-8", xml_declaration=True)
PY

overall="pass"
if [ "$fail" -ne 0 ]; then
  overall="fail"
fi

cat > "$EVIDENCE_DIR/backend-verification.json" <<JSON
{
  "schema": "backend-verification/v1",
  "overall_status": "$overall",
  "unit_id": "$VERIFICATION_UNIT_ID",
  "phases": [$phase_json]
}
JSON

echo
echo "Phase summary: $EVIDENCE_DIR/backend-verification.json"
python3 - "$EVIDENCE_DIR/backend-verification.json" <<'PY' 2>/dev/null || true
import json, sys
with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)
for phase in data["phases"]:
    print(f"  {phase['phase']:<14} {phase['status']:<5} exit={phase['exit_code']} {phase['duration_seconds']}s")
PY

exit $fail
