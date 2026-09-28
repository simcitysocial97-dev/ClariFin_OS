# runtime/foundation/verification/mutation_execution/workspace.py
#
# M9-C44.6 — Isolated Mutation Workspace.
#
# Each campaign gets its own disposable, deterministic workspace under
# `runtime/generated/m9-c44/campaigns/<campaign-id>/`.
#
# Structure:
#   campaigns/<id>/
#     manifest.json          — MutationCampaign state
#     source/                — read-only copy of source tree (or selective copy)
#     mutants/               — where mutmut applies mutations
#     executions/            — per-mutant execution records
#     evidence/              — aggregated results, logs, summaries
#     logs/                  — stdout/stderr captures
#     reconciliation/        — reconciliation artifacts
#
# Invariants:
#   * No two workers mutate the same workspace concurrently.
#   * Workspace is fully disposable after campaign completion.
#   * Workspace can be inspected at any point for forensic analysis.

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.foundation.verification.mutation_execution.domain_model import (
    MutationCampaign,
    MutationCandidate,
    save_campaign_manifest,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CAMPAIGNS_ROOT = REPO_ROOT / "runtime" / "generated" / "m9-c44" / "campaigns"


class MutationWorkspace:
    """Isolated workspace for one mutation campaign."""

    def __init__(self, campaign: MutationCampaign, root: Path | None = None):
        self.campaign = campaign
        self.root = Path(root or CAMPAIGNS_ROOT) / campaign.campaign_id
        self._created = False

    # ── Paths ───────────────────────────────────────────────────────────────

    @property
    def manifest_path(self) -> Path:
        return self.root / "manifest.json"

    @property
    def source_dir(self) -> Path:
        return self.root / "source"

    @property
    def mutants_dir(self) -> Path:
        return self.root / "mutants"

    @property
    def executions_dir(self) -> Path:
        return self.root / "executions"

    @property
    def evidence_dir(self) -> Path:
        return self.root / "evidence"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"

    @property
    def reconciliation_dir(self) -> Path:
        return self.root / "reconciliation"

    # ── Lifecycle ───────────────────────────────────────────────────────────

    def create(
        self, copy_source: bool = True, source_scope: list[str] | None = None
    ) -> MutationWorkspace:
        """Create workspace directory structure. Optionally copy source."""
        self.root.mkdir(parents=True, exist_ok=True)
        self.source_dir.mkdir(exist_ok=True)
        self.mutants_dir.mkdir(exist_ok=True)
        self.executions_dir.mkdir(exist_ok=True)
        self.evidence_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.reconciliation_dir.mkdir(exist_ok=True)

        if copy_source and source_scope:
            self._copy_source(source_scope)

        save_campaign_manifest(self.campaign, self.manifest_path)
        self._created = True
        return self

    def _copy_source(self, scope: list[str]) -> None:
        """Copy selected source paths into workspace source/ directory."""
        for rel in scope:
            src = REPO_ROOT / rel
            if not src.exists():
                continue
            dst = self.source_dir / rel
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(
                    src,
                    dst,
                    symlinks=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                )
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    def persist_candidate(self, candidate: MutationCandidate) -> Path:
        path = self.executions_dir / f"{candidate.canonical_mutant_id}.json"
        path.write_text(json.dumps(candidate.to_dict(), indent=2) + "\n")
        return path

    def persist_execution(self, execution_dict: dict[str, Any]) -> Path:
        mid = execution_dict.get("mutant_id", "unknown")
        path = self.executions_dir / f"{mid}.json"
        path.write_text(json.dumps(execution_dict, indent=2) + "\n")
        return path

    def persist_log(self, log_name: str, content: str) -> Path:
        path = self.logs_dir / f"{log_name}.log"
        path.write_text(content)
        return path

    def persist_evidence(self, name: str, data: Any) -> Path:
        path = self.evidence_dir / f"{name}.json"
        path.write_text(json.dumps(data, indent=2) + "\n")
        return path

    def load_manifest(self) -> MutationCampaign:
        return load_campaign_manifest(self.manifest_path)

    def mark_complete(self) -> None:
        """Update campaign status to COMPLETED in manifest."""
        camp = self.load_manifest()
        camp_dict = camp.to_dict()
        camp_dict["status"] = "COMPLETED"
        self.manifest_path.write_text(json.dumps(camp_dict, indent=2) + "\n")

    def mark_failed(self, reason: str) -> None:
        camp_dict = self.load_manifest().to_dict()
        camp_dict["status"] = "FAILED"
        camp_dict["failure_reason"] = reason
        self.manifest_path.write_text(json.dumps(camp_dict, indent=2) + "\n")

    def cleanup(self) -> None:
        """Remove the entire workspace."""
        if self.root.exists():
            shutil.rmtree(self.root, ignore_errors=True)
        self._created = False

    @property
    def exists(self) -> bool:
        return self.root.exists() and self.manifest_path.exists()

    @property
    def created(self) -> bool:
        return self._created

    def summary(self) -> dict[str, Any]:
        exec_files = list(self.executions_dir.glob("*.json")) if self.exists else []
        return {
            "campaign_id": self.campaign.campaign_id,
            "path": str(self.root.relative_to(REPO_ROOT)),
            "exists": self.exists,
            "execution_records": len(exec_files),
            "manifest_status": self.load_manifest().status if self.exists else "N/A",
        }


def load_campaign_manifest(path: Path) -> MutationCampaign:
    from runtime.foundation.verification.mutation_execution.domain_model import (
        load_campaign_manifest as _load,
    )

    return _load(path)


def create_workspace(
    *,
    campaign_id: str | None = None,
    repository_revision: str = "",
    scope: str = "full",
    backend: str = "mutmut",
    backend_version: str = "0.0.0",
    configuration_fingerprint: str = "",
    test_selection: str = "",
    execution_policy: str = "serial",
    worker_count: int = 1,
    shard_index: int | None = None,
    shard_total: int | None = None,
    resumed_from: str | None = None,
    copy_source: bool = True,
    source_scope: list[str] | None = None,
) -> MutationWorkspace:
    """Factory function to create a new campaign workspace."""
    import uuid as _uuid

    cid = campaign_id or f"mut-{_uuid.uuid4().hex[:12]}"
    now = datetime.now(UTC).isoformat()

    campaign = MutationCampaign(
        campaign_id=cid,
        repository_revision=repository_revision or "unknown",
        environment_fingerprint="",
        mutation_backend=backend,
        backend_version=backend_version,
        scope=scope,
        test_selection=test_selection,
        configuration_fingerprint=configuration_fingerprint,
        execution_policy=execution_policy,
        creation_timestamp=now,
        status="INITIALIZED",
        resumed_from=resumed_from,
        worker_count=worker_count,
        shard_index=shard_index,
        shard_total=shard_total,
    )
    ws = MutationWorkspace(campaign)
    ws.create(copy_source=copy_source, source_scope=source_scope)
    return ws


def resume_workspace(campaign_id: str, root: Path | None = None) -> MutationWorkspace:
    """Load an existing workspace for resume. Raises if not found."""
    ws_root = Path(root or CAMPAIGNS_ROOT) / campaign_id
    if not ws_root.exists():
        raise FileNotFoundError(f"Campaign workspace not found: {campaign_id}")
    manifest = ws_root / "manifest.json"
    if not manifest.exists():
        raise FileNotFoundError(f"No manifest in campaign workspace: {campaign_id}")

    camp = load_campaign_manifest(manifest)
    ws = MutationWorkspace(camp, root=root)
    ws._created = True
    return ws


def list_campaigns() -> list[dict[str, Any]]:
    """List all campaign workspaces."""
    if not CAMPAIGNS_ROOT.exists():
        return []
    campaigns = []
    for d in sorted(CAMPAIGNS_ROOT.iterdir()):
        if d.is_dir() and (d / "manifest.json").exists():
            try:
                camp = load_campaign_manifest(d / "manifest.json")
                exec_count = (
                    len(list((d / "executions").glob("*.json")))
                    if (d / "executions").exists()
                    else 0
                )
                campaigns.append(
                    {
                        "campaign_id": camp.campaign_id,
                        "status": camp.status,
                        "scope": camp.scope,
                        "backend": camp.mutation_backend,
                        "creation_timestamp": camp.creation_timestamp,
                        "execution_records": exec_count,
                        "path": str(d.relative_to(REPO_ROOT)),
                    }
                )
            except Exception:
                pass
    return campaigns


__all__ = [
    "MutationWorkspace",
    "create_workspace",
    "resume_workspace",
    "list_campaigns",
    "CAMPAIGNS_ROOT",
]
