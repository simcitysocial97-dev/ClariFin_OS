"""Snapshot Tests — Program 7B.5

Deterministic snapshot tests for cross-layer map, verification plan,
and verification report outputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch


from runtime.foundation.verification.models import VerificationScope, VerificationStatus
from runtime.foundation.verification.planner import (
    CrossLayerImpactPlanner,
    VerificationPlanner,
)
from runtime.foundation.verification.orchestrator import VerificationOrchestrator


import re


SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def _write_snapshot(name: str, data) -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOT_DIR / f"{name}.json"
    if isinstance(data, dict):
        path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    else:
        path.write_text(str(data), encoding="utf-8")
    return path


def _read_snapshot(name: str):
    path = SNAPSHOT_DIR / f"{name}.json"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _sanitize_markdown(text: str) -> str:
    text = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+\+\d{2}:\d{2}", "2026-01-01T00:00:00+00:00", text)
    text = re.sub(r"plan-\d{8}-\d{6}", "plan-20260101-000000", text)
    return text


class TestSnapshots:
    """Deterministic snapshot tests."""

    def test_cross_layer_map_snapshot(self, tmp_path: Path):
        map_data = {
            "backend/src/engines/loan_engine/amortization.py": {
                "engine": "backend/src/engines/loan_engine/amortization.py",
                "services": ["LoanService"],
                "routers": ["backend/src/routers/loans.py"],
                "endpoints": ["GET /api/loans/{loan_id}/schedule"],
                "capabilities": ["useLoansCapability"],
                "mappers": ["loansMapper"],
                "viewModels": ["LoansViewModel"],
                "pages": ["app/loans/page.tsx"],
                "workspace": ["LoansWorkspace"],
                "components": ["AmortizationTable"],
                "tests": [
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/contract/generated/test_loans.py",
                ],
                "graphRenderers": [],
            }
        }
        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(map_data, indent=2), encoding="utf-8")

        planner = CrossLayerImpactPlanner(map_path=map_path)
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"]
        )
        result = report.to_dict()

        snapshot = _read_snapshot("cross-layer-map")
        if snapshot is None:
            _write_snapshot("cross-layer-map", result)
            snapshot = _read_snapshot("cross-layer-map")

        assert result == snapshot

    def test_verification_plan_snapshot(self, isolated_registry):
        planner = VerificationPlanner(registry=isolated_registry)
        from runtime.foundation.verification.planner.planner import PlanningContext

        context = PlanningContext(
            changed_files=["backend/src/engines/loan_engine/amortization.py"],
            requested_scope=VerificationScope.BACKEND,
            force_scope=VerificationScope.BACKEND,
            include_dependencies=True,
            include_dependents=False,
            max_depth=3,
        )
        with patch(
            "runtime.foundation.verification.planner.planner.datetime"
        ) as mock_dt:
            import datetime as dt
            mock_dt.utcnow.return_value = dt.datetime(2026, 1, 1, 0, 0, 0)
            mock_dt.datetime = dt.datetime
            plan = planner.plan(context)

        snapshot_data = {
            "scope": plan.scope.value,
            "target_count": len(plan.targets),
            "step_count": len(plan.steps),
            "target_ids": sorted([t.id for t in plan.targets]),
            "step_ids": sorted([s.id for s in plan.steps]),
            "metadata_keys": sorted(plan.metadata.keys()),
        }

        snapshot = _read_snapshot("verification-plan")
        if snapshot is None:
            _write_snapshot("verification-plan", snapshot_data)
            snapshot = _read_snapshot("verification-plan")

        assert snapshot_data == snapshot

    def test_verification_report_snapshot(self, tmp_path: Path):
        map_data = {
            "backend/src/engines/loan_engine/amortization.py": {
                "engine": "backend/src/engines/loan_engine/amortization.py",
                "services": ["LoanService"],
                "routers": ["backend/src/routers/loans.py"],
                "endpoints": ["GET /api/loans/{loan_id}/schedule"],
                "capabilities": ["useLoansCapability"],
                "mappers": ["loansMapper"],
                "viewModels": ["LoansViewModel"],
                "pages": ["app/loans/page.tsx"],
                "workspace": ["LoansWorkspace"],
                "components": ["AmortizationTable"],
                "tests": [
                    "backend/tests/unit/engines/loan/test_amortization.py",
                    "backend/tests/contract/generated/test_loans.py",
                ],
                "graphRenderers": [],
            }
        }
        map_path = tmp_path / "cross-layer-map.json"
        map_path.write_text(json.dumps(map_data, indent=2), encoding="utf-8")

        with patch(
            "runtime.foundation.verification.orchestrator._find_repo_root",
            return_value=tmp_path,
        ), patch(
            "runtime.foundation.verification.orchestrator.VERIFICATION_REPORT_PATH",
            tmp_path / "verification-report.md",
        ), patch(
            "runtime.foundation.verification.orchestrator.VERIFICATION_CACHE_PATH",
            tmp_path / "verification-cache.json",
        ), patch(
            "runtime.foundation.verification.orchestrator.datetime"
        ) as mock_dt:
            import datetime as dt
            mock_dt.now.return_value = dt.datetime(2026, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc)
            mock_dt.timezone = dt.timezone
            orchestrator = VerificationOrchestrator(repo_root=tmp_path, map_path=map_path)
            orchestrator._changed_files = ["backend/src/engines/loan_engine/amortization.py"]
            orchestrator.analyze_cross_layer()
            plan = orchestrator.generate_plan(scope=VerificationScope.QUICK)
            new_steps = []
            for step in plan.steps:
                new_steps.append(
                    step.__class__(
                        id=step.id,
                        target=step.target,
                        order=step.order,
                        command=None,
                        workflow=step.workflow,
                        script=step.script,
                        estimated_duration_seconds=step.estimated_duration_seconds,
                        required_evidence=step.required_evidence,
                        dependencies=step.dependencies,
                        status=VerificationStatus.SKIPPED,
                        metadata=step.metadata,
                    )
                )
            from dataclasses import replace
            plan = replace(plan, steps=new_steps)
            orchestrator._plan = plan
            orchestrator._results = [
                type("R", (), {
                    "task_id": s.id,
                    "command": s.command or "no-op",
                    "status": VerificationStatus.SKIPPED,
                    "duration_seconds": 0.0,
                })()
                for s in plan.steps
            ]

            report = orchestrator.generate_report()
            md = _sanitize_markdown(report.to_markdown())
            snapshot = _read_snapshot("verification-report")
            if snapshot is None:
                _write_snapshot("verification-report", md)
                snapshot = _read_snapshot("verification-report")

            assert md == snapshot
