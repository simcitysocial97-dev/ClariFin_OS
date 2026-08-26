#!/usr/bin/env python3
"""
M9-C42.27 — M27.1 Authoritative Baseline

Freeze the existing verification architecture state before any
architectural changes. Produces a baseline artifact containing
fingerprints/hashes of every frozen artifact so future changes can
detect drift against the C42.26 starting point.

Deterministic. No subprocess. Pure hashing.

Usage:
    .venv/bin/python runtime/generated/m9-c42.27/m27_1_baseline.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUTPUT_PATH = REPO_ROOT / "runtime" / "generated" / "m9-c42.27" / "m9-c42.27-baseline.json"


# Frozen artifacts that constitute the pre-C42.27 verification
# architecture. Each entry is the repo-relative path the baseline
# fingerprint was computed against. The mapping is *enumerated* —
# never inferred — so a frozen file is always identifiable.
FROZEN_ARCHITECTURE: list[tuple[str, str]] = [
    # M9-C42.26 certification artifacts (the certified starting state)
    ("certification", "runtime/generated/m9-c42.26/m9-c42.26-certification.json"),
    ("certification", "runtime/generated/m9-c42.26/m9-c42.26-baseline.json"),
    ("certification", "runtime/generated/m9-c42.26/m9-c42.26-population-expansion.json"),
    ("certification", "runtime/generated/m9-c42.26/m9-c42.26-component-matrix.json"),
    ("certification", "runtime/generated/m9-c42.26/m9-c42.26-mathematical-reconciliation.json"),
    ("certification", "runtime/generated/m9-c42.26/m9-c42.26-intelligence-certification.json"),
    ("certification", "runtime/generated/m9-c42.26/m9-c42.26-intelligence-survivor-intelligence.json"),
    ("certification", "runtime/generated/m9-c42.26/m9-c42.26-mutation-score-interpretation.json"),
    ("certification", "runtime/generated/m9-c42.26/m9-c42.26-cross-dimension-reconciliation.json"),
    ("certification", "runtime/generated/m9-c42.26/m9-c42.26-cadence-and-architecture.json"),
    # 14-component population ledger
    ("population_ledger", "runtime/generated/m9-c42.26/m9-c42.26-component-matrix.json"),
    # Mutation contract + runner + inventory (the certified tooling)
    ("mutation_contract", "runtime/foundation/verification/mutation_contract.py"),
    ("mutation_runner", "runtime/foundation/verification/mutation_runner.py"),
    ("mutation_inventory", "runtime/foundation/verification/mutation_inventory.py"),
    # Capability registry
    ("registry", "runtime/foundation/verification/registry/registry.py"),
    ("registry_init", "runtime/foundation/verification/registry/__init__.py"),
    # Verification config
    ("verification_config", "runtime/foundation/verification/verification.yaml"),
    # Planner (existing)
    ("planner", "runtime/foundation/verification/planner/planner.py"),
    ("planner_models", "runtime/foundation/verification/planner/plan_models.py"),
    ("planner_impact", "runtime/foundation/verification/planner/impact_rules.py"),
    # Orchestrator
    ("orchestrator", "runtime/foundation/verification/orchestrator.py"),
    # Runtime entry
    ("verify_runtime", "runtime/verify.py"),
    # Models / evidence contract
    ("verification_models", "runtime/foundation/verification/models/model.py"),
    ("verification_scope", "runtime/foundation/verification/models/scope.py"),
    ("verification_models_init", "runtime/foundation/verification/models/__init__.py"),
    ("evidence_contract", "runtime/foundation/verification/evidence_contract.py"),
    # Progress
    ("progress", "progress.md"),
]


def _hash_file(path: Path) -> dict:
    if not path.exists():
        return {
            "exists": False,
            "sha256": None,
            "bytes": 0,
        }
    raw = path.read_bytes()
    return {
        "exists": True,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def _git_head() -> str | None:
    head = REPO_ROOT / ".git" / "HEAD"
    if not head.exists():
        return None
    ref = head.read_text().strip()
    if ref.startswith("ref:"):
        ref_path = REPO_ROOT / ".git" / ref.split(":", 1)[1].strip()
        if ref_path.exists():
            return ref_path.read_text().strip()
    return ref


def main() -> int:
    git_head = _git_head()
    artifacts: list[dict] = []
    missing: list[str] = []

    for kind, rel in FROZEN_ARCHITECTURE:
        full = REPO_ROOT / rel
        info = _hash_file(full)
        artifacts.append(
            {
                "kind": kind,
                "path": rel,
                **info,
            }
        )
        if not info["exists"]:
            missing.append(rel)

    # Aggregate fingerprint (order-stable: sorted by path).
    ordered = sorted(a["sha256"] or "" for a in artifacts)
    aggregate = hashlib.sha256("\n".join(ordered).encode()).hexdigest()

    payload = {
        "title": "M9-C42.27 — Authoritative Baseline (M27.1)",
        "milestone": "M9-C42.27",
        "phase": "M27.1 — Freeze and Audit the Existing Verification Architecture",
        "generated_at": datetime.now(UTC).isoformat(),
        "git_head": git_head,
        "freeze_semantics": (
            "All paths listed are frozen. C42.27 must not change the behavior "
            "or contents of these artifacts. Any mutation, deletion, or new "
            "dependency on these paths is a C42.27 violation."
        ),
        "frozen_artifact_count": len(artifacts),
        "missing_artifacts": missing,
        "aggregate_sha256": aggregate,
        "artifacts": artifacts,
        "certification_label": (
            "M9-C42.26 — 14-COMPONENT POPULATION RECONCILED — "
            "NO FULL RERUN REQUIRED"
        ),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))

    print(f"Baseline written: {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    print(f"Frozen artifacts: {len(artifacts)}")
    print(f"Missing artifacts: {len(missing)}")
    print(f"Aggregate SHA-256: {aggregate[:16]}…")
    if missing:
        print("MISSING:")
        for m in missing:
            print(f"  - {m}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
