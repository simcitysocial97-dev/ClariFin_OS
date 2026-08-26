"""Build real-master-scenario forensic record from completed mutation evidence.

The targeted mutation for credit_card_engine already completed
(killed=440, survived=142, score=75.6). We reconstruct ExecutionEvidence
from the persisted mutation-summary.json rather than re-running mutation
(a 116s operation), then run the full forensic pipeline.
"""
import json
from pathlib import Path

from runtime.foundation.verification.evidence_planner import default_planner
from runtime.foundation.verification.executor_pipeline import (
    build_executable_plan,
    reconcile,
    default_population,
    default_prior_measurements,
    build_forensic_record,
    ExecutionEvidence,
)
from runtime.foundation.verification.diagnostic_agent import DiagnosticForensicAgent

CHANGED = ("backend/src/engines/credit_card_engine/risk.py",)
SUMMARY = Path("backend/tests/generated/mutation/mutation-summary.json")


def main():
    summary = json.loads(SUMMARY.read_text())

    planner = default_planner()
    plan = planner.plan(CHANGED)
    print(f"Plan: {len(plan.selected_tasks)} tasks for {[t.target for t in plan.selected_tasks]}")

    executable = build_executable_plan(plan)
    print(f"Executable: {len(executable.tasks)} tasks")

    # Reconstruct ExecutionEvidence from the already-produced mutation summary.
    counts = {
        "generated": summary["mutants_generated"],
        "killed": summary["killed"],
        "survived": summary["survived"],
        "no_tests": summary["no_tests"],
        "timeout": summary["timeout"],
        "suspicious": summary["suspicious"],
        "not_checked": summary["not_checked"],
    }
    evidence = ExecutionEvidence(
        execution_id=summary["run_id"],
        task_id="task::mutation::credit_card_engine",
        component="credit_card_engine",
        capability="credit-card-risk",
        verification_kind="mutation",
        started_at=summary.get("started_at", summary.get("generated_at", "")),
        completed_at=summary.get("ended_at", ""),
        duration_seconds=summary.get("duration_seconds", 0),
        command="verify.py mutation --target credit_card_engine",
        exit_code=0 if summary["execution_status"] == "PASS" else 1,
        failure_kind=None,
        failure_message="",
        counts=counts,
        coverage=None,
        test_count=None,
        source_fingerprint="",
        test_fingerprint="",
        config_fingerprint=summary.get("config_hash", ""),
        toolchain_fingerprint="",
        artifact_paths=("backend/tests/generated/mutation/mutation-summary.json",),
        repository_sha=summary["repository_sha"],
        notes=f"reconstructed from {SUMMARY}",
    )

    fresh = {evidence.component: evidence}

    reconciled = reconcile(
        plan, fresh, {m.component: m for m in default_prior_measurements()},
        default_population(),
    )
    reused = [c.component for c in reconciled.components if c.source == "reused"]
    invalidated = [c.component for c in reconciled.components if c.source == "invalidated"]
    print(f"Reconciled: reused={reused}, invalidated={invalidated}, "
          f"certifiable={reconciled.certifiable}")

    record = build_forensic_record(plan, executable, fresh, reconciled)
    print(f"Record ID: {record.record_id}")

    record_dict = record.to_dict()
    out_path = Path("runtime/generated/m9-c42.32-36/real-master-scenario-full.json")
    out_path.write_text(json.dumps(record_dict, indent=2))

    # Now run the Diagnostic & Forensic Agent.
    agent = DiagnosticForensicAgent()
    report = agent.diagnose(record_dict)
    rep_path = Path("runtime/generated/m9-c42.32-36/real-master-scenario-diagnostic.json")
    rep_path.write_text(json.dumps(report.to_dict(), indent=2))
    print(f"Diagnostic verdict: {report.q9_verdict['verdict']}")
    print(f"Saved record -> {out_path}")
    print(f"Saved diagnostic -> {rep_path}")


if __name__ == "__main__":
    main()
