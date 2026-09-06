# runtime/foundation/verification/mutation_execution/domain_model_report.py
#
# M9-C44.1 — Canonical Mutation Domain Model Report.
#
# Produces: runtime/generated/m9-c44/mutation-domain-model.json

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c44"


def build_domain_model_report() -> dict:
    return {
        "schema": "m9-c44-mutation-domain-model/v1",
        "generated_at": "2026-09-03T00:00:00Z",
        "mutation_result_states": {
            "KILLED": "targeted tests fail because of the mutation",
            "SURVIVED": "selected tests pass despite the mutation",
            "EQUIVALENT": "mutation cannot affect externally observable behaviour",
            "NO_TESTS": "no valid selected test exercised the mutation",
            "TIMEOUT": "execution exceeded defined timeout threshold",
            "EXECUTION_ERROR": "test process crashed or infrastructure failed",
            "INVALID_MUTANT": "mutated source identical to baseline or unapplyable",
            "NOT_EXECUTED": "scheduled but never attempted (campaign cancelled)",
            "CANCELLED": "explicitly cancelled by operator or campaign policy",
            "UNKNOWN": "truly unclassifiable after exhaustive diagnostics",
        },
        "timeout_kinds": {
            "test_timeout": "individual test execution exceeded timeout",
            "worker_timeout": "worker process exceeded timeout",
            "campaign_timeout": "total campaign duration exceeded limit",
            "infrastructure_timeout": "infrastructure component (e.g. container) timed out",
            "cleanup_timeout": "post-execution cleanup exceeded timeout",
        },
        "infrastructure_failure_kinds": {
            "none": "no failure",
            "subprocess_crash": "test subprocess crashed unexpectedly",
            "import_path_failure": "Python import path incorrect (edited src layout issue)",
            "cache_contamination": "stale cache produced incorrect results",
            "stale_cache_reuse": "cached result reused despite configuration change",
            "editable_install_failure": "editable install caused wrong source import",
            "temp_dir_failure": "temporary directory creation/access failed",
            "workspace_corruption": "mutation workspace became corrupted",
            "concurrency_collision": "parallel workers collided on shared state",
            "tool_crash": "mutation backend tool crashed",
            "timeout": "execution exceeded timeout",
            "signal_kill": "process killed by external signal",
            "unknown": "unclassified infrastructure failure",
        },
        "mutation_campaign_fields": [
            "campaign_id",
            "repository_revision",
            "environment_fingerprint",
            "mutation_backend",
            "backend_version",
            "scope",
            "test_selection",
            "configuration_fingerprint",
            "execution_policy",
            "creation_timestamp",
            "status",
            "resumed_from",
            "worker_count",
            "shard_index",
            "shard_total",
        ],
        "mutation_candidate_fields": [
            "canonical_mutant_id",
            "source_file",
            "source_hash",
            "function",
            "line",
            "column",
            "operator",
            "original_expression",
            "mutated_expression",
            "capability",
            "component",
            "risk",
            "selected_tests",
            "backend_metadata",
        ],
        "mutation_execution_fields": [
            "execution_id",
            "campaign_id",
            "mutant_id",
            "worker_id",
            "start_time",
            "end_time",
            "duration_seconds",
            "process_id",
            "exit_status",
            "test_result",
            "timeout",
            "infrastructure_failure",
            "mutation_result",
            "stdout_ref",
            "stderr_ref",
            "retry_count",
            "workspace_id",
            "verification_passed",
        ],
        "mutation_result_fields": [
            "campaign_id",
            "total_candidates",
            "killed",
            "survived",
            "equivalent",
            "no_tests",
            "timeout",
            "execution_error",
            "invalid_mutant",
            "not_executed",
            "cancelled",
            "unknown",
            "total_executions",
            "successful_executions",
            "infrastructure_failures",
            "timeouts",
            "retries_total",
        ],
        "canonical_identifier_formula": (
            "sha256(repository_revision | source_file | source_hash | function | "
            "line | operator | original_expression | mutated_expression)[:20]"
        ),
        "backend_interface_methods": [
            "discover(scope, candidates) -> candidates",
            "generate(campaign, candidates, workspace) -> path",
            "execute(candidate, test_selection, workspace, environment, timeout, worker_id, campaign_id) -> execution",
            "collect(campaign, workspace) -> result",
            "cancel(campaign, workspace) -> None",
            "resume(campaign_id, workspace, checkpoint) -> campaign",
            "cleanup(campaign, workspace) -> None",
            "diagnostics(workspace) -> dict",
        ],
    }


def write_report(output_dir: Path | None = None) -> Path:
    if output_dir is None:
        output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_domain_model_report()
    path = output_dir / "mutation-domain-model.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    return path


if __name__ == "__main__":
    p = write_report()
    print(f"Domain model report: {p}")
