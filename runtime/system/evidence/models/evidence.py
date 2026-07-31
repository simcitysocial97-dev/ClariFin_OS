"""Evidence Models — Structured dataclasses for verification evidence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True, slots=True)
class CoverageEvidence:
    """Coverage evidence from test runs."""

    percentage: float
    covered_lines: int
    total_lines: int
    gaps: List[str] = field(default_factory=list)
    source: str = "backend"
    artifact_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass(frozen=True, slots=True)
class MutationEvidence:
    """Mutation testing evidence."""

    score: float
    killed: int
    survived: int
    timeout: int = 0
    error: int = 0
    skipped: int = 0
    survivor_details: List[Dict[str, Any]] = field(default_factory=list)
    source: str = "backend"
    artifact_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass(frozen=True, slots=True)
class VerificationEvidence:
    """Complete verification evidence for a commit/branch."""

    commit_sha: str
    branch: str
    timestamp: str
    status: str  # "pass", "fail", "partial"
    coverage: Optional[CoverageEvidence] = None
    mutation: Optional[MutationEvidence] = None
    property_tests: Dict[str, Any] = field(default_factory=dict)
    contract_tests: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.coverage:
            data["coverage"] = self.coverage.to_dict()
        if self.mutation:
            data["mutation"] = self.mutation.to_dict()
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationEvidence":
        coverage_data = data.get("coverage")
        mutation_data = data.get("mutation")
        coverage = CoverageEvidence(**coverage_data) if coverage_data else None
        mutation = MutationEvidence(**mutation_data) if mutation_data else None
        return cls(
            commit_sha=data["commit_sha"],
            branch=data["branch"],
            timestamp=data["timestamp"],
            status=data["status"],
            coverage=coverage,
            mutation=mutation,
            property_tests=data.get("property_tests", {}),
            contract_tests=data.get("contract_tests", {}),
            artifacts=data.get("artifacts", []),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "VerificationEvidence":
        return cls.from_dict(json.loads(json_str))

    def write(self, path: Path) -> None:
        """Write verification evidence to a JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())


@dataclass(frozen=True, slots=True)
class EvidenceCollectionResult:
    """Result of collecting all evidence from a workspace."""

    workspace_root: str
    collected_at: str
    artifacts: List[Dict[str, Any]]
    collectors: Dict[str, Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json())