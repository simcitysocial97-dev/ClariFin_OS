"""Status service adapter (C67.1 — ``/platform/v1/status``).

Aggregates canonical runtime identity, health, certification state,
and catalog counts into the Phase 1 ``Status`` contract.

Source-of-truth chain:
    git (commit, branch, tree)
        ↓
    runtime.version / runtime.fingerprint
        ↓
    EngineeringHealthReport / AnalyticsEngine (framework health)
        ↓
    CapabilityCatalog (capability count)
        ↓
    workflow_inspection (workflow count)
        ↓
    EngineeringEventStore (recent run)
        ↓
    generated metadata (certification state from C66 artifact)

No new persistent model. No mock state. All values originate from
canonical runtime authorities.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from runtime.platform.api.contracts import status as status_contract
from runtime.platform.api.contracts._primitives import Status
from runtime.platform.api.services._helpers import envelope, now_iso
from runtime.system.observability.analytics import AnalyticsEngine
from runtime.system.observability.event_store import EngineeringEventStore

REPO_ROOT = Path(__file__).resolve().parents[4]
C66_ARTIFACT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c66-certification-forensics"
VERSION_PATH = REPO_ROOT / "runtime" / "VERSION"


def _git_field(field_args: list[str]) -> str:
    """Return a single git field value, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git", *field_args],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _load_certification_state() -> str:
    """Read the C66 certification state from the generated artifact."""
    cert_file = C66_ARTIFACT_DIR / "final-certification.md"
    if cert_file.exists():
        text = cert_file.read_text(errors="replace")
        if "CERTIFIED" in text:
            return "CERTIFIED"
        if "BLOCKED" in text:
            return "BLOCKED"
    return "UNKNOWN"


def build_status() -> dict[str, Any]:
    """Build the ``platform.status`` envelope from canonical runtime state."""

    commit_sha = _git_field(["rev-parse", "HEAD"])
    tree_sha = _git_field(["rev-parse", "HEAD^{tree}"])
    branch = _git_field(["branch", "--show-current"])
    fingerprint = _git_field(["rev-parse", "--short", "HEAD"])

    runtime_version = "1.0.0"
    if VERSION_PATH.exists():
        text = VERSION_PATH.read_text().strip()
        # Extract first line or semver token from multi-line VERSION file.
        first_line = text.splitlines()[0] if text else ""
        import re as _re

        m = _re.search(r"[\d]+\.[\d]+\.[\d]+", first_line)
        if m:
            runtime_version = m.group(0)

    store = EngineeringEventStore()
    engine = AnalyticsEngine(store)
    analytics = engine.compute()
    combined = analytics.combined
    verif = combined.get("verification", {})

    # Framework health from the verification success rate.
    success_rate = float(verif.get("success_rate", 0.0))
    total_runs = int(verif.get("total_runs", 0))
    if total_runs == 0:
        framework_health = Status.UNKNOWN
    elif success_rate >= 0.95:
        framework_health = Status.HEALTHY
    elif success_rate >= 0.80:
        framework_health = Status.DEGRAD
    else:
        framework_health = Status.UNHEALTHY

    # Certification state from C66 artifact.
    certification_state = _load_certification_state()

    # Capability count from the live catalog.
    try:
        from runtime.foundation.verification.capability_catalog import (
            get_capability_catalog,
        )

        catalog = get_capability_catalog()
        capability_count = len(catalog.entries)
    except Exception:
        capability_count = 0

    # Profile count — derived from profiles.py available profiles.
    try:
        from runtime.foundation.verification.profiles import profile_names

        profile_count = len(profile_names())
    except Exception:
        profile_count = 0

    # Workflow count from canonical workflow inspection.
    try:
        from runtime.foundation.verification.workflow_inspection import (
            enumerate_workflows,
        )

        workflows = enumerate_workflows()
        workflow_count = len(workflows)
    except Exception:
        workflow_count = 0

    # Recent run from event store.
    recent_status: Status | None = None
    recent_run_id: str | None = None
    events = list(store.iter_events())
    for evt in reversed(events):
        if evt.event_type == "VerificationCompleted":
            payload = evt.payload or {}
            status_val = payload.get("status", "unknown")
            if status_val in ("passed", "failed", "blocked", "interrupted"):
                recent_status = {
                    "passed": Status.HEALTHY,
                    "failed": Status.UNHEALTHY,
                    "blocked": Status.DEGRAD,
                    "interrupted": Status.DEGRAD,
                }.get(status_val, Status.UNKNOWN)
            else:
                recent_status = Status.UNKNOWN
            recent_run_id = evt.event_id
            break

    data = {
        "repository": str(REPO_ROOT),
        "commit_sha": commit_sha,
        "tree_sha": tree_sha,
        "branch": branch,
        "runtime_version": runtime_version,
        "fingerprint": fingerprint,
        "framework_health": framework_health.value,
        "certification_state": certification_state,
        "capability_count": capability_count,
        "profile_count": profile_count,
        "workflow_count": workflow_count,
        "recent_run_status": recent_status.value if recent_status else None,
        "recent_run_id": recent_run_id,
        "configuration_identity": None,
        "last_updated": now_iso(),
    }
    return envelope(kind=status_contract.STATUS_KIND, data=data)
