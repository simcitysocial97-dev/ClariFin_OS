# runtime/foundation/verification/mutation_execution/backend_contract_report.py
#
# M9-C44.3 — Mutation Backend Interface Report.
#
# Produces: runtime/generated/m9-c44/mutation-backend-contract.json

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c44"


def build_backend_contract_report() -> dict:
    return {
        "schema": "m9-c44-mutation-backend-contract/v1",
        "generated_at": "2026-09-03T00:00:00Z",
        "interface_version": "v1",
        "description": (
            "Strict backend interface that every mutation tool adapter MUST implement. "
            "The rest of ClariFin_OS calls ONLY this interface; it never invokes a "
            "specific tool directly."
        ),
        "required_methods": {
            "discover": {
                "signature": "discover(scope: str, candidates: list[MutationCandidate]) -> list[MutationCandidate]",
                "description": "Discover mutations within scope. Returns enhanced candidates with canonical IDs.",
                "guarantees": [
                    "Returns candidates with deterministic canonical_mutant_id",
                    "Does not mutate source files",
                    "Idempotent for same input",
                ],
            },
            "generate": {
                "signature": "generate(campaign: MutationCampaign, candidates: list[MutationCandidate], workspace: Path) -> Path",
                "description": "Apply mutations to workspace and return path to generated state.",
                "guarantees": [
                    "Mutations applied only within workspace, never in-place in repo",
                    "Returns path to mutants directory",
                    "Workspace is isolated from canonical repository",
                ],
            },
            "execute": {
                "signature": "execute(candidate, test_selection, workspace, environment, timeout, worker_id, campaign_id) -> MutationExecution",
                "description": "Execute one mutant against selected tests in isolated workspace.",
                "guarantees": [
                    "Process isolation: each execution in its own process group",
                    "Timeout enforced: returns TIMEOUT state if exceeded",
                    "Environment isolated: PYTHONPATH, working dir, temp files controlled",
                    "Results normalized to canonical MutationResultState",
                    "Never misclassifies tool crash as SURVIVED or KILLED",
                ],
            },
            "collect": {
                "signature": "collect(campaign: MutationCampaign, workspace: Path) -> MutationResult",
                "description": "Aggregate all execution records into canonical MutationResult.",
                "guarantees": [
                    "Produces arithmetic-complete result (reconcile() == True)",
                    "All candidates accounted for",
                    "No backend-specific states leak through",
                ],
            },
            "cancel": {
                "signature": "cancel(campaign: MutationCampaign, workspace: Path) -> None",
                "description": "Gracefully cancel an in-progress campaign.",
                "guarantees": [
                    "Running processes terminated",
                    "Pending candidates marked CANCELLED",
                    "Workspace left in recoverable state",
                ],
            },
            "resume": {
                "signature": "resume(campaign_id, workspace, last_checkpoint) -> MutationCampaign",
                "description": "Resume a paused/interrupted campaign from last checkpoint.",
                "guarantees": [
                    "Completed mutants are NOT re-executed",
                    "Pending mutants are picked up from checkpoint",
                    "Evidence integrity preserved across resume",
                ],
            },
            "cleanup": {
                "signature": "cleanup(campaign: MutationCampaign, workspace: Path) -> None",
                "description": "Clean up temporary workspace artifacts (keep evidence).",
                "guarantees": [
                    "Evidence directory preserved",
                    "Temporary mutation sources removed",
                    "No cross-contamination with other campaigns",
                ],
            },
            "diagnostics": {
                "signature": "diagnostics(workspace: Path) -> dict",
                "description": "Return diagnostic information about current workspace state.",
            },
        },
        "optional_hooks": {
            "verify_tool_version": "Check backend meets minimum version requirement",
            "verify_configuration": "Validate workspace configuration before execution",
            "verify_environment": "Validate runtime environment before execution",
        },
        "current_adapters": [
            {
                "name": "mutmut",
                "version": "3.7.0",
                "status": "active",
                "qualified": True,
                "limitations": [
                    "No native resume support (workaround: shard-based recovery)",
                    "Cache depends on .mutmut-cache (superseded by M44.12 canonical cache)",
                    "Discovery may silently skip some Python 3.12+ syntax patterns",
                ],
            }
        ],
        "qualification_criteria": {
            "deterministic_discovery": "required",
            "deterministic_identity": "required",
            "process_isolation": "required",
            "resume": "required",
            "cache_correctness": "required",
            "timeout_isolation": "required",
            "result_normalization": "required",
            "ci_operation": "required",
            "src_import_correctness": "required",
            "parallel_execution": "required",
            "failure_diagnostics": "required",
            "evidence_provenance": "required",
            "large_campaign_support": "required",
        },
    }


def write_report(output_dir: Path | None = None) -> Path:
    if output_dir is None:
        output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_backend_contract_report()
    path = output_dir / "mutation-backend-contract.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    return path


if __name__ == "__main__":
    p = write_report()
    print(f"Backend contract report: {p}")
