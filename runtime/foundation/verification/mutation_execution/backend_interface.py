# runtime/foundation/verification/mutation_execution/backend_interface.py
#
# M9-C44.3 — Mutation Backend Interface.
#
# Strict interface that every mutation backend adapter MUST implement.
# The rest of ClariFin_OS calls ONLY this interface; it never invokes a
# specific tool directly.  `mutmut` is one implementation behind this boundary.
#
# Design:
#   - Discover(scope)      -> list[MutationCandidate]
#   - Generate(campaign, candidates) -> None  (write mutation state to workspace)
#   - Execute(candidate, test_selection, workspace) -> MutationExecution
#   - Collect(campaign_id) -> MutationResult  (aggregate from workspace)
#   - Cancel(campaign_id)  -> None
#   - Resume(campaign_id, last_checkpoint) -> MutationCampaign
#   - Cleanup(campaign_id) -> None
#   - Diagnostics(workspace) -> dict

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable

from runtime.foundation.verification.mutation_execution.domain_model import (
    MutationCampaign,
    MutationCandidate,
    MutationExecution,
    MutationResult,
)


@runtime_checkable
class MutationBackendProtocol(Protocol):
    """Protocol that any mutation backend adapter MUST satisfy."""

    backend_name: str
    backend_version: str

    def discover(self, scope: str, candidates: list[MutationCandidate]) -> list[MutationCandidate]:
        """Discover mutations within the given scope. Returns enhanced candidates."""
        ...

    def generate(
        self,
        campaign: MutationCampaign,
        candidates: list[MutationCandidate],
        workspace: Path,
    ) -> Path:
        """Apply mutations to workspace and return path to generated state (mutants dir, etc.)."""
        ...

    def execute(
        self,
        candidate: MutationCandidate,
        test_selection: tuple[str, ...],
        workspace: Path,
        environment: dict[str, str],
        timeout: float,
        worker_id: str,
        campaign_id: str,
    ) -> MutationExecution:
        """Execute one mutant against selected tests in isolated workspace."""
        ...

    def collect(self, campaign: MutationCampaign, workspace: Path) -> MutationResult:
        """Aggregate all execution records into a canonical MutationResult."""
        ...

    def cancel(self, campaign: MutationCampaign, workspace: Path) -> None:
        """Gracefully cancel an in-progress campaign."""
        ...

    def resume(
        self,
        campaign_id: str,
        workspace: Path,
        last_checkpoint: MutationCampaign,
    ) -> MutationCampaign:
        """Resume a paused/interrupted campaign from last checkpoint."""
        ...

    def cleanup(self, campaign: MutationCampaign, workspace: Path) -> None:
        """Clean up all workspace artifacts for a completed campaign."""
        ...

    def diagnostics(self, workspace: Path) -> dict:
        """Return diagnostic information about the current workspace state."""
        ...


class MutationBackendBase(ABC):
    """Abstract base for mutation backend adapters.

    Subclasses implement the protocol methods.  Common cross-cutting concerns
    (version verification, config validation, environment checks) live here.
    """

    backend_name: str = "abstract"
    backend_version: str = "0.0.0"

    # ------------------------------------------------------------------
    # Lifecycle hooks (optional override)
    # ------------------------------------------------------------------
    def verify_tool_version(self, minimum_version: str) -> bool:
        """Check that the installed backend meets minimum version. Default: pass."""
        return True

    def verify_configuration(self, workspace: Path) -> list[str]:
        """Validate workspace configuration. Return list of errors (empty = OK)."""
        return []

    def verify_environment(self, workspace: Path) -> list[str]:
        """Validate runtime environment before execution."""
        return []

    # ------------------------------------------------------------------
    # Canonical protocol methods (required)
    # ------------------------------------------------------------------
    @abstractmethod
    def discover(
        self, scope: str, candidates: list[MutationCandidate]
    ) -> list[MutationCandidate]:
        raise NotImplementedError

    @abstractmethod
    def generate(
        self,
        campaign: MutationCampaign,
        candidates: list[MutationCandidate],
        workspace: Path,
    ) -> Path:
        raise NotImplementedError

    @abstractmethod
    def execute(
        self,
        candidate: MutationCandidate,
        test_selection: tuple[str, ...],
        workspace: Path,
        environment: dict[str, str],
        timeout: float,
        worker_id: str,
        campaign_id: str,
    ) -> MutationExecution:
        raise NotImplementedError

    @abstractmethod
    def collect(self, campaign: MutationCampaign, workspace: Path) -> MutationResult:
        raise NotImplementedError

    def cancel(self, campaign: MutationCampaign, workspace: Path) -> None:
        """Default: no-op cancel."""

    def resume(
        self, campaign_id: str, workspace: Path, last_checkpoint: MutationCampaign
    ) -> MutationCampaign:
        """Default: return campaign as-is (not resumable)."""
        return last_checkpoint

    def cleanup(self, campaign: MutationCampaign, workspace: Path) -> None:
        """Default: no-op cleanup."""

    def diagnostics(self, workspace: Path) -> dict:
        """Default: minimal diagnostics."""
        return {
            "backend": self.backend_name,
            "version": self.backend_version,
            "workspace_exists": workspace.exists(),
        }


__all__ = [
    "MutationBackendProtocol",
    "MutationBackendBase",
]
