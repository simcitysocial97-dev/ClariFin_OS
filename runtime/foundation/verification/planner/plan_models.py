"""Verification Plan Model — Program 5 Delivery.

Dataclasses for selective verification planning.
Uses Python stdlib only (dataclasses, no Pydantic).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Literal

from runtime.foundation.verification.planner.impact_rules import (
    classify_change,
    config_changed,
    test_changed,
)


@dataclass(frozen=True, slots=True)
class TestSuiteDecision:
    run: bool
    paths: list[str] = field(default_factory=list)
    reason: str = ""
    schemathesis_tags: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class MutationDecision:
    run: bool
    targets: list[str] = field(default_factory=list)
    test_runner_paths: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass(frozen=True, slots=True)
class VerificationImpact:
    engines: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    routers: list[str] = field(default_factory=list)
    blast_radius: Literal["low", "medium", "high", "full"] = "low"


def _strip_backend(file_path: str) -> str:
    """Convert a repo-root-relative path to a backend-relative path."""
    if file_path.startswith("backend/"):
        return file_path[len("backend/"):]
    return file_path


@dataclass
class VerificationPlan:
    plan_id: str
    generated_at: str
    triggered_by: str
    changed_files: list[str]
    impact: VerificationImpact
    unit_tests: TestSuiteDecision
    property_tests: TestSuiteDecision
    contract_tests: TestSuiteDecision
    mutation: MutationDecision
    integration_tests: TestSuiteDecision
    golden_tests: TestSuiteDecision

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> VerificationPlan:
        data = json.loads(json_str)
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> VerificationPlan:
        return cls(
            plan_id=data["plan_id"],
            generated_at=data["generated_at"],
            triggered_by=data["triggered_by"],
            changed_files=data["changed_files"],
            impact=VerificationImpact(**data["impact"]),
            unit_tests=TestSuiteDecision(**data["unit_tests"]),
            property_tests=TestSuiteDecision(**data["property_tests"]),
            contract_tests=TestSuiteDecision(**data["contract_tests"]),
            mutation=MutationDecision(**data["mutation"]),
            integration_tests=TestSuiteDecision(**data["integration_tests"]),
            golden_tests=TestSuiteDecision(**data["golden_tests"]),
        )

    def to_github_outputs(self) -> dict[str, str]:
        return {
            "run_unit": str(self.unit_tests.run).lower(),
            "run_property": str(self.property_tests.run).lower(),
            "run_contract": str(self.contract_tests.run).lower(),
            "run_mutation": str(self.mutation.run).lower(),
            "run_integration": str(self.integration_tests.run).lower(),
            "run_golden": str(self.golden_tests.run).lower(),
            "affected_engines": json.dumps(self.impact.engines),
            "affected_services": json.dumps(self.impact.services),
            "affected_routers": json.dumps(self.impact.routers),
            "blast_radius": self.impact.blast_radius,
            "unit_paths": " ".join(self.unit_tests.paths),
            "property_paths": " ".join(self.property_tests.paths),
            "contract_paths": " ".join(self.contract_tests.paths),
            "mutation_targets": " ".join(self.mutation.targets),
            "integration_paths": " ".join(self.integration_tests.paths),
            "golden_paths": " ".join(self.golden_tests.paths),
        }

    @classmethod
    def from_changed_files(cls, files: list[str], triggered_by: str = "push") -> VerificationPlan:
        engines: list[str] = []
        services = set()
        routers = set()
        max_blast_rank = 0

        blast_rank = {"low": 0, "medium": 1, "high": 2, "full": 3}

        unit_paths = set()
        property_paths = set()
        contract_paths = set()
        integration_paths = set()
        mutation_targets = set()
        golden_paths = set()

        has_model_change = False
        has_config_change = False
        has_test_change = False

        for f in files:
            classification = classify_change(f)
            ctype = classification.change_type

            if ctype == "engine":
                eng_name = classification.engine_name or "unknown"
                if eng_name not in engines:
                    engines.append(eng_name)
                unit_paths.add(f"tests/unit/engines/{eng_name}/")
                property_paths.add("tests/properties/")
                mutation_targets.add(_strip_backend(f))
                integration_paths.add("tests/integration/")
                max_blast_rank = max(max_blast_rank, blast_rank["medium"])

            elif ctype == "service":
                svc = f.split("/")[2] if len(f.split("/")) > 2 else "unknown"
                services.add(svc)
                unit_paths.add("tests/unit/services/")
                integration_paths.add("tests/integration/")
                max_blast_rank = max(max_blast_rank, blast_rank["medium"])

            elif ctype == "router":
                router = classification.router_name or "unknown"
                routers.add(router)
                contract_paths.add("tests/contract/")
                integration_paths.add("tests/integration/")
                max_blast_rank = max(max_blast_rank, blast_rank["medium"])

            elif ctype == "model":
                has_model_change = True
                max_blast_rank = max(max_blast_rank, blast_rank["high"])

            elif ctype == "test":
                has_test_change = True
                unit_paths.add(_strip_backend(f))
                max_blast_rank = max(max_blast_rank, blast_rank["low"])

            elif ctype == "config":
                has_config_change = True
                max_blast_rank = max(max_blast_rank, blast_rank["full"])

        if has_model_change:
            max_blast_rank = max(max_blast_rank, blast_rank["high"])
            unit_paths.add("tests/unit/")
            property_paths.add("tests/properties/")
            contract_paths.add("tests/contract/")
            integration_paths.add("tests/integration/")
            for f in files:
                if not test_changed(f) and not config_changed(f) and f.startswith("backend/src/") and f.endswith(".py"):
                    mutation_targets.add(_strip_backend(f))

        if has_config_change:
            max_blast_rank = max(max_blast_rank, blast_rank["full"])
            unit_paths.add("tests/unit/")
            property_paths.add("tests/properties/")
            contract_paths.add("tests/contract/")
            integration_paths.add("tests/integration/")
            golden_paths.add("tests/")

        if has_test_change:
            unit_paths.add("tests/unit/")

        blast_radius = "low"
        for name, rank in blast_rank.items():
            if max_blast_rank >= rank:
                blast_radius = name

        plan_id = hashlib.sha256(
            json.dumps(sorted(files)).encode()
        ).hexdigest()[:12]

        return cls(
            plan_id=plan_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            triggered_by=triggered_by,
            changed_files=files,
            impact=VerificationImpact(
                    engines=engines,
                services=sorted(services),
                routers=sorted(routers),
                blast_radius=blast_radius,
            ),
            unit_tests=TestSuiteDecision(
                run=len(unit_paths) > 0,
                paths=sorted(unit_paths),
                reason="Engine/service/model/config changes require unit tests"
                if (engines or services or has_model_change or has_config_change)
                else "No unit tests required",
            ),
            property_tests=TestSuiteDecision(
                run=len(property_paths) > 0,
                paths=sorted(property_paths),
                reason="Engine or model changes require property tests"
                if (engines or has_model_change)
                else "No property tests required",
            ),
            contract_tests=TestSuiteDecision(
                run=len(contract_paths) > 0,
                paths=sorted(contract_paths),
                schemathesis_tags=sorted(routers) if routers else [],
                reason="Router changes require contract tests"
                if routers
                else ("Model changes require contract tests" if has_model_change else "No contract tests required"),
            ),
            mutation=MutationDecision(
                run=len(mutation_targets) > 0,
                targets=sorted(mutation_targets),
                test_runner_paths=sorted(unit_paths),
                reason="Engine or model file changed directly"
                if (engines or has_model_change)
                else "No mutation required",
            ),
            integration_tests=TestSuiteDecision(
                run=len(integration_paths) > 0,
                paths=sorted(integration_paths),
                reason="Service or engine changes may affect integration tests"
                if (services or engines or has_model_change)
                else "No integration tests required",
            ),
            golden_tests=TestSuiteDecision(
                run=len(golden_paths) > 0,
                paths=sorted(golden_paths),
                reason="Config change may affect golden datasets" if has_config_change else "No golden dependency",
            ),
        )