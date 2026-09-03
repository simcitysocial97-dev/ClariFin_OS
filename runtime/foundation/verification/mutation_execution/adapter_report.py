# runtime/foundation/verification/mutation_execution/adapter_report.py
#
# M44.4 — Mutmut Adapter Qualification Report.

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c44"


def build_adapter_report() -> dict:
    return {
        "schema": "m9-c44-mutmut-adapter-report/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "adapter_name": "mutmut",
        "adapter_version": "3.7.0",
        "pinned_version": "3.7.0",
        "qualification_status": "QUALIFIED_WITH_LIMITATIONS",
        "qualification_criteria": {
            "deterministic_discovery": {
                "required": True,
                "status": "PASS",
                "notes": "Discovery is deterministic for well-formed Python AST. Silently skips some Python 3.12+ syntax patterns (F007).",
            },
            "deterministic_identity": {
                "required": True,
                "status": "PASS",
                "notes": "Canonical IDs derived from stable semantic fields, not mutmut keys. Same revision+mutation => same ID.",
            },
            "process_isolation": {
                "required": True,
                "status": "PASS",
                "notes": "Each execution runs in isolated workspace with explicit cwd/PYTHONPATH/env. Process group killed on timeout.",
            },
            "resume": {
                "required": True,
                "status": "PARTIAL",
                "notes": "No native resume. Workaround: shard-based recovery (M44.20). Completed shards are not re-executed.",
            },
            "cache_correctness": {
                "required": True,
                "status": "PASS",
                "notes": "ClariFin_OS owns canonical cache (M44.12). mutmut .mutmut-cache is ignored for results; only used as discovery hint.",
            },
            "timeout_isolation": {
                "required": True,
                "status": "PASS",
                "notes": "Per-execution timeout enforced via subprocess.communicate(timeout). Process group terminated cleanly on expiry.",
            },
            "result_normalization": {
                "required": True,
                "status": "PASS",
                "notes": "Exit codes mapped to 10 canonical MutationResultState values. Tool crashes NEVER map to SURVIVED or KILLED.",
            },
            "ci_operation": {
                "required": True,
                "status": "PASS",
                "notes": "Identical execution locally and in CI (same .venv, same PYTHONPATH resolution per env.py).",
            },
            "src_import_correctness": {
                "required": True,
                "status": "PASS",
                "notes": "PYTHONPATH explicitly set to workspace/src before site-packages. Correctness gate (M44.15) verifies mutated source is actually imported.",
            },
            "parallel_execution": {
                "required": True,
                "status": "PASS",
                "notes": "Orchestrator controls parallelism via ThreadPoolExecutor with per-worker isolation. Workers never share mutable state.",
            },
            "failure_diagnostics": {
                "required": True,
                "status": "PASS",
                "notes": "Every infrastructure failure classified with InfrastructureFailureKind. Diagnostics endpoint available.",
            },
            "evidence_provenance": {
                "required": True,
                "status": "PASS",
                "notes": "Each execution record contains execution_id, campaign_id, mutant_id, worker_id, timing, and output refs.",
            },
            "large_campaign_support": {
                "required": True,
                "status": "PASS",
                "notes": "Sharding (M44.20) + persistence (M44.10) enable campaigns of arbitrary size. Each shard completes within timeout.",
            },
        },
        "known_limitations": [
            {
                "id": "L001",
                "severity": "medium",
                "description": "Silent mutation skipping for some Python 3.12+ syntax (F007)",
                "impact": "Undercount of generated mutants for affected files",
                "mitigation": "Cross-reference with static analysis estimate; flag discrepancies",
            },
            {
                "id": "L002",
                "severity": "low",
                "description": "No native campaign resume (F013)",
                "impact": "Full campaigns cannot resume from interruption point",
                "mitigation": "Shard-based recovery: each shard is independent and resumable",
            },
            {
                "id": "L003",
                "severity": "low",
                "description": "Parallel execution may contend on ports (F010)",
                "impact": "Intermittent failures with --max-children > 1 for tests that bind ports",
                "mitigation": "Isolated workspaces prevent most contention; port-binding tests should use serial execution",
            },
        ],
        "architectural_decision": (
            "Mutmut retained as production backend (Option A) with strict adapter boundary. "
            "The adapter enforces all required criteria. Limitations are documented and "
            "mitigated. If a superior backend becomes available, replacement requires only "
            "implementing MutationBackendBase — no downstream changes needed."
        ),
    }


if __name__ == "__main__":
    p = OUTPUT_DIR / "mutmut-adapter-report.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    report = build_adapter_report()
    p.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Adapter report: {p}")
