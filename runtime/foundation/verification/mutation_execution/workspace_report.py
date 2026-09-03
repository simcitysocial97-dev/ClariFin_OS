# runtime/foundation/verification/mutation_execution/workspace_report.py
#
# M44.6 — Mutation Workspace Report.

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c44"


def build_workspace_report() -> dict:
    campaigns_root = REPO_ROOT / "runtime" / "generated" / "m9-c44" / "campaigns"
    campaigns = []
    if campaigns_root.exists():
        for d in sorted(campaigns_root.iterdir()):
            if d.is_dir() and (d / "manifest.json").exists():
                try:
                    m = json.loads((d / "manifest.json").read_text())
                    exec_count = len(list((d / "executions").glob("*.json"))) if (d / "executions").exists() else 0
                    campaigns.append({
                        "campaign_id": m.get("campaign_id"),
                        "status": m.get("status"),
                        "scope": m.get("scope"),
                        "backend": m.get("mutation_backend"),
                        "path": str(d.relative_to(REPO_ROOT)),
                        "execution_records": exec_count,
                    })
                except Exception:
                    pass

    return {
        "schema": "m9-c44-workspace-report/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "campaigns_root": str(campaigns_root.relative_to(REPO_ROOT)),
        "total_campaigns": len(campaigns),
        "campaigns": campaigns,
        "workspace_structure": {
            "manifest.json": "Campaign state (MutationCampaign serialized)",
            "source/": "Read-only copy of source tree for isolated mutation",
            "mutants/": "Where mutmut applies mutations",
            "executions/": "Per-mutant execution records (.json)",
            "evidence/": "Aggregated results and summaries",
            "logs/": "stdout/stderr captures per execution",
            "reconciliation/": "Reconciliation artifacts",
        },
        "invariants": [
            "No two workers mutate the same workspace concurrently",
            "Workspace is fully disposable after campaign completion",
            "Workspace can be inspected at any point for forensic analysis",
            "Source tree is never mutated in-place during normal operation",
        ],
    }


if __name__ == "__main__":
    p = OUTPUT_DIR / "mutation-workspace-report.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    report = build_workspace_report()
    p.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Workspace report: {p}")
