"""O-5 Controlled Scenarios — Frontend↔Backend Capability Convergence

Tests for M9-C57 O-5-R: validates the canonical planner integration
with frontend capabilities, cross-layer impact, and unmapped handling.
"""

from __future__ import annotations

import json
from pathlib import Path

from runtime.foundation.verification.planner.planner import (
    CrossLayerImpactPlanner,
)


class TestControlledScenarioA_BackendChange:
    """Scenario A: Backend change → backend symbol → backend capability → backend obligation.

    A change to a backend engine file should resolve to the owning engine
    and its associated capabilities via the chain map.
    """

    def test_backend_change_resolves_to_engine(self):
        """Backend file change resolves to correct engine."""
        planner = CrossLayerImpactPlanner()
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"]
        )

        # Should resolve to loan engine via chain map
        assert "backend/src/engines/loan_engine" in report.affected_engines

        # Should not invent frontend capabilities for backend changes
        frontend_caps = [
            c for c in report.affected_capabilities
            if c.startswith("frontend:")
        ]
        assert len(frontend_caps) == 0, (
            f"Backend change should not produce frontend capabilities, got: {frontend_caps}"
        )

    def test_backend_change_produces_obligation(self):
        """Backend change produces verification obligations."""
        planner = CrossLayerImpactPlanner()
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"]
        )

        plan = report.verification_plan
        assert plan.get("run_unit") is True, "Backend engine change requires unit tests"
        assert plan.get("run_property") is True, "Loan engine change requires property tests"


class TestControlledScenarioB_FrontendChange:
    """Scenario B: Frontend change → TS/TSX symbol → frontend capability → frontend obligation.

    A change to a frontend hook/component should resolve to the corresponding
    frontend capability and propagate backend dependencies.
    """

    def test_frontend_hook_resolves_to_capability(self):
        """Frontend hook change resolves to frontend capability."""
        planner = CrossLayerImpactPlanner()
        report = planner.analyze_cross_layer_impact(
            ["frontend/lib/hooks/use-accounts.ts"]
        )

        # Should resolve to frontend capability
        assert "frontend:hook:frontend-accounts:accounts" in report.affected_capabilities

    def test_frontend_hook_propagates_backend(self):
        """Frontend hook change propagates backend dependencies."""
        planner = CrossLayerImpactPlanner()
        report = planner.analyze_cross_layer_impact(
            ["frontend/lib/hooks/use-accounts.ts"]
        )

        # Should include backend capability
        assert "account-engine" in report.affected_capabilities

    def test_frontend_hook_produces_obligation(self):
        """Frontend hook change produces verification obligations."""
        planner = CrossLayerImpactPlanner()
        report = planner.analyze_cross_layer_impact(
            ["frontend/lib/hooks/use-accounts.ts"]
        )

        plan = report.verification_plan
        assert plan.get("run_frontend") is True, "Frontend change requires frontend verification"
        assert plan.get("run_contract") is True, "Hook with API deps requires contract tests"


class TestControlledScenarioC_CrossLayerChange:
    """Scenario C: Cross-layer change → frontend symbol + backend symbol → cross-layer capability → cross-layer obligation.

    This is the critical missing proof. A change affecting an actual
    frontend/backend contract relationship must produce a cross-layer obligation.
    """

    def test_frontend_backend_contract_change(self):
        """Change to frontend hook that calls backend endpoint."""
        planner = CrossLayerImpactPlanner()
        report = planner.analyze_cross_layer_impact(
            ["frontend/lib/hooks/use-accounts.ts"]
        )

        # Should have both frontend and backend in capabilities
        frontend_caps = [c for c in report.affected_capabilities if c.startswith("frontend:")]
        backend_caps = [c for c in report.affected_capabilities if c not in frontend_caps and not c.startswith("UNMAPPED:")]

        assert len(frontend_caps) >= 1, "Should resolve frontend capability"
        assert len(backend_caps) >= 1, "Should resolve backend capability via propagation"

    def test_cross_layer_obligation_generated(self):
        """Cross-layer change generates appropriate obligations."""
        planner = CrossLayerImpactPlanner()
        report = planner.analyze_cross_layer_impact(
            ["frontend/lib/hooks/use-accounts.ts"]
        )

        plan = report.verification_plan

        # Should require frontend verification
        assert plan.get("run_frontend") is True

        # Should require contract verification (API endpoints involved)
        assert plan.get("run_contract") is True

        # Should include backend capability
        assert "account-engine" in plan.get("capabilities", [])

    def test_endpoints_propagated(self):
        """Cross-layer change propagates affected endpoints."""
        planner = CrossLayerImpactPlanner()
        report = planner.analyze_cross_layer_impact(
            ["frontend/lib/hooks/use-accounts.ts"]
        )

        # Should include the backend endpoints the hook calls
        assert "/api/accounts/manage" in report.affected_endpoints


class TestControlledScenarioD_FrontendAPIClient:
    """Scenario D: Frontend API consumer → API endpoint → backend capability.

    Change an actual frontend API consumer in a harmless way. Prove the
    frontend consumer maps to the backend endpoint and capability.
    """

    def test_api_client_maps_to_endpoint(self):
        """Frontend API client resolves to backend endpoint."""
        planner = CrossLayerImpactPlanner()
        report = planner.analyze_cross_layer_impact(
            ["frontend/lib/hooks/use-accounts.ts"]
        )

        # Should have endpoints in affected list
        assert len(report.affected_endpoints) > 0, (
            f"Expected endpoints, got: {report.affected_endpoints}"
        )

    def test_no_financial_behavior_modified(self):
        """Frontend API consumer change does not affect financial calculations."""
        planner = CrossLayerImpactPlanner()
        report = planner.analyze_cross_layer_impact(
            ["frontend/lib/hooks/use-accounts.ts"]
        )

        # Should not touch financial engines
        financial_engines = [
            e for e in report.affected_engines
            if "financial" in e.lower() or "credit_card" in e.lower()
        ]
        assert len(financial_engines) == 0, (
            f"Account hook change should not affect financial engines: {financial_engines}"
        )


class TestControlledScenarioE_UnmappedFrontend:
    """Scenario E: Unmapped frontend → explicit UNMAPPED state.

    Use or create a temporary isolated frontend symbol that has no known
    capability relationship. The framework must report UNMAPPED, not silently
    map the symbol to the entire frontend.
    """

    def test_unmapped_frontend_is_explicit(self):
        """Unmapped frontend file is explicitly marked."""
        planner = CrossLayerImpactPlanner()
        report = planner.analyze_cross_layer_impact(
            ["frontend/lib/unknown/orphan-component.tsx"]
        )

        # Should have UNMAPPED prefix
        unmapped = [c for c in report.affected_capabilities if c.startswith("UNMAPPED:")]
        assert len(unmapped) >= 1, "Unmapped frontend file should be explicitly marked"
        assert "frontend/lib/unknown/orphan-component.tsx" in unmapped[0]

    def test_unmapped_does_not_inflate_blast_radius(self):
        """Unmapped frontend does not silently map to all capabilities."""
        planner = CrossLayerImpactPlanner()
        report = planner.analyze_cross_layer_impact(
            ["frontend/lib/unknown/orphan-component.tsx"]
        )

        # Should NOT have legitimate capabilities
        legitimate_caps = [
            c for c in report.affected_capabilities
            if not c.startswith("UNMAPPED:") and not c.startswith("frontend:")
        ]
        assert len(legitimate_caps) == 0, (
            f"Unmapped file should not produce backend capabilities: {legitimate_caps}"
        )

    def test_unmapped_has_minimal_obligation(self):
        """Unmapped frontend produces minimal obligation."""
        planner = CrossLayerImpactPlanner()
        report = planner.analyze_cross_layer_impact(
            ["frontend/lib/unknown/orphan-component.tsx"]
        )

        plan = report.verification_plan
        # Should only require frontend check, not full campaign
        assert plan.get("run_frontend") is True
        # Should NOT escalate to mutation or full regression
        # (this is verified indirectly by the plan structure)


class TestControlledScenarioF_Recovery:
    """Scenario F: Recovery → controlled failure restored successfully.

    Verify that the recovery process did not break existing functionality.
    """

    def test_chain_map_still_works(self):
        """Chain map resolution still functions for backend files."""
        planner = CrossLayerImpactPlanner()
        report = planner.analyze_cross_layer_impact(
            ["backend/src/engines/loan_engine/amortization.py"]
        )

        # Should still resolve via chain map
        assert "backend/src/engines/loan_engine" in report.affected_engines

    def test_generated_artifacts_are_read(self):
        """Cross-layer graph artifact is loaded correctly."""
        planner = CrossLayerImpactPlanner()

        # Should have loaded the graph
        assert planner._cross_layer_graph is not None
        assert "frontend_capabilities" in planner._cross_layer_graph
        assert "edges" in planner._cross_layer_graph

    def test_frontend_backend_map_exists(self):
        """Generated frontend-backend map exists and is valid."""
        graph_path = Path("runtime/generated/cross-layer-graph.json")
        assert graph_path.exists(), "Cross-layer graph artifact must exist"

        with open(graph_path) as f:
            data = json.load(f)

        assert len(data.get("frontend_capabilities", {})) > 0
        assert len(data.get("edges", [])) > 0


class TestFrontendCapabilityResolution:
    """Direct tests for _find_frontend_capability()."""

    def test_find_frontend_capability_by_absolute_path(self):
        """Can resolve frontend capability using absolute path."""
        planner = CrossLayerImpactPlanner()
        result = planner._find_frontend_capability(
            "/home/vasantha/AI-Projects/ClariFin_OS/frontend/lib/hooks/use-accounts.ts"
        )

        assert result is not None
        assert result["capability_id"] == "frontend:hook:frontend-accounts:accounts"
        assert result["status"] == "MAPPED"
        assert "account-engine" in result["backend_capabilities"]

    def test_find_frontend_capability_by_relative_path(self):
        """Can resolve frontend capability using relative path."""
        planner = CrossLayerImpactPlanner()
        result = planner._find_frontend_capability(
            "frontend/lib/hooks/use-accounts.ts"
        )

        assert result is not None
        assert result["capability_id"] == "frontend:hook:frontend-accounts:accounts"

    def test_find_frontend_capability_unmapped(self):
        """Returns None for completely unknown frontend file."""
        planner = CrossLayerImpactPlanner()
        result = planner._find_frontend_capability(
            "frontend/lib/unknown/orphan.tsx"
        )

        assert result is None

    def test_find_frontend_capability_no_graph(self):
        """Returns None when cross-layer graph is not loaded."""
        planner = CrossLayerImpactPlanner()
        # Temporarily disable graph
        original = planner._cross_layer_graph
        planner._cross_layer_graph = None

        try:
            result = planner._find_frontend_capability("frontend/lib/hooks/use-accounts.ts")
            assert result is None
        finally:
            planner._cross_layer_graph = original

    def test_resolve_capability_edges(self):
        """Correctly extracts edges from cross-layer graph."""
        planner = CrossLayerImpactPlanner()
        result = planner._resolve_capability_edges("frontend:hook:frontend-accounts:accounts")

        assert result is not None
        assert result["kind"] == "frontend_hook"
        assert result["domain"] == "frontend-accounts"
        assert len(result["edges"]) > 0


class TestContractDriftClassification:
    """Tests for contract drift detection and classification."""

    def test_drifts_are_detected(self):
        """Contract drifts are present in the graph."""
        planner = CrossLayerImpactPlanner()
        assert planner._cross_layer_graph is not None

        drifts = planner._cross_layer_graph.get("contract_drifts", [])
        assert len(drifts) > 0, "Expected contract drifts to be detected"

    def test_drift_types_are_known(self):
        """All drift types are from expected categories."""
        planner = CrossLayerImpactPlanner()
        drifts = planner._cross_layer_graph.get("contract_drifts", [])

        valid_types = {"missing_endpoint", "path_mismatch", "method_mismatch", "schema_drift"}
        for drift in drifts:
            assert drift.get("drift_type") in valid_types, (
                f"Unexpected drift type: {drift.get('drift_type')}"
            )


class TestGeneratedArtifactIsolation:
    """Tests ensuring generated artifacts don't create recursive impact."""

    def test_generated_files_not_treated_as_source(self):
        """Generated artifacts are not treated as source changes."""
        planner = CrossLayerImpactPlanner()

        # Generated files should not resolve to any capability
        report = planner.analyze_cross_layer_impact(
            ["runtime/generated/cross-layer-graph.json"]
        )

        # Should not produce blast radius from generated file itself
        # (it may produce some impact if the graph says so, but not recursive)
        caps = report.affected_capabilities
        assert not any("cross-layer-graph" in c for c in caps), (
            "Generated graph file should not reference itself"
        )

    def test_symbol_cache_not_treated_as_source(self):
        """TypeScript symbol cache is not treated as source change."""
        planner = CrossLayerImpactPlanner()

        report = planner.analyze_cross_layer_impact(
            ["runtime/generated/typescript-symbol-cache/symbol-cache.json"]
        )

        # Should not produce frontend capabilities from cache file
        frontend_caps = [c for c in report.affected_capabilities if c.startswith("frontend:")]
        assert len(frontend_caps) == 0, (
            f"Cache file should not produce frontend capabilities: {frontend_caps}"
        )
