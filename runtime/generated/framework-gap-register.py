#!/usr/bin/env python3
"""Phase 8 — Framework Gap Register.

Documents evidence-backed platform limitations observed during validation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    output = {
        "schema": "framework-gap-register/v1",
        "generated_at": "2026-08-06T15:00:00+00:00",
        "gaps": [
            {
                "gap_id": "gap-verification-execution-success-rate",
                "observed_evidence": "Local verification runs show 0% success rate (0/5 passed) in health report. Cache hit rate is 0% (0/5).",
                "affected_workflow": "local_verification_execution",
                "engineering_impact": "Developers cannot rely on local verification for fast feedback. All verification must be delegated to CI, reducing iteration speed.",
                "proposed_future_program": "Program 16.0 — Verification Execution Reliability",
            },
            {
                "gap_id": "gap-changeset-platform-artifact-pollution",
                "observed_evidence": "Intelligence pipeline detects generated artifacts (runtime/generated/*.json, *.md, *.py) as changed files, polluting the changeset with platform-internal files.",
                "affected_workflow": "change_detection_and_intelligence_analysis",
                "engineering_impact": "Platform files are classified as 'platform' paths, but they still appear in the changeset, causing unnecessary intelligence analysis on non-production files.",
                "proposed_future_program": "Program 16.0 — Changeset Filtering",
            },
            {
                "gap_id": "gap-heavy-profile-local-timeout",
                "observed_evidence": "python3 runtime/verify.py quick timed out after 120000ms (2 minutes). The profile is designed for CI execution, not local developer machines.",
                "affected_workflow": "local_verification_profiles",
                "engineering_impact": "Developers cannot run full verification profiles locally. The platform must clearly distinguish between lightweight (local) and heavy (CI) profiles.",
                "proposed_future_program": "Program 16.0 — Profile Execution Boundaries",
            },
            {
                "gap_id": "gap-ci-collection-opt-in-requirement",
                "observed_evidence": "GitHub intelligence collection is disabled by default (requires --no-ci flag to disable, or default behavior requires explicit CI flag). The retrieval policy shows 'available': false when CI collection is disabled.",
                "affected_workflow": "ci_intelligence_collection",
                "engineering_impact": "Developers may forget to enable CI collection, leading to incomplete diagnostic data when analyzing CI failures.",
                "proposed_future_program": "Program 16.0 — CI Intelligence Defaults",
            },
        ],
        "summary": {
            "total_gaps": 4,
            "evidence_backed_gaps": 4,
            "speculative_gaps": 0,
            "implementation_pending": True,
        },
    }

    out_path = REPO_ROOT / "runtime" / "generated" / "framework-gap-register.json"
    out_path.write_text(
        json.dumps(output, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(f"Generated: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
