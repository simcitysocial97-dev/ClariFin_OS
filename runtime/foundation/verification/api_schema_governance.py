# runtime/foundation/verification/api_schema_governance.py
#
# M9-C48 D2 — API schema mismatch governance (GAP-013).
#
# Distinguishes three states:
#   * Historical defect — provenance only, not authoritative.
#   * Current contract  — derived from the API Contract Integrity Gate.
#   * Current enforcement — the workflow that re-runs the gate on every PR.
#
# This module is pure logic + filesystem reads of the gate's evidence
# file. It does NOT execute the gate (which requires backend fixtures);
# it consumes the gate's last-emitted evidence and produces a governance
# report that distinguishes:
#   1. The historical loan-shape mismatch (acknowledged, documented,
#      no longer authoritative).
#   2. The current contract shape (whatever the gate certified last).
#   3. The enforcement authority (the workflow file exists).
#
# Importable by tests and by runtime/verify.py.

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


HISTORICAL_DEFECTS: tuple[dict[str, str], ...] = (
    {
        "id": "loan-api-response-shape-c30-c32",
        "title": "Loan API response-shape mismatch",
        "description": (
            "Backend returned a list of loans; frontend expected a wrapped "
            "object. Fixed by introducing LoanListResponse wrapper."
        ),
        "discovered_in": "M9-C30",
        "remediated_in": "M9-C32 / C46 reconciliation",
        "current_state": "RESOLVED",
        "authority": "provenance only",
    },
)


@dataclass(frozen=True, slots=True)
class ContractEvidence:
    evidence_path: str
    present: bool
    gate_status: str
    dimensions: dict[str, str]
    last_updated: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class GovernanceReport:
    schema: str
    generated_at: str
    repository_sha: str
    historical_defects: tuple[dict[str, str], ...]
    current_contract: ContractEvidence | None
    enforcement_workflow_present: bool
    enforcement_workflow_path: str
    state: str  # RESOLVED | UNRESOLVED | UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "repository_sha": self.repository_sha,
            "historical_defects": list(self.historical_defects),
            "current_contract": (
                self.current_contract.to_dict() if self.current_contract else None
            ),
            "enforcement_workflow_present": self.enforcement_workflow_present,
            "enforcement_workflow_path": self.enforcement_workflow_path,
            "state": self.state,
        }


def _git_sha() -> str:
    import subprocess
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def load_contract_evidence(
    evidence_path: str | Path = "runtime/generated/api-contract-evidence.json",
) -> ContractEvidence | None:
    """Load the last-emitted API contract gate evidence."""
    p = Path(evidence_path)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text())
    except Exception:
        return None
    gate_status = str(data.get("status") or data.get("verdict") or "UNKNOWN")
    dimensions: dict[str, str] = {}
    for dim in ("structural", "generated", "consumer", "wire"):
        v = data.get(dim)
        if isinstance(v, dict):
            dimensions[dim] = str(v.get("status") or v.get("verdict") or "UNKNOWN")
        elif v is not None:
            dimensions[dim] = str(v)
    last_updated = str(
        data.get("last_updated")
        or data.get("generated_at")
        or data.get("timestamp")
        or ""
    )
    return ContractEvidence(
        evidence_path=str(p),
        present=True,
        gate_status=gate_status,
        dimensions=dimensions,
        last_updated=last_updated,
    )


def workflow_present(workflows_dir: str | Path = ".github/workflows") -> bool:
    """Check whether the api-contracts workflow exists."""
    d = Path(workflows_dir)
    if not d.exists():
        return False
    return any(p.name.startswith("api-contracts") for p in d.glob("*.yml"))


def build_governance_report(
    *,
    evidence_path: str | Path = "runtime/generated/api-contract-evidence.json",
    workflows_dir: str | Path = ".github/workflows",
) -> GovernanceReport:
    """Build the governance report distinguishing historical / current / enforcement."""
    ce = load_contract_evidence(evidence_path)
    wf_present = workflow_present(workflows_dir)
    if ce and ce.gate_status in {"PASS", "OK", "GREEN"}:
        state = "RESOLVED"
    elif ce is None:
        state = "UNKNOWN"
    else:
        state = "UNRESOLVED"
    return GovernanceReport(
        schema="m9-c48/api-schema-governance@1",
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        repository_sha=_git_sha(),
        historical_defects=HISTORICAL_DEFECTS,
        current_contract=ce,
        enforcement_workflow_present=wf_present,
        enforcement_workflow_path=str(Path(workflows_dir) / "api-contracts.yml"),
        state=state,
    )


__all__ = [
    "HISTORICAL_DEFECTS",
    "ContractEvidence",
    "GovernanceReport",
    "load_contract_evidence",
    "workflow_present",
    "build_governance_report",
]
