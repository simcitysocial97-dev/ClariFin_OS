"""Change Impact Analysis Engine.

Given modified files, determines:
- affected capabilities
- affected engines
- affected services
- affected repositories
- affected contracts
- affected properties
- affected golden datasets
- affected integration tests
- affected mutation targets

Output is machine-readable JSON for GitHub Actions consumption.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from src.verification.runtime.registries import CapabilityRegistry

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"
SRC_DIR = BACKEND_DIR / "src"


@dataclass
class AffectedComponent:
    """A single affected component."""

    id: str
    type: str
    name: str = ""
    risk: str = "LOW"
    criticality: str = "unknown"
    verification_required: list[str] = field(default_factory=list)
    verification_skippable: list[str] = field(default_factory=list)


@dataclass
class ChangeImpact:
    """Complete change impact analysis result."""

    changed_files: list[str] = field(default_factory=list)
    affected_capabilities: list[AffectedComponent] = field(default_factory=list)
    affected_engines: list[AffectedComponent] = field(default_factory=list)
    affected_services: list[AffectedComponent] = field(default_factory=list)
    affected_repositories: list[AffectedComponent] = field(default_factory=list)
    affected_contracts: list[AffectedComponent] = field(default_factory=list)
    affected_properties: list[AffectedComponent] = field(default_factory=list)
    affected_golden_datasets: list[AffectedComponent] = field(default_factory=list)
    affected_integration_tests: list[AffectedComponent] = field(default_factory=list)
    affected_mutation_targets: list[AffectedComponent] = field(default_factory=list)
    overall_risk: str = "LOW"
    overall_confidence: str = "HIGH"
    strategy: str = "full"
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed_files": self.changed_files,
            "affected_capabilities": [
                self._component_to_dict(c) for c in self.affected_capabilities
            ],
            "affected_engines": [
                self._component_to_dict(c) for c in self.affected_engines
            ],
            "affected_services": [
                self._component_to_dict(c) for c in self.affected_services
            ],
            "affected_repositories": [
                self._component_to_dict(c) for c in self.affected_repositories
            ],
            "affected_contracts": [
                self._component_to_dict(c) for c in self.affected_contracts
            ],
            "affected_properties": [
                self._component_to_dict(c) for c in self.affected_properties
            ],
            "affected_golden_datasets": [
                self._component_to_dict(c) for c in self.affected_golden_datasets
            ],
            "affected_integration_tests": [
                self._component_to_dict(c) for c in self.affected_integration_tests
            ],
            "affected_mutation_targets": [
                self._component_to_dict(c) for c in self.affected_mutation_targets
            ],
            "overall_risk": self.overall_risk,
            "overall_confidence": self.overall_confidence,
            "strategy": self.strategy,
            "generated_at": self.generated_at,
        }

    @staticmethod
    def _component_to_dict(comp: AffectedComponent) -> dict[str, Any]:
        return {
            "id": comp.id,
            "type": comp.type,
            "name": comp.name,
            "risk": comp.risk,
            "criticality": comp.criticality,
            "verification_required": comp.verification_required,
            "verification_skippable": comp.verification_skippable,
        }


class ImpactEngine:
    """Analyzes changed files to determine impact on the verification surface."""

    RISK_PATTERNS: dict[str, tuple[str, str]] = {
        "/engines/": ("CRITICAL", "HIGH"),
        "/verification/intelligence/": ("HIGH", "HIGH"),
        "/services/": ("HIGH", "MEDIUM"),
        "/routers/": ("MEDIUM", "HIGH"),
        "/repositories/": ("HIGH", "HIGH"),
        "/models/": ("CRITICAL", "HIGH"),
        "/contracts/": ("MEDIUM", "MEDIUM"),
        "/tests/properties/": ("LOW", "HIGH"),
        "/tests/golden/": ("LOW", "HIGH"),
        "/tests/capability/": ("LOW", "HIGH"),
        "/tests/invariants/": ("LOW", "HIGH"),
        "/tests/integration/": ("MEDIUM", "MEDIUM"),
        "/tests/meta/": ("LOW", "HIGH"),
        "/tests/architecture/": ("LOW", "HIGH"),
        "/.github/workflows/": ("MEDIUM", "MEDIUM"),
        "/pyproject.toml": ("MEDIUM", "HIGH"),
        "/requirements.txt": ("MEDIUM", "HIGH"),
    }

    def __init__(self) -> None:
        self._capability_registry: CapabilityRegistry = cast(CapabilityRegistry, {})
        self._file_to_capabilities: dict[str, set[str]] = {}
        self._file_to_engines: dict[str, set[str]] = {}
        self._file_to_services: dict[str, set[str]] = {}
        self._file_to_repos: dict[str, set[str]] = {}

    def analyze(self, changed_files: list[str]) -> ChangeImpact:
        """Analyze changed files and return impact assessment."""
        self._load_registries()
        self._build_file_mappings()

        impact = ChangeImpact(
            changed_files=changed_files,
            generated_at=datetime.now(UTC).isoformat(),
        )

        affected_caps: set[str] = set()
        affected_engines: set[str] = set()
        affected_services: set[str] = set()
        affected_repos: set[str] = set()
        affected_contracts: set[str] = set()
        affected_properties: set[str] = set()
        affected_golden: set[str] = set()
        affected_integration: set[str] = set()
        affected_mutation: set[str] = set()

        for file_path in changed_files:
            risk, confidence = self._classify_file_risk(file_path)

            caps = self._get_capabilities_for_file(file_path)
            engines = self._get_engines_for_file(file_path)
            services = self._get_services_for_file(file_path)
            repos = self._get_repos_for_file(file_path)

            affected_caps.update(caps)
            affected_engines.update(engines)
            affected_services.update(services)
            affected_repos.update(repos)

            if risk == "CRITICAL":
                affected_mutation.update(engines)
                affected_integration.update(caps)

            if risk in ("HIGH", "CRITICAL"):
                affected_contracts.update(caps)
                affected_properties.update(caps)
                affected_golden.update(caps)

            if risk == "MEDIUM":
                affected_properties.update(caps)
                affected_golden.update(caps)

        impact.affected_capabilities = [
            self._build_component(c, "capability") for c in sorted(affected_caps)
        ]
        impact.affected_engines = [
            self._build_component(e, "engine") for e in sorted(affected_engines)
        ]
        impact.affected_services = [
            self._build_component(s, "service") for s in sorted(affected_services)
        ]
        impact.affected_repositories = [
            self._build_component(r, "repository") for r in sorted(affected_repos)
        ]
        impact.affected_contracts = [
            self._build_component(c, "contract") for c in sorted(affected_contracts)
        ]
        impact.affected_properties = [
            self._build_component(p, "property") for p in sorted(affected_properties)
        ]
        impact.affected_golden_datasets = [
            self._build_component(g, "golden_dataset") for g in sorted(affected_golden)
        ]
        impact.affected_integration_tests = [
            self._build_component(i, "integration_test")
            for i in sorted(affected_integration)
        ]
        impact.affected_mutation_targets = [
            self._build_component(m, "mutation_target")
            for m in sorted(affected_mutation)
        ]

        impact.overall_risk = self._compute_overall_risk(affected_caps, changed_files)
        impact.overall_confidence = self._compute_overall_confidence(changed_files)
        impact.strategy = self._determine_strategy(impact)

        return impact

    def _load_registries(self) -> None:
        """Load the capability registry."""
        from src.verification.runtime.registries import load_capability_registry

        self._capability_registry = load_capability_registry()

    def _build_file_mappings(self) -> None:
        """Build mappings from file paths to capabilities/engines/services/repos."""
        self._file_to_capabilities = {}
        self._file_to_engines = {}
        self._file_to_services = {}
        self._file_to_repos = {}

        for cap in self._capability_registry.get("capabilities", []):
            cap_id = cap.get("id", "")

            for router in cap.get("routers", []):
                self._file_to_capabilities.setdefault(router, set()).add(cap_id)

            for service in cap.get("services", []):
                self._file_to_capabilities.setdefault(service, set()).add(cap_id)
                self._file_to_services.setdefault(service, set()).add(cap_id)

            for engine in cap.get("engines", []):
                self._file_to_capabilities.setdefault(engine, set()).add(cap_id)
                self._file_to_engines.setdefault(engine, set()).add(cap_id)

            for repo in cap.get("repositories", []):
                self._file_to_capabilities.setdefault(repo, set()).add(cap_id)
                self._file_to_repos.setdefault(repo, set()).add(cap_id)

    def _classify_file_risk(self, file_path: str) -> tuple[str, str]:
        """Classify risk level for a changed file."""
        for pattern, (risk, confidence) in self.RISK_PATTERNS.items():
            if pattern in file_path:
                return risk, confidence

        if file_path.endswith((".md", ".txt", ".rst")):
            return "LOW", "HIGH"

        if file_path.startswith("backend/tests/"):
            return "LOW", "HIGH"

        if file_path.startswith("frontend/"):
            return "MEDIUM", "MEDIUM"

        return "LOW", "LOW"

    def _get_capabilities_for_file(self, file_path: str) -> set[str]:
        """Get capabilities affected by a changed file."""
        result: set[str] = set()

        direct = self._file_to_capabilities.get(file_path, set())
        result.update(direct)

        for cap in self._capability_registry.get("capabilities", []):
            cap_id = cap.get("id", "")
            for engine in cap.get("engines", []):
                if engine in file_path:
                    result.add(cap_id)
            for service in cap.get("services", []):
                if service in file_path:
                    result.add(cap_id)
            for router in cap.get("routers", []):
                if router in file_path:
                    result.add(cap_id)
            for repo in cap.get("repositories", []):
                if repo in file_path:
                    result.add(cap_id)

        for dep_cap in self._capability_registry.get("capabilities", []):
            dep_id = dep_cap.get("id", "")
            if dep_id in result:
                for transitive_dep in dep_cap.get("dependencies", []):
                    result.add(transitive_dep)

        return result

    def _get_engines_for_file(self, file_path: str) -> set[str]:
        """Get engines affected by a changed file."""
        result: set[str] = set()
        for engine in self._file_to_engines.get(file_path, set()):
            result.add(engine)
        return result

    def _get_services_for_file(self, file_path: str) -> set[str]:
        """Get services affected by a changed file."""
        result: set[str] = set()
        for service in self._file_to_services.get(file_path, set()):
            result.add(service)
        return result

    def _get_repos_for_file(self, file_path: str) -> set[str]:
        """Get repositories affected by a changed file."""
        result: set[str] = set()
        for repo in self._file_to_repos.get(file_path, set()):
            result.add(repo)
        return result

    def _build_component(
        self, component_id: str, component_type: str
    ) -> AffectedComponent:
        """Build an AffectedComponent from a capability/engine/service ID."""
        cap = self._get_capability_by_id(component_id)
        return AffectedComponent(
            id=component_id,
            type=component_type,
            name=cap.get("name", component_id) if cap else component_id,
            risk=cap.get("risk", "LOW") if cap else "LOW",
            criticality=cap.get("criticality", "unknown") if cap else "unknown",
            verification_required=self._get_required_verification(cap or {}),
            verification_skippable=self._get_skippable_verification(cap or {}),
        )

    def _get_capability_by_id(self, cap_id: str) -> dict[str, Any] | None:
        """Look up a capability by ID in the registry."""
        for cap in self._capability_registry.get("capabilities", []):
            cap_data: dict[str, Any] = cap
            if cap_data.get("id") == cap_id:
                return cap_data
        return None

    def _get_required_verification(self, cap: dict[str, Any]) -> list[str]:
        """Get verification types required for a capability."""
        required: list[str] = []
        if cap.get("contracts"):
            required.append("contract")
        if cap.get("property_tests"):
            required.append("property")
        if cap.get("golden_datasets"):
            required.append("golden")
        if cap.get("invariants"):
            required.append("invariant")
        if cap.get("architecture_tests"):
            required.append("architecture")
        return required

    def _get_skippable_verification(self, cap: dict[str, Any]) -> list[str]:
        """Get verification types that can be skipped for a capability."""
        skippable: list[str] = []
        risk = cap.get("risk", "LOW")
        if risk == "LOW":
            skippable.append("mutation")
        if risk == "LOW" and cap.get("criticality") != "high":
            skippable.append("integration")
        return skippable

    def _compute_overall_risk(
        self, affected_caps: set[str], changed_files: list[str]
    ) -> str:
        """Compute overall risk from affected capabilities and files."""
        if not affected_caps and not changed_files:
            return "LOW"

        risk_priority = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        max_risk = "LOW"

        for cap_id in affected_caps:
            cap = self._get_capability_by_id(cap_id)
            if cap:
                cap_risk = cap.get("risk", "LOW")
                if risk_priority.get(cap_risk, 0) > risk_priority.get(max_risk, 0):
                    max_risk = cap_risk

        for file_path in changed_files:
            file_risk, _ = self._classify_file_risk(file_path)
            if risk_priority.get(file_risk, 0) > risk_priority.get(max_risk, 0):
                max_risk = file_risk

        return max_risk

    def _compute_overall_confidence(self, changed_files: list[str]) -> str:
        """Compute overall confidence based on file types."""
        if not changed_files:
            return "HIGH"

        min_confidence = "HIGH"
        for file_path in changed_files:
            _, confidence = self._classify_file_risk(file_path)
            conf_priority = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
            if conf_priority.get(confidence, 0) < conf_priority.get(min_confidence, 0):
                min_confidence = confidence

        return min_confidence

    def _determine_strategy(self, impact: ChangeImpact) -> str:
        """Determine verification strategy based on impact."""
        if not impact.changed_files:
            return "fast"

        if impact.overall_risk == "CRITICAL":
            return "full"

        if impact.overall_risk == "HIGH":
            if len(impact.affected_capabilities) <= 2:
                return "selective"
            return "full"

        if impact.overall_risk == "MEDIUM":
            if len(impact.affected_capabilities) <= 3:
                return "selective"
            return "full"

        if impact.overall_risk == "LOW":
            return "selective"

        return "full"


def analyze_changes(changed_files: list[str]) -> ChangeImpact:
    """Convenience function to analyze changed files."""
    engine = ImpactEngine()
    return engine.analyze(changed_files)


def get_ci_targets(impact: ChangeImpact) -> dict[str, Any]:
    """Generate CI targets from change impact for GitHub Actions."""
    targets: dict[str, Any] = {
        "must_run": [],
        "can_skip": [],
        "mutation_targets": [],
        "regression_suites": [],
        "affected_capabilities": [],
        "strategy": impact.strategy,
    }

    for cap in impact.affected_capabilities:
        targets["affected_capabilities"].append(cap.id)
        for v in cap.verification_required:
            targets["must_run"].append(f"{cap.id}:{v}")
        for v in cap.verification_skippable:
            targets["can_skip"].append(f"{cap.id}:{v}")

    for engine in impact.affected_engines:
        targets["mutation_targets"].append(engine.id)

    for cap in impact.affected_capabilities:
        if cap.risk in ("HIGH", "CRITICAL"):
            targets["regression_suites"].append(cap.id)

    return targets
