from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.foundation.intelligence.models import AffectedTestPlan
from runtime.foundation.verification.planner.planner import (
    CrossLayerImpactPlanner,
)


@dataclass(frozen=True, slots=True)
class AffectedTestPlanner:
    cross_layer_planner: (
        CrossLayerImpactPlanner | None
    ) = None

    @property
    def _planner(self) -> CrossLayerImpactPlanner:
        if self.cross_layer_planner is not None:
            return self.cross_layer_planner
        return CrossLayerImpactPlanner()

    def build_test_plan(
        self, changed_files: list[str]
    ) -> AffectedTestPlan:
        report = self._planner.analyze_cross_layer_impact(
            changed_files,
        )

        backend_tests = self._resolve_backend_tests(report)
        frontend_tests = self._resolve_frontend_tests(report)
        runtime_tests = self._resolve_runtime_tests(report)
        playwright = self._resolve_playwright_tests(report)
        contracts = self._resolve_contract_tests(report)

        total = (
            len(backend_tests)
            + len(frontend_tests)
            + len(runtime_tests)
            + len(playwright)
            + len(contracts)
        )

        return AffectedTestPlan(
            backend_tests=tuple(sorted(backend_tests)),
            frontend_tests=tuple(sorted(frontend_tests)),
            runtime_tests=tuple(sorted(runtime_tests)),
            playwright=tuple(sorted(playwright)),
            contracts=tuple(sorted(contracts)),
            total_count=total,
        )

    def _resolve_backend_tests(
        self, report: Any
    ) -> list[str]:
        tests: list[str] = []
        for t in report.affected_tests:
            if t.startswith("backend/tests/"):
                tests.append(t)
        for engine in report.affected_engines:
            engine_name = engine.split("/")[-1].replace(".py", "")
            tests.append(
                f"backend/tests/unit/engines/{engine_name}/"
            )
        for service in report.affected_services:
            tests.append(f"backend/tests/unit/services/{service}/")
        for router in report.affected_routers:
            router_name = router.split("/")[-1].replace(".py", "")
            tests.append(
                f"backend/tests/unit/routers/{router_name}/"
            )
        return tests

    def _resolve_frontend_tests(
        self, report: Any
    ) -> list[str]:
        tests: list[str] = []
        for cap in report.affected_capabilities:
            cap_file = f"contract/{cap.lower()}"
            tests.append(cap_file)
        for page in report.affected_pages:
            page_name = page.split("/")[-1].replace(".tsx", "")
            tests.append(f"contract/{page_name}")
        return tests

    def _resolve_runtime_tests(
        self, report: Any
    ) -> list[str]:
        tests: list[str] = []
        for cap in report.affected_capabilities:
            tests.append(f"planner/{cap}")
        for engine in report.affected_engines:
            engine_name = engine.split("/")[-1].replace(".py", "")
            tests.append(f"planner/{engine_name}")
        return tests

    def _resolve_playwright_tests(
        self, report: Any
    ) -> list[str]:
        tests: list[str] = []
        for page in report.affected_pages:
            page_name = page.split("/")[-1].replace(".tsx", "")
            tests.append(f"playwright/{page_name}")
        for ws in report.affected_workspaces:
            tests.append(f"playwright/{ws}")
        return tests

    def _resolve_contract_tests(
        self, report: Any
    ) -> list[str]:
        tests: list[str] = []
        for ep in report.affected_endpoints:
            ep_name = ep.split("/")[-1].replace("{", "").replace("}", "")
            tests.append(f"contract/{ep_name}")
        for cap in report.affected_capabilities:
            tests.append(f"contract/{cap}")
        return tests