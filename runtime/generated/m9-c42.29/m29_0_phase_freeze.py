"""
M9-C42.29–31 — Phase Baseline Freeze (M29.0).

Freezes the certified M9-C42.28 state as the authoritative starting
point for the combined C42.29 (CI Evidence Fingerprinting &
Correlation), C42.30 (Diagnostic & Forensic Agent Foundation) and
C42.31 (Evidence-Driven Strengthening Loop) phase.

The freeze records:
  * the repository SHA,
  * fingerprints for every architectural surface the phase must
    preserve (verification graph, planner, evidence reuse layer,
    execution layer, mutation contract, population snapshots,
    evidence schemas, CLI surface, CI workflow inventory),
  * the C42.27/C42.28 certified artifacts.

C42.29–31 must not change the behaviour or contents of these frozen
surfaces in a way that breaks their certified contracts. Any drift is
detectable by re-running this freeze and comparing fingerprints.

Run with:
    .venv/bin/python runtime/generated/m9-c42.29/m29_0_phase_freeze.py
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

assert (REPO_ROOT / "backend").is_dir(), (
    f"REPO_ROOT sanity check failed: {REPO_ROOT}"
)

OUT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c42.29"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _sha256_file(p: Path) -> str:
    if not p.exists():
        return "MISSING"
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _dir_fingerprint(d: Path) -> str:
    if not d.exists():
        return "MISSING"
    h = hashlib.sha256()
    for f in sorted(d.rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts:
            h.update(str(f.relative_to(d)).encode())
            try:
                h.update(f.read_bytes())
            except Exception:
                h.update(b"<unreadable>")
    return h.hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout.strip()
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Frozen surfaces — the architecture C42.29–31 must preserve.
# ---------------------------------------------------------------------------

FROZEN_MODULES: dict[str, str] = {
    # C42.27 verification graph + planner + evidence layer
    "graph_model": "runtime/foundation/verification/graph_model.py",
    "evidence_reuse": "runtime/foundation/verification/evidence_reuse.py",
    "evidence_planner": "runtime/foundation/verification/evidence_planner.py",
    "correlation": "runtime/foundation/verification/correlation.py",
    # C42.28 execution layer
    "executor_pipeline": "runtime/foundation/verification/executor_pipeline.py",
    "mutation_runner": "runtime/foundation/verification/mutation_runner.py",
    "mutation_contract": "runtime/foundation/verification/mutation_contract.py",
    "mutation_inventory": "runtime/foundation/verification/mutation_inventory.py",
    # Evidence schemas (VEA-5 lineage)
    "evidence_contract": "runtime/foundation/verification/evidence_contract.py",
    "reconciliation": "runtime/foundation/verification/reconciliation.py",
}

FROZEN_ARTIFACTS: dict[str, str] = {
    "c42.27-certification": "runtime/generated/m9-c42.27/m9-c42.27-certification.json",
    "c42.27-baseline": "runtime/generated/m9-c42.27/m9-c42.27-baseline.json",
    "c42.27-graph-inventory": "runtime/generated/m9-c42.27/m9-c42.27-graph-inventory.json",
    "c42.27-scenarios": "runtime/generated/m9-c42.27/m9-c42.27-scenarios.json",
    "c42.28-baseline": "runtime/generated/m9-c42.28/m9-c42.28-baseline.json",
    "c42.28-certification": "runtime/generated/m9-c42.28/m9-c42.28-certification.json",
    "c42.28-scenarios": "runtime/generated/m9-c42.28/m9-c42.28-scenarios.json",
    "pop-12-c42.24-B": "runtime/generated/m9-c42.27/snapshots/pop-12-c42.24-B.json",
    "pop-txn-c42.25": "runtime/generated/m9-c42.27/snapshots/pop-txn-c42.25.json",
    "pop-14-c42.26": "runtime/generated/m9-c42.27/snapshots/pop-14-c42.26.json",
    "c42.26-derived-aggregate": "runtime/generated/m9-c42.27/snapshots/c42.26-derived-aggregate.json",
}


def _workflow_inventory() -> dict:
    """Fingerprint every CI workflow file (the surface C42.29 binds)."""
    wf_dir = REPO_ROOT / ".github" / "workflows"
    out: dict[str, str] = {}
    if wf_dir.exists():
        for f in sorted(wf_dir.glob("*.yml")):
            out[f.name] = _sha256_file(f)
    return out


def _cli_surface_fingerprint() -> str:
    """Fingerprint the verify.py command dispatch surface (the literal
    command tokens, so cosmetic edits do not churn the fingerprint)."""
    vp = REPO_ROOT / "runtime" / "verify.py"
    if not vp.exists():
        return "MISSING"
    import re

    text = vp.read_text()
    commands = re.findall(r'command == "([a-z0-9_-]+)"', text)
    return hashlib.sha256(
        "\n".join(sorted(set(commands))).encode()
    ).hexdigest()


def main() -> int:
    sha = _git_sha()
    modules = {k: _sha256_file(REPO_ROOT / v) for k, v in FROZEN_MODULES.items()}
    artifacts = {k: _sha256_file(REPO_ROOT / v) for k, v in FROZEN_ARTIFACTS.items()}
    workflows = _workflow_inventory()

    graph_fp = _dir_fingerprint(REPO_ROOT / "runtime" / "foundation" / "verification")
    snapshots_fp = _dir_fingerprint(REPO_ROOT / "runtime" / "generated" / "m9-c42.27" / "snapshots")

    missing = [k for k, v in artifacts.items() if v == "MISSING"]
    if missing:
        print(f"FROZEN ARTIFACTS MISSING: {missing}", file=sys.stderr)
        return 1

    payload = {
        "schema": "m9-phase-baseline/v1",
        "phase": "M9-C42.29-31",
        "frozen_at": datetime.now(UTC).isoformat(),
        "repository_sha": sha,
        "prior_certification": {
            "c42.27": "CERTIFIED — Verification Graph + Planner Hardening (24/24 gates)",
            "c42.28": "CERTIFIED — Targeted Verification Execution (27/27 gates)",
        },
        "module_fingerprints": modules,
        "artifact_fingerprints": artifacts,
        "verification_layer_fingerprint": graph_fp,
        "population_snapshots_fingerprint": snapshots_fp,
        "cli_command_surface_fingerprint": _cli_surface_fingerprint(),
        "ci_workflow_inventory": workflows,
        "governing_constraints": [
            "Targeted measurement remains the default.",
            "A full campaign requires a formal trigger (C42.26 policy).",
            "A test addition alone never justifies a full campaign.",
            "Authoritative/targeted/reused/derived evidence must remain distinguishable.",
            "No production business logic may change merely to improve metrics.",
        ],
    }

    out = OUT_DIR / "m9-c42.29-31-baseline.json"
    out.write_text(json.dumps(payload, indent=2))
    print(f"Phase baseline written: {out.relative_to(REPO_ROOT)}")
    print(f"Repository SHA: {sha}")
    print(f"Modules fingerprinted: {len(modules)}")
    print(f"Artifacts fingerprinted: {len(artifacts)}")
    print(f"CI workflows inventoried: {len(workflows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
