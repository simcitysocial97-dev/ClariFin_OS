"""Risk Classification Engine.

Provides lightweight verification metadata with risk levels:
- Critical
- High
- Medium
- Low

Risk classification influences:
- mutation priority
- regression priority
- verification ordering
- GitHub Actions scheduling
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"
SRC_DIR = BACKEND_DIR / "src"


VALID_RISK_LEVELS = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

RISK_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

RISK_WEIGHTS = {
    "CRITICAL": 8,
    "HIGH": 4,
    "MEDIUM": 2,
    "LOW": 1,
}


@dataclass
class RiskEntry:
    """Risk metadata for a single component."""

    id: str
    type: str
    risk: str
    criticality: str = "unknown"
    priority: int = 0
    mutation_priority: int = 0
    regression_priority: int = 0
    verification_order: int = 0
    ci_schedule: str = "default"
    evidence_required: list[str] = field(default_factory=list)
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "risk": self.risk,
            "criticality": self.criticality,
            "priority": self.priority,
            "mutation_priority": self.mutation_priority,
            "regression_priority": self.regression_priority,
            "verification_order": self.verification_order,
            "ci_schedule": self.ci_schedule,
            "evidence_required": self.evidence_required,
            "rationale": self.rationale,
        }


@dataclass
class RiskMap:
    """Complete risk map for the project."""

    entries: list[RiskEntry] = field(default_factory=list)
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [e.to_dict() for e in self.entries],
            "generated_at": self.generated_at,
        }


class RiskEngine:
    """Classifies components by risk level and determines verification priority."""

    def __init__(self) -> None:
        self._entries: list[RiskEntry] = []

    def classify_all(self) -> RiskMap:
        """Classify all registered components by risk."""
        self._entries = []

        self._classify_capabilities()
        self._classify_engines()
        self._classify_services()
        self._classify_routers()
        self._classify_repositories()

        self._entries.sort(key=lambda e: RISK_ORDER.get(e.risk, 99))

        self._assign_priorities()
        self._assign_ci_schedules()

        return RiskMap(
            entries=self._entries,
            generated_at=datetime.now(UTC).isoformat(),
        )

    def _classify_capabilities(self) -> None:
        """Classify capabilities from the registry."""
        from src.verification.runtime.registries import load_capability_registry

        registry = load_capability_registry()
        for cap in registry.get("capabilities", []):
            cap_id = cap.get("id", "")
            risk = cap.get("risk", "LOW")
            criticality = cap.get("criticality", "unknown")

            evidence_required = []
            if cap.get("contracts"):
                evidence_required.append("contract")
            if cap.get("property_tests"):
                evidence_required.append("property")
            if cap.get("golden_datasets"):
                evidence_required.append("golden")
            if cap.get("invariants"):
                evidence_required.append("invariant")
            if cap.get("architecture_tests"):
                evidence_required.append("architecture")

            rationale_parts = []
            if criticality == "high":
                rationale_parts.append("high criticality")
            if risk == "CRITICAL":
                rationale_parts.append("critical risk level")
            if cap.get("dependencies"):
                rationale_parts.append(
                    f"has {len(cap.get('dependencies', []))} downstream dependencies"
                )

            self._entries.append(
                RiskEntry(
                    id=cap_id,
                    type="capability",
                    risk=risk.upper() if risk.islower() else risk,
                    criticality=criticality,
                    evidence_required=evidence_required,
                    rationale=(
                        "; ".join(rationale_parts)
                        if rationale_parts
                        else "auto-classified"
                    ),
                )
            )

    def _classify_engines(self) -> None:
        """Classify engines based on their financial domain."""
        engines_dir = SRC_DIR / "engines"
        if not engines_dir.exists():
            return

        financial_keywords = [
            "cashflow",
            "loan",
            "forecast",
            "interest",
            "amortization",
            "behaviour",
            "behavior",
            "credit_card",
            "credit",
            "balance",
            "debt",
            "investment",
            "reconciliation",
        ]

        for py_file in engines_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            engine_name = py_file.stem
            engine_module = f"src.engines.{py_file.relative_to(engines_dir).with_suffix('').as_posix().replace('/', '.')}"

            is_financial = any(kw in engine_name.lower() for kw in financial_keywords)
            risk = "CRITICAL" if is_financial else "HIGH"

            self._entries.append(
                RiskEntry(
                    id=engine_module,
                    type="engine",
                    risk=risk,
                    criticality="high" if is_financial else "medium",
                    evidence_required=["property", "invariant"],
                    rationale=(
                        "financial_engine" if is_financial else "infrastructure_engine"
                    ),
                )
            )

    def _classify_services(self) -> None:
        """Classify services by their domain."""
        services_dir = SRC_DIR / "services"
        if not services_dir.exists():
            return

        for py_file in services_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            service_name = py_file.stem
            service_module = f"src.services.{py_file.stem}"

            financial_keywords = [
                "loan",
                "credit",
                "behaviour",
                "behavior",
                "forecast",
                "investment",
                "reconciliation",
                "cashflow",
            ]
            is_financial = any(kw in service_name.lower() for kw in financial_keywords)
            risk = "HIGH" if is_financial else "MEDIUM"

            self._entries.append(
                RiskEntry(
                    id=service_module,
                    type="service",
                    risk=risk,
                    criticality="high" if is_financial else "medium",
                    evidence_required=["property"],
                    rationale=(
                        "financial_service"
                        if is_financial
                        else "infrastructure_service"
                    ),
                )
            )

    def _classify_routers(self) -> None:
        """Classify routers by their domain."""
        routers_dir = SRC_DIR / "routers"
        if not routers_dir.exists():
            return

        for py_file in routers_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            router_name = py_file.stem
            router_module = f"src.routers.{py_file.stem}"

            financial_keywords = [
                "loan",
                "credit",
                "behaviour",
                "behavior",
                "forecast",
                "investment",
                "reconciliation",
                "cashflow",
                "account",
            ]
            is_financial = any(kw in router_name.lower() for kw in financial_keywords)
            risk = "MEDIUM" if is_financial else "LOW"

            self._entries.append(
                RiskEntry(
                    id=router_module,
                    type="router",
                    risk=risk,
                    criticality="medium" if is_financial else "low",
                    evidence_required=["contract"],
                    rationale=(
                        "financial_router" if is_financial else "infrastructure_router"
                    ),
                )
            )

    def _classify_repositories(self) -> None:
        """Classify repositories by their domain."""
        repos_dir = SRC_DIR / "repositories"
        if not repos_dir.exists():
            return

        for py_file in repos_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            repo_name = py_file.stem
            repo_module = f"src.repositories.{py_file.stem}"

            financial_keywords = [
                "loan",
                "credit",
                "behaviour",
                "behavior",
                "forecast",
                "investment",
                "reconciliation",
                "cashflow",
                "account",
                "transaction",
            ]
            is_financial = any(kw in repo_name.lower() for kw in financial_keywords)
            risk = "HIGH" if is_financial else "MEDIUM"

            self._entries.append(
                RiskEntry(
                    id=repo_module,
                    type="repository",
                    risk=risk,
                    criticality="high" if is_financial else "medium",
                    evidence_required=["invariant"],
                    rationale=(
                        "financial_repository"
                        if is_financial
                        else "infrastructure_repository"
                    ),
                )
            )

    def _assign_priorities(self) -> None:
        """Assign mutation, regression, and verification priorities."""
        for entry in self._entries:
            base_priority = RISK_WEIGHTS.get(entry.risk, 1)
            entry.mutation_priority = base_priority * 10
            entry.regression_priority = base_priority * 5
            entry.verification_order = base_priority

    def _assign_ci_schedules(self) -> None:
        """Assign CI schedules based on risk."""
        for entry in self._entries:
            if entry.risk == "CRITICAL" or entry.risk == "HIGH":
                entry.ci_schedule = "every_commit"
            elif entry.risk == "MEDIUM":
                entry.ci_schedule = "pull_request"
            else:
                entry.ci_schedule = "nightly"


def classify_all_risks() -> RiskMap:
    """Convenience function to classify all risks."""
    engine = RiskEngine()
    return engine.classify_all()


def get_risk_for_component(component_id: str, component_type: str) -> RiskEntry | None:
    """Get risk entry for a specific component."""
    engine = RiskEngine()
    risk_map = engine.classify_all()
    for entry in risk_map.entries:
        if entry.id == component_id and entry.type == component_type:
            return entry
    return None


def get_mutation_priority_order() -> list[RiskEntry]:
    """Get components sorted by mutation priority (highest first)."""
    engine = RiskEngine()
    risk_map = engine.classify_all()
    return sorted(risk_map.entries, key=lambda e: e.mutation_priority, reverse=True)


def get_regression_priority_order() -> list[RiskEntry]:
    """Get components sorted by regression priority (highest first)."""
    engine = RiskEngine()
    risk_map = engine.classify_all()
    return sorted(risk_map.entries, key=lambda e: e.regression_priority, reverse=True)


def get_verification_order() -> list[RiskEntry]:
    """Get components sorted by verification order (highest priority first)."""
    engine = RiskEngine()
    risk_map = engine.classify_all()
    return sorted(risk_map.entries, key=lambda e: e.verification_order, reverse=True)
