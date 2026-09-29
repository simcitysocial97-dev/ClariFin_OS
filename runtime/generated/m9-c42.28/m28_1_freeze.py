"""
M9-C42.28 — M28.1 Freeze the C42.27 baseline for C42.28.

Mirrors M27.1 but freezes the *C42.27* artifacts as the authoritative
starting point for the C42.28 (Targeted Verification Execution) work.

All paths listed are frozen. C42.28 must not change the behavior or
contents of these artifacts. Any mutation, deletion, or new dependency
on these paths is a C42.28 violation.

The freeze also captures the *runtime surface* that C42.28 must obey:
the registry, the mutation contract, the verify.py entry point, and the
existing test-suite baseline. Fingerprints for each are recorded so any
silent drift is detectable.

Run with:
    .venv/bin/python runtime/generated/m9-c42.28/m28_1_freeze.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

assert (REPO_ROOT / "runtime").is_dir(), (
    f"REPO_ROOT sanity check failed: {REPO_ROOT}"
)

OUT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c42.28"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Frozen C42.27 artifact paths — the authoritative C42.28 starting point.
# ---------------------------------------------------------------------------
FROZEN_ARTIFACTS: list[dict] = [
    # C42.27 certification + graph + planner artifacts
    {
        "kind": "certification",
        "path": "runtime/generated/m9-c42.27/m9-c42.27-certification.json",
    },
    {
        "kind": "certification",
        "path": "runtime/generated/m9-c42.27/m9-c42.27-baseline.json",
    },
    {
        "kind": "graph_inventory",
        "path": "runtime/generated/m9-c42.27/m9-c42.27-graph-inventory.json",
    },
    {
        "kind": "derivation_manifest",
        "path": "runtime/generated/m9-c42.27/m9-c42.27-graph-derivation-manifest.json",
    },
    {
        "kind": "scenarios",
        "path": "runtime/generated/m9-c42.27/m9-c42.27-scenarios.json",
    },
    {
        "kind": "scenarios_module",
        "path": "runtime/generated/m9-c42.27/m27_11_scenarios.py",
    },
    # Population snapshots used by C42.27
    {
        "kind": "population_snapshot",
        "path": "runtime/generated/m9-c42.27/snapshots/pop-12-c42.24-B.json",
    },
    {
        "kind": "population_snapshot",
        "path": "runtime/generated/m9-c42.27/snapshots/pop-14-c42.26.json",
    },
    {
        "kind": "population_snapshot",
        "path": "runtime/generated/m9-c42.27/snapshots/pop-txn-c42.25.json",
    },
    {
        "kind": "population_snapshot",
        "path": "runtime/generated/m9-c42.27/snapshots/c42.26-derived-aggregate.json",
    },
    # Evidence reuse / invalidation rules / planner implementation
    {
        "kind": "evidence_reuse_module",
        "path": "runtime/foundation/verification/evidence_reuse.py",
    },
    {
        "kind": "evidence_planner_module",
        "path": "runtime/foundation/verification/evidence_planner.py",
    },
    {
        "kind": "correlation_module",
        "path": "runtime/foundation/verification/correlation.py",
    },
    {
        "kind": "graph_model_module",
        "path": "runtime/foundation/verification/graph_model.py",
    },
    # C42.27 test suite
    {
        "kind": "test_suite",
        "path": "runtime/tests/test_m9_c42_27.py",
    },
    # Correlation outputs from C42.27 scenarios
    {
        "kind": "correlation_output",
        "path": "runtime/generated/m9-c42.27/correlation-A_no_change.json",
    },
    {
        "kind": "correlation_output",
        "path": "runtime/generated/m9-c42.27/correlation-B_source_change.json",
    },
    {
        "kind": "correlation_output",
        "path": "runtime/generated/m9-c42.27/correlation-C_test_change.json",
    },
    {
        "kind": "correlation_output",
        "path": "runtime/generated/m9-c42.27/correlation-D_config_change.json",
    },
]


# ---------------------------------------------------------------------------
# Runtime surface C42.28 must obey (not frozen, but fingerprinted)
# ---------------------------------------------------------------------------
RUNTIME_SURFACE: list[dict] = [
    {
        "kind": "registry",
        "path": "runtime/foundation/verification/registry/registry.py",
    },
    {
        "kind": "registry_config",
        "path": "runtime/foundation/verification/verification.yaml",
    },
    {
        "kind": "mutation_contract",
        "path": "runtime/foundation/verification/mutation_contract.py",
    },
    {
        "kind": "mutation_runner",
        "path": "runtime/foundation/verification/mutation_runner.py",
    },
    {
        "kind": "executor",
        "path": "runtime/foundation/verification/executor.py",
    },
    {
        "kind": "verify_entrypoint",
        "path": "runtime/verify.py",
    },
    {
        "kind": "profiles",
        "path": "runtime/foundation/verification/profiles.py",
    },
    {
        "kind": "test_suite_mutation_infra",
        "path": "runtime/tests/test_mutation_infra.py",
    },
    {
        "kind": "test_suite_orchestrator",
        "path": "runtime/tests/test_orchestrator.py",
    },
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _record(entries: list[dict]) -> tuple[list[dict], list[str], int]:
    """Record existence + sha256 for every entry. Return (records, missing, total_bytes)."""
    records: list[dict] = []
    missing: list[str] = []
    total = 0
    for e in entries:
        p = REPO_ROOT / e["path"]
        if not p.exists():
            missing.append(e["path"])
            continue
        h = _sha256(p)
        size = p.stat().st_size
        total += size
        records.append(
            {
                "kind": e["kind"],
                "path": e["path"],
                "exists": True,
                "sha256": h,
                "bytes": size,
            }
        )
    return records, missing, total


def main() -> int:
    frozen_records, frozen_missing, frozen_bytes = _record(FROZEN_ARTIFACTS)
    runtime_records, runtime_missing, runtime_bytes = _record(RUNTIME_SURFACE)

    # Aggregate fingerprint over the frozen set (the formal C42.28 starting point)
    aggregate = hashlib.sha256(
        "\n".join(sorted(r["sha256"] for r in frozen_records)).encode()
    ).hexdigest()
    runtime_aggregate = hashlib.sha256(
        "\n".join(sorted(r["sha256"] for r in runtime_records)).encode()
    ).hexdigest()

    baseline = {
        "title": "M9-C42.28 \u2014 Authoritative Baseline (M28.1 freeze of C42.27)",
        "milestone": "M9-C42.28",
        "phase": "M28.1 \u2014 Freeze and Audit the C42.27 Verification Architecture",
        "generated_at": datetime.now(UTC).isoformat(),
        "git_head": _git_head(),
        "freeze_semantics": (
            "All paths under frozen_artifacts are frozen. C42.28 must not "
            "change the behavior or contents of these artifacts. Any "
            "mutation, deletion, or new dependency on these paths is a "
            "C42.28 violation. The runtime_surface entries are not "
            "frozen but are fingerprinted; any silent drift in those "
            "files invalidates this baseline."
        ),
        "frozen_artifact_count": len(frozen_records),
        "frozen_artifact_bytes": frozen_bytes,
        "frozen_aggregate_sha256": aggregate,
        "missing_frozen_artifacts": frozen_missing,
        "runtime_surface_count": len(runtime_records),
        "runtime_surface_bytes": runtime_bytes,
        "runtime_surface_aggregate_sha256": runtime_aggregate,
        "missing_runtime_surface": runtime_missing,
        "frozen_artifacts": frozen_records,
        "runtime_surface": runtime_records,
        "snapshot_of": {
            "c42_27_certification": "runtime/generated/m9-c42.27/m9-c42.27-certification.json",
            "c42_27_gates_passed": 24,
            "c42_27_scenarios_pass": "5/5",
            "c42_27_graph_inventory": {
                "sources": 411,
                "capabilities": 14,
                "test_surfaces": 57,
                "tasks": 13,
            },
            "c42_27_planner_dispositions": 9,
            "c42_27_invalidation_rules": 14,
        },
    }

    out = OUT_DIR / "m9-c42.28-baseline.json"
    out.write_text(json.dumps(baseline, indent=2))

    print(f"Baseline frozen: {out.relative_to(REPO_ROOT)}")
    print(
        f"Frozen artifacts: {len(frozen_records)} ({frozen_bytes:,} bytes); "
        f"missing: {len(frozen_missing)}"
    )
    print(
        f"Runtime surface:  {len(runtime_records)} ({runtime_bytes:,} bytes); "
        f"missing: {len(runtime_missing)}"
    )
    print(f"Aggregate SHA256: {aggregate}")
    return 0 if not frozen_missing and not runtime_missing else 1


if __name__ == "__main__":
    sys.exit(main())
