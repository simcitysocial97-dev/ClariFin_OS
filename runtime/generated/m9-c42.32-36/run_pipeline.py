"""Run the full real-master-scenario forensic pipeline for C42.32-36 Phase 7."""
from runtime.foundation.verification.evidence_planner import default_planner
from runtime.foundation.verification.executor_pipeline import (
    build_executable_plan,
    reconcile,
    default_population,
    default_prior_measurements,
    execute_mutation_task,
    build_forensic_record,
)
import json

CHANGED = ("backend/src/engines/credit_card_engine/risk.py",)

planner = default_planner()
plan = planner.plan(CHANGED)
print(f"Plan: {len(plan.selected_tasks)} tasks for {[t.target for t in plan.selected_tasks]}")

executable = build_executable_plan(plan)
print(f"Executable: {len(executable.tasks)} tasks")

results = {}
for task in executable.tasks:
    print(f"Executing {task.component}...")
    result = execute_mutation_task(task, max_runtime=300)
    results[task.component] = result
    counts = getattr(result, "counts", {})
    print(f"  Result: killed={counts.get('killed', 0)}, exit_code={result.exit_code}")

reconciled = reconcile(
    plan, results, {m.component: m for m in default_prior_measurements()},
    default_population(),
)
print(f"Reconciled: reused={list(reconciled.reused.keys())}, invalidated={list(reconciled.invalidated.keys())}")

record = build_forensic_record(plan, executable, results, reconciled)
print(f"Record ID: {record.record_id}")

out_path = "runtime/generated/m9-c42.32-36/real-master-scenario-full.json"
with open(out_path, "w") as f:
    json.dump(record.to_dict(), f, indent=2)
print(f"Saved to {out_path}")
