"""Base Evidence Collector Framework."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, List, Dict, Optional


@dataclass(frozen=True)
class EvidenceArtifact:
    """A single piece of evidence collected from the workspace."""

    artifact_type: str  # e.g., "coverage", "mutation", "property_test"
    name: str  # Human-readable name
    path: str  # Relative path to the artifact file
    timestamp: str  # ISO format timestamp
    metadata: Dict[str, Any]  # Collector-specific metadata

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EvidenceCollector(ABC):
    """Abstract base class for evidence collectors.

    Subclasses implement two methods:
    - collect_artifacts(): Returns List[EvidenceArtifact] (primary interface)
    - collect(): Returns collector-specific evidence object (optional, for direct use)
    """

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    @property
    @abstractmethod
    def artifact_type(self) -> str:
        """Unique identifier for this collector's artifact type."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this collector."""
        pass

    @abstractmethod
    def collect_artifacts(self) -> List[EvidenceArtifact]:
        """Collect evidence artifacts from the workspace.

        Returns:
            List of EvidenceArtifact objects found.
        """
        pass

    def collect(self, artifact_path: Optional[Path] = None) -> Any:
        """Collect evidence from a specific artifact path.

        Default implementation delegates to collect_artifacts().
        Subclasses that produce typed evidence objects override this.
        """
        return self.collect_artifacts()

    def _read_json(self, path: Path) -> Any:
        """Safely read a JSON file."""
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def _read_text(self, path: Path) -> str:
        """Safely read a text file."""
        try:
            return path.read_text()
        except OSError:
            return ""

    def _artifact(
        self,
        name: str,
        path: Path,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvidenceArtifact:
        """Create an EvidenceArtifact from a file path."""
        try:
            rel_path = path.relative_to(self.workspace_root)
        except ValueError:
            rel_path = path
        return EvidenceArtifact(
            artifact_type=self.artifact_type,
            name=name,
            path=str(rel_path),
            timestamp=datetime.utcnow().isoformat() + "Z",
            metadata=metadata or {},
        )
