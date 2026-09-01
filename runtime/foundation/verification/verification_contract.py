# runtime/foundation/verification/verification_contract.py
#
# M9-C52.4 — Unified Change→Capability→Plan Contract.
#
# Composes the already-certified pieces into ONE canonical executable contract:
#
#     repository state + changed files
#         -> change detection (C50 change_surface)
#         -> blast radius (C50 blast_radius)
#         -> capability resolution (C51 capability_discovery)
#         -> evidence planning (C42.27 evidence_planner)
#         -> canonical machine-readable VerificationDecision
#
# NO duplicate planner. NO duplicate blast-radius engine. NO second capability
# resolver. Uses existing implementations only.

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.foundation.verification.blast_radius import compute_blast_radius
from runtime.foundation.verification.capability_discovery import (
    CapabilityDiscoveryService,
)
from runtime.foundation.verification.change_surface import (
    discover_change_surfaces,
)
from runtime.foundation.verification.evidence_planner import (
    default_planner,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@dataclass(frozen=True, slots=True)
class VerificationDecision:
    """Canonical machine-readable output of the unified control plane.

    Given a repository state and changed files, this is the single source of
    truth for: what capabilities are affected, what verification is required,
    what evidence can be reused, what must execute, and why.
    """

    schema: str = "m9-c52-verification-decision/v1"
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    repository_sha: str = ""
    working_tree_dirty: bool = False

    # Input
    changed_files: tuple[str, ...] = ()

    # Change detection
    change_surface: dict[str, Any] = field(default_factory=dict)

    # Blast radius (C50 canonical)
    blast_radius_contract: dict[str, Any] = field(default_factory=dict)

    # Capability resolution (C51 certified)
    capability_resolutions: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Evidence planning (C42.27 certified)
    evidence_plan: dict[str, Any] = field(default_factory=dict)

    # Selected execution tasks
    selected_tasks: list[dict[str, Any]] = field(default_factory=list)

    # Excluded tasks with reasons
    excluded_tasks: list[dict[str, Any]] = field(default_factory=list)

    # Reusable evidence
    reusable_evidence: list[dict[str, Any]] = field(default_factory=list)

    # Invalidated evidence
    invalidated_evidence: list[dict[str, Any]] = field(default_factory=list)

    # Certification implications
    certification_implications: dict[str, Any] = field(default_factory=dict)

    # Reasons / audit trail
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class VerificationContractEngine:
    """Single entry point for the unified change→capability→plan contract.

    Does not duplicate any existing logic; composes certified components.
    """

    def __init__(self) -> None:
        self._capability_resolver = CapabilityDiscoveryService()
        self._evidence_planner = default_planner()

    def _get_repo_sha(self) -> str:
        import subprocess

        try:
            return subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        except Exception:
            return "unknown"

    def _is_working_tree_dirty(self) -> bool:
        import subprocess

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            return bool(result.stdout.strip())
        except Exception:
            return False

    def decide(
        self,
        changed_files: list[str] | None = None,
    ) -> VerificationDecision:
        """Execute the full unified contract.

        Args:
            changed_files: Explicit list of changed files. If None, derives
                from git working tree (C50 change_surface).

        Returns:
            VerificationDecision with complete audit trail.
        """
        # 1. Change detection
        if changed_files is None:
            surface = discover_change_surfaces()
            changed_files = list(surface.changed_files)
            change_surface_dict = surface.to_dict()
        else:
            surface = discover_change_surfaces(explicit_files=changed_files)
            change_surface_dict = surface.to_dict()

        repo_sha = self._get_repo_sha()
        dirty = self._is_working_tree_dirty()

        # 2. Blast radius (C50 canonical - single source of truth for impact)
        blast_contract = compute_blast_radius(explicit_files=changed_files)
        blast_dict = blast_contract.to_dict()

        # 3. Capability resolution (C51 certified resolver)
        # Resolve each changed file to its canonical capability path
        capability_resolutions = {}
        if changed_files:
            # Use blast-radius's capability impacts for provenance
            for cap_impact in blast_contract.capability_impacts:
                cap_id = cap_impact.capability_id
                if cap_id not in capability_resolutions:
                    # Run the C51 resolver for this capability
                    problem_type = "changed_file"
                    res = self._capability_resolver.discover(
                        problem_type=problem_type,
                        changed_files=changed_files,
                    )
                    capability_resolutions[cap_id] = res.to_dict()

        # 4. Evidence planning (C42.27 certified planner)
        evidence_plan = self._evidence_planner.plan(changed_files)
        evidence_plan_dict = evidence_plan.to_dict()

        # 5. Extract selected/excluded/reusable/invalidated from evidence plan
        selected_tasks = []
        excluded_tasks = []
        reusable_evidence = []
        invalidated_evidence = []

        for task in evidence_plan.selected_tasks:
            task_dict = task.to_dict()
            selected_tasks.append(task_dict)

        for task in evidence_plan.excluded_tasks:
            task_dict = task.to_dict()
            excluded_tasks.append(task_dict)

        for reuse in evidence_plan.reuses:
            reusable_evidence.append(reuse.to_dict())

        for inv in evidence_plan.drift_blockers:
            invalidated_evidence.append({"drift_blocker": inv})

        for gap in evidence_plan.certification_gaps:
            invalidated_evidence.append({"certification_gap": gap})

        # 6. Certification implications
        cert_implications = {
            "gated_by": [],
            "blocked_by": [],
            "requires_human_authorization": any(
                "human" in str(t.get("evidence_reuse", "")).lower()
                for t in selected_tasks
            ),
        }
        for cap_id in capability_resolutions:
            cert_implications["gated_by"].append(cap_id)

        # 7. Audit trail / reasons
        reasons = [
            f"Change surface: {len(changed_files)} files analyzed",
            f"Blast radius: {len(blast_contract.directly_affected_capabilities)} direct, {len(blast_contract.transitively_affected_capabilities)} transitive capabilities",
            f"Evidence plan: {len(selected_tasks)} selected, {len(reusable_evidence)} reused, {len(invalidated_evidence)} invalidated",
            f"Fail-closed: {blast_contract.is_fail_closed}",
        ]
        reasons.extend(blast_contract.fail_closed_reasons)

        return VerificationDecision(
            repository_sha=repo_sha,
            working_tree_dirty=dirty,
            changed_files=tuple(changed_files),
            change_surface=change_surface_dict,
            blast_radius_contract=blast_dict,
            capability_resolutions=capability_resolutions,
            evidence_plan=evidence_plan_dict,
            selected_tasks=selected_tasks,
            excluded_tasks=excluded_tasks,
            reusable_evidence=reusable_evidence,
            invalidated_evidence=invalidated_evidence,
            certification_implications=cert_implications,
            reasons=reasons,
        )


def main() -> int:
    """CLI: verify.py verification-contract [--files FILE...] [--json] [--out PATH]"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="verify.py verification-contract", add_help=False
    )
    parser.add_argument(
        "--files",
        nargs="*",
        help="Explicit list of changed files (default: git working tree)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output machine-readable JSON"
    )
    parser.add_argument("--out", help="Write JSON to file")
    args = parser.parse_args(sys.argv[2:])

    engine = VerificationContractEngine()
    decision = engine.decide(changed_files=args.files if args.files else None)

    output = json.dumps(decision.to_dict(), indent=2, default=str)

    if args.out:
        Path(args.out).write_text(output)
        print(f"Written to {args.out}")
    if args.json or args.out:
        print(output)
    else:
        # Human-readable summary
        print(
            f"Repository: {decision.repository_sha[:12]} (dirty={decision.working_tree_dirty})"
        )
        print(f"Changed files: {len(decision.changed_files)}")
        print(f"Selected tasks: {len(decision.selected_tasks)}")
        print(f"Reused evidence: {len(decision.reusable_evidence)}")
        print(f"Invalidated evidence: {len(decision.invalidated_evidence)}")
        print(
            f"Fail-closed: {decision.blast_radius_contract.get('is_fail_closed', False)}"
        )
        for r in decision.reasons:
            print(f"  - {r}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
