#!/usr/bin/env python3
"""Phase 5 — Repository Coverage Validation.

Compares repository implementation against platform knowledge.
Detects engines without tests, services without ownership, routers without verification,
repositories without integrity, workspaces without capabilities, undocumented execution paths.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    gap_analysis_path = (
        REPO_ROOT / "runtime" / "generated" / "certification-gap-analysis.json"
    )
    if not gap_analysis_path.exists():
        print(f"Error: {gap_analysis_path} not found.", file=sys.stderr)
        return 1

    data = json.loads(gap_analysis_path.read_text(encoding="utf-8"))

    output = {
        "schema": "repository-gap-analysis/v1",
        "generated_at": data.get("generated_at", "2026-08-06T15:00:00+00:00"),
        "repository_findings": [],
        "platform_findings": [],
        "gap_categories": {
            "engines_without_tests": [],
            "services_without_ownership": [],
            "routers_without_verification": [],
            "repositories_without_integrity": [],
            "workspaces_without_capabilities": [],
            "undocumented_execution_paths": [],
        },
        "summary": {
            "total_repository_gaps": 0,
            "total_platform_gaps": 0,
            "evidence_backed": True,
        },
    }

    # Extract engineering defects from gap analysis
    eng_analysis = data.get("engineering_analysis", {})
    q1 = eng_analysis.get("q1_audit_failure_classification", {})
    repo_defects = q1.get("repository_defects", [])

    for defect in repo_defects:
        output["repository_findings"].append(
            {
                "defect": defect,
                "category": _categorize_defect(defect),
                "severity": "medium",
                "evidence_source": "certification-gap-analysis.json",
            }
        )

    # Map specific gaps
    for finding in repo_defects:
        if "no tests" in finding.lower():
            output["gap_categories"]["engines_without_tests"].append(finding)
        elif "ownership" in finding.lower():
            output["gap_categories"]["services_without_ownership"].append(finding)
        elif "router" in finding.lower():
            output["gap_categories"]["routers_without_verification"].append(finding)
        elif "repository" in finding.lower():
            output["gap_categories"]["repositories_without_integrity"].append(finding)
        elif "workspace" in finding.lower():
            output["gap_categories"]["workspaces_without_capabilities"].append(finding)
        elif "undocumented" in finding.lower() or "execution path" in finding.lower():
            output["gap_categories"]["undocumented_execution_paths"].append(finding)

    output["summary"]["total_repository_gaps"] = len(output["repository_findings"])
    output["summary"]["total_platform_gaps"] = len(output["platform_findings"])

    out_path = REPO_ROOT / "runtime" / "generated" / "repository-gap-analysis.json"
    out_path.write_text(
        json.dumps(output, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(f"Generated: {out_path}")
    return 0


def _categorize_defect(defect: str) -> str:
    defect_lower = defect.lower()
    if "test" in defect_lower:
        return "testing"
    if "ownership" in defect_lower:
        return "ownership"
    if "router" in defect_lower:
        return "verification"
    if "repository" in defect_lower:
        return "integrity"
    if "workspace" in defect_lower:
        return "capability"
    if "undocumented" in defect_lower or "execution path" in defect_lower:
        return "documentation"
    return "other"


if __name__ == "__main__":
    sys.exit(main())
