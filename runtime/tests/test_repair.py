"""Tests for RepairGuidance — Program 8."""

from __future__ import annotations

import pytest

from runtime.foundation.intelligence.repair import (
    RepairGuidance,
    build_repair_guidance,
)


SAMPLE_CHAIN = {
    "source": "backend/src/engines/loan_engine/amortization.py",
    "engine": "backend/src/engines/loan_engine/amortization.py",
    "services": ["LoanService"],
    "routers": ["backend/src/routers/loans.py"],
    "endpoints": ["GET /api/loans/{id}/schedule"],
    "capabilities": ["useLoansCapability"],
    "mappers": ["loansMapper"],
    "viewModels": ["LoansViewModel"],
    "workspace": ["LoansWorkspace"],
    "components": ["AmortizationTable"],
    "tests": ["backend/tests/unit/loan/test_amortization.py"],
    "graphRenderers": [],
}


class TestRepairGuidance:
    def test_build_repair_guidance_from_chain(self) -> None:
        guidance = build_repair_guidance([SAMPLE_CHAIN])
        assert len(guidance.suggestions) > 0

    def test_build_repair_guidance_returns_repair_guidance(
        self,
    ) -> None:
        guidance = build_repair_guidance([SAMPLE_CHAIN])
        assert isinstance(guidance, RepairGuidance)

    def test_for_capability_finds_suggestions(self) -> None:
        guidance = build_repair_guidance([SAMPLE_CHAIN])
        results = guidance.for_capability("useLoansCapability")
        assert len(results) > 0
        assert all(s.change_type == "capability" for s in results)

    def test_for_endpoint_finds_suggestions(self) -> None:
        guidance = build_repair_guidance([SAMPLE_CHAIN])
        results = guidance.for_endpoint("GET /api/loans/{id}/schedule")
        assert len(results) > 0
        assert all(s.change_type == "endpoint" for s in results)

    def test_for_router_finds_suggestions(self) -> None:
        guidance = build_repair_guidance([SAMPLE_CHAIN])
        results = guidance.for_router("backend/src/routers/loans.py")
        assert len(results) > 0
        assert all(s.change_type == "router" for s in results)

    def test_for_mapper_finds_suggestions(self) -> None:
        guidance = build_repair_guidance([SAMPLE_CHAIN])
        results = guidance.for_mapper("loansMapper")
        assert len(results) > 0
        assert all(s.change_type == "mapper" for s in results)

    def test_for_view_model_finds_suggestions(self) -> None:
        guidance = build_repair_guidance([SAMPLE_CHAIN])
        results = guidance.for_view_model("LoansViewModel")
        assert len(results) > 0
        assert all(s.change_type == "view_model" for s in results)

    def test_for_workspace_finds_suggestions(self) -> None:
        guidance = build_repair_guidance([SAMPLE_CHAIN])
        results = guidance.for_workspace("LoansWorkspace")
        assert len(results) > 0
        assert all(s.change_type == "workspace" for s in results)

    def test_for_component_finds_suggestions(self) -> None:
        guidance = build_repair_guidance([SAMPLE_CHAIN])
        results = guidance.for_component("AmortizationTable")
        assert len(results) > 0
        assert all(s.change_type == "component" for s in results)

    def test_all_suggestions_returns_all(self) -> None:
        guidance = build_repair_guidance([SAMPLE_CHAIN])
        all_s = guidance.all_suggestions()
        assert len(all_s) == len(guidance.suggestions)

    def test_empty_chain_produces_no_suggestions(self) -> None:
        guidance = build_repair_guidance([])
        assert len(guidance.suggestions) == 0

    def test_suggestion_has_required_fields(self) -> None:
        guidance = build_repair_guidance([SAMPLE_CHAIN])
        for s in guidance.suggestions:
            assert s.target != ""
            assert s.change_type != ""
            assert s.reason != ""
            assert s.guidance != ""
            assert s.dependency_reference != ""

    def test_suggestions_are_immutable(self) -> None:
        guidance = build_repair_guidance([SAMPLE_CHAIN])
        with pytest.raises(AttributeError):
            guidance.suggestions = ()  # type: ignore[misc]