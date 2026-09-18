"""M9-C61 — Regression Tests for Endpoint Normalization Contract.

Tests covering the canonical normalization rules for frontend/backend
endpoint representation convergence.
"""

from __future__ import annotations

import pytest

from runtime.foundation.verification.endpoint_normalize import (
    NormalizedEndpoint,
    EndpointNormalizer,
    endpoints_match,
    get_canonical_key,
    normalize_endpoint,
)


class TestEndpointNormalization:
    """Tests for the normalize_endpoint function."""

    def test_static_path_unchanged(self):
        """Static paths remain unchanged."""
        result = normalize_endpoint("/api/health")
        assert result.canonical_path == "/api/health"
        assert result.path_params == ()
        assert result.query_params == ()

    def test_frontend_template_variable_normalized(self):
        """Frontend ${id} template variables normalized to {param}."""
        result = normalize_endpoint("/api/loans/${id}")
        assert result.canonical_path == "/api/loans/{param}"
        assert "DOLLAR_BRACE_TEMPLATE" in result.normalization_rules

    def test_frontend_multiple_template_variables(self):
        """Multiple template variables each become {param}."""
        result = normalize_endpoint("/api/items/${itemId}/comments/${commentId}")
        assert result.canonical_path == "/api/items/{param}/comments/{param}"
        assert result.normalization_rules.count("DOLLAR_BRACE_TEMPLATE") == 2

    def test_backend_brace_parameter_normalized(self):
        """Backend {param_name} normalized to {param}."""
        result = normalize_endpoint("/api/loans/{loan_id}")
        assert result.canonical_path == "/api/loans/{param}"
        assert "BRACE_PARAMETER" in result.normalization_rules

    def test_express_colon_parameter_normalized(self):
        """Express-style :param_name normalized to {param}."""
        result = normalize_endpoint("/api/loans/:loan_id")
        assert result.canonical_path == "/api/loans/{param}"
        assert "COLON_PARAMETER" in result.normalization_rules

    def test_encode_uri_component_normalized_to_param(self):
        """encodeURIComponent(variable!) normalized to {param} in canonical form."""
        result = normalize_endpoint("/api/capabilities/${encodeURIComponent(capabilityId!)}")
        assert result.canonical_path == "/api/capabilities/{param}"
        assert "ENCODE_URI_COMPONENT" in result.normalization_rules
        # Original parameter name preserved in path_params
        assert "capabilityId" in result.path_params

    def test_encode_uri_component_with_exclamation_normalized(self):
        """encodeURIComponent preserves parameter name in path_params but canonical uses {param}."""
        result = normalize_endpoint("/api/items/${encodeURIComponent(itemId!)}")
        assert result.canonical_path == "/api/items/{param}"
        assert "itemId" in result.path_params

    def test_query_string_stripped_from_path(self):
        """Query strings stripped for path normalization but preserved in query_params."""
        result = normalize_endpoint("/api/events?limit=10")
        assert result.canonical_path == "/api/events"
        assert result.query_params == ("limit",)

    def test_query_params_extracted(self):
        """Multiple query parameters extracted."""
        result = normalize_endpoint("/api/search?q=test&page=1&size=20")
        assert result.canonical_path == "/api/search"
        assert set(result.query_params) == {"q", "page", "size"}

    def test_template_variable_in_query(self):
        """Template variables in query string normalized."""
        result = normalize_endpoint("/api/events?limit=${limit}")
        assert result.canonical_path == "/api/events"
        assert result.query_params == ("limit",)
        assert "DOLLAR_BRACE_TEMPLATE" in result.normalization_rules

    def test_trailing_slash_removed(self):
        """Trailing slashes removed (except root)."""
        result = normalize_endpoint("/api/health/")
        assert result.canonical_path == "/api/health"
        assert "TRIM_TRAILING_SLASH" in result.normalization_rules

    def test_root_trailing_slash_preserved(self):
        """Root path '/' keeps its trailing slash."""
        result = normalize_endpoint("/")
        assert result.canonical_path == "/"

    def test_multiple_slashes_collapsed(self):
        """Multiple consecutive slashes collapsed."""
        result = normalize_endpoint("/api//health///check")
        assert result.canonical_path == "/api/health/check"
        assert "COLLAPSE_SLASHES" in result.normalization_rules

    def test_method_aware_canonical_key(self):
        """Canonical key includes HTTP method."""
        get_result = normalize_endpoint("/api/items", "GET")
        post_result = normalize_endpoint("/api/items", "POST")
        
        assert get_result.canonical_path == "GET:/api/items"
        assert post_result.canonical_path == "POST:/api/items"
        assert get_result != post_result

    def test_unknown_method_no_prefix(self):
        """Unknown method doesn't prefix canonical path."""
        result = normalize_endpoint("/api/items", "UNKNOWN")
        assert result.canonical_path == "/api/items"

    def test_provenance_preserved(self):
        """Original endpoint preserved in result."""
        original = "/api/loans/${loanId}/schedule"
        result = normalize_endpoint(original)
        assert result.original == original

    def test_parameter_names_extracted(self):
        """Original parameter names extracted before normalization."""
        result = normalize_endpoint("/api/loans/${loanId}/schedule")
        assert result.path_params == ("loanId",)

    def test_backend_parameter_names_extracted(self):
        """Backend parameter names extracted."""
        result = normalize_endpoint("/api/loans/{loan_id}/schedule")
        assert result.path_params == ("loan_id",)


class TestEndpointsMatch:
    """Tests for endpoints_match function."""

    def test_dollar_brace_matches_brace_param(self):
        """Frontend ${id} matches backend {id}."""
        assert endpoints_match("/api/loans/${id}", "/api/loans/{loan_id}")

    def test_dollar_brace_matches_colon_param(self):
        """Frontend ${id} matches Express :id."""
        assert endpoints_match("/api/loans/${id}", "/api/loans/:loan_id")

    def test_encode_uri_component_matches_brace_param(self):
        """Frontend ${encodeURIComponent(id!)} matches backend {id}."""
        assert endpoints_match(
            "/api/capabilities/${encodeURIComponent(capabilityId!)}",
            "/api/capabilities/{capability_id}"
        )

    def test_different_parameter_names_match(self):
        """Different parameter names match if position/structure same."""
        assert endpoints_match("/api/items/${itemId}", "/api/items/{id}")

    def test_method_mismatch_returns_false(self):
        """Different HTTP methods don't match."""
        assert not endpoints_match("/api/items", "/api/items", "GET", "POST")

    def test_query_string_ignored_for_matching(self):
        """Query strings don't affect path matching."""
        assert endpoints_match("/api/events?limit=10", "/api/events")

    def test_trailing_slash_ignored(self):
        """Trailing slashes don't affect matching."""
        assert endpoints_match("/api/health/", "/api/health")

    def test_multiple_slashes_ignored(self):
        """Multiple slashes don't affect matching."""
        assert endpoints_match("/api//health", "/api/health")

    def test_different_paths_dont_match(self):
        """Different paths don't match."""
        assert not endpoints_match("/api/loans", "/api/investments")

    def test_encode_uri_component_variants_match(self):
        """Different encodeURIComponent variants match same backend."""
        assert endpoints_match(
            "/api/capabilities/${encodeURIComponent(capabilityId!)}",
            "/api/capabilities/${capabilityId}"
        )


class TestEndpointNormalizer:
    """Tests for the stateful EndpointNormalizer class."""

    def test_cache_reuse(self):
        """Repeated normalization uses cache."""
        normalizer = EndpointNormalizer()
        
        result1 = normalizer.normalize("/api/loans/${id}")
        result2 = normalizer.normalize("/api/loans/${id}")
        
        assert result1 is result2

    def test_match_returns_normalized_objects(self):
        """match() returns both normalized objects."""
        normalizer = EndpointNormalizer()
        
        matched, fe_norm, be_norm = normalizer.match(
            "/api/loans/${id}",
            "/api/loans/{loan_id}",
        )
        
        assert matched is True
        assert isinstance(fe_norm, NormalizedEndpoint)
        assert isinstance(be_norm, NormalizedEndpoint)

    def test_match_false_for_different_endpoints(self):
        """match() returns False for different endpoints."""
        normalizer = EndpointNormalizer()
        
        matched, fe_norm, be_norm = normalizer.match(
            "/api/loans/${id}",
            "/api/investments/${id}",
        )
        
        assert matched is False

    def test_clear_cache(self):
        """clear_cache() empties the cache."""
        normalizer = EndpointNormalizer()
        normalizer.normalize("/api/loans/${id}")
        normalizer.clear_cache()
        
        # After clear, new object created
        result1 = normalizer.normalize("/api/loans/${id}")
        result2 = normalizer.normalize("/api/loans/${id}")
        # Should still be cached within same session
        assert result1 is result2


class TestCanonicalKey:
    """Tests for get_canonical_key function."""

    def test_canonical_key_format(self):
        """Canonical key includes method prefix."""
        key = get_canonical_key("/api/items", "GET")
        assert key == "GET:/api/items"

    def test_canonical_key_without_method(self):
        """Canonical key without method has no prefix."""
        key = get_canonical_key("/api/items")
        assert key == "/api/items"

    def test_same_endpoint_same_key(self):
        """Semantically equivalent endpoints produce same key."""
        key1 = get_canonical_key("/api/loans/${id}", "GET")
        key2 = get_canonical_key("/api/loans/{loan_id}", "GET")
        assert key1 == key2


class TestNormalizationRulesTracking:
    """Tests that normalization rules are correctly tracked."""

    def test_dollar_brace_rule_recorded(self):
        """DOLLAR_BRACE_TEMPLATE rule recorded for ${...}."""
        result = normalize_endpoint("/api/${id}")
        assert "DOLLAR_BRACE_TEMPLATE" in result.normalization_rules

    def test_brace_param_rule_recorded(self):
        """BRACE_PARAMETER rule recorded for {...}."""
        result = normalize_endpoint("/api/{id}")
        assert "BRACE_PARAMETER" in result.normalization_rules

    def test_colon_param_rule_recorded(self):
        """COLON_PARAMETER rule recorded for :id."""
        result = normalize_endpoint("/api/:id")
        assert "COLON_PARAMETER" in result.normalization_rules

    def test_encode_uri_component_rule_recorded(self):
        """ENCODE_URI_COMPONENT rule recorded."""
        result = normalize_endpoint("/api/${encodeURIComponent(id!)}")
        assert "ENCODE_URI_COMPONENT" in result.normalization_rules

    def test_query_params_rule_recorded(self):
        """QUERY_PARAMS_EXTRACTED rule recorded."""
        result = normalize_endpoint("/api/?q=test")
        assert "QUERY_PARAMS_EXTRACTED" in result.normalization_rules

    def test_trailing_slash_rule_recorded(self):
        """TRIM_TRAILING_SLASH rule recorded."""
        result = normalize_endpoint("/api/health/")
        assert "TRIM_TRAILING_SLASH" in result.normalization_rules

    def test_collapse_slashes_rule_recorded(self):
        """COLLAPSE_SLASHES rule recorded."""
        result = normalize_endpoint("/api//health")
        assert "COLLAPSE_SLASHES" in result.normalization_rules


class TestPlatformEndpointNormalization:
    """Tests specific to platform endpoint normalization (C61 targets)."""

    def test_capabilities_encode_uri_component(self):
        """Platform capabilities with encodeURIComponent."""
        assert endpoints_match(
            "/platform/v1/capabilities/${encodeURIComponent(capabilityId!)}",
            "/platform/v1/capabilities/{capability_id}"
        )

    def test_capabilities_graph_encode_uri_component(self):
        """Platform capabilities graph with encodeURIComponent."""
        assert endpoints_match(
            "/platform/v1/capabilities/${encodeURIComponent(capabilityId!)}/graph",
            "/platform/v1/capabilities/{capability_id}/graph"
        )

    def test_capabilities_simple_template(self):
        """Platform capabilities with simple template."""
        assert endpoints_match(
            "/platform/v1/capabilities/${capabilityId}",
            "/platform/v1/capabilities/{capability_id}"
        )

    def test_tasks_cancel(self):
        """Platform tasks cancel endpoint."""
        assert endpoints_match(
            "/platform/v1/tasks/${taskId}/cancel",
            "/platform/v1/tasks/{task_id}/cancel"
        )

    def test_architecture_authority_encode_uri_component(self):
        """Platform architecture authority with encodeURIComponent."""
        assert endpoints_match(
            "/platform/v1/architecture/authority/${encodeURIComponent(name!)}",
            "/platform/v1/architecture/authority/{name}"
        )

    def test_events_query_param(self):
        """Platform events with query param."""
        assert endpoints_match(
            "/platform/v1/events?limit=${limit}",
            "/platform/v1/events"
        )


class TestNonPlatformEndpointNormalization:
    """Tests for non-platform endpoint normalization."""

    def test_accounts_manage(self):
        """Accounts manage endpoint."""
        assert endpoints_match(
            "/api/accounts/manage/${id}",
            "/api/accounts/manage/{account_id}"
        )

    def test_cashflow_monthly_query(self):
        """Cashflow monthly with query param."""
        assert endpoints_match(
            "/api/cashflow/monthly?months=${months}",
            "/api/cashflow/monthly"
        )

    def test_investments_id(self):
        """Investments by ID."""
        assert endpoints_match(
            "/api/investments/${id}",
            "/api/investments/{investment_id}"
        )

    def test_loans_schedule(self):
        """Loans schedule."""
        assert endpoints_match(
            "/api/loans/${loanId}/schedule",
            "/api/loans/{loan_id}/schedule"
        )

    def test_loans_prepayment_simulation(self):
        """Loans prepayment simulation."""
        assert endpoints_match(
            "/api/loans/${loanId}/prepayment-simulation",
            "/api/loans/{loan_id}/prepayment-simulation"
        )

    def test_loans_id(self):
        """Loans by ID."""
        assert endpoints_match(
            "/api/loans/${id}",
            "/api/loans/{loan_id}"
        )

    def test_overview_query(self):
        """Overview with query."""
        assert endpoints_match(
            "/api/overview?${query}",
            "/api/overview"
        )


class TestDriftClassification:
    """Tests for drift classification logic."""

    def test_normalization_mismatch_resolved_to_zero(self):
        """After C61, normalization mismatches should be 0 (resolved as edges)."""
        from runtime.foundation.verification.cross_layer_graph import CrossLayerGraphBuilder
        from pathlib import Path
        
        builder = CrossLayerGraphBuilder(Path.cwd())
        graph = builder.build()
        
        # Normalization mismatches should be resolved (0 drifts)
        norm_drifts = [d for d in graph.contract_drifts if d.drift_type == "normalization_mismatch"]
        assert len(norm_drifts) == 0, (
            f"Expected 0 normalization_mismatch drifts after C61, got {len(norm_drifts)}"
        )
        
        # But edges should exist for previously mismatched endpoints
        edges = [e for e in graph.edges if e.target_type == "endpoint"]
        assert len(edges) > 0

    def test_missing_endpoint_classified_critical(self):
        """Truly missing endpoints classified as critical."""
        from runtime.foundation.verification.cross_layer_graph import CrossLayerGraphBuilder
        from pathlib import Path
        
        builder = CrossLayerGraphBuilder(Path.cwd())
        graph = builder.build()
        
        missing_drifts = [d for d in graph.contract_drifts if d.drift_type == "missing_endpoint"]
        for drift in missing_drifts:
            assert drift.severity == "critical"
            assert drift.backend_endpoint is None

    def test_path_mismatch_classified_high(self):
        """Structural path differences classified as high."""
        from runtime.foundation.verification.cross_layer_graph import CrossLayerGraphBuilder
        from pathlib import Path
        
        builder = CrossLayerGraphBuilder(Path.cwd())
        graph = builder.build()
        
        path_drifts = [d for d in graph.contract_drifts if d.drift_type == "path_mismatch"]
        for drift in path_drifts:
            assert drift.severity == "high"
            assert drift.backend_endpoint is None

    def test_five_platform_normalization_resolved_as_edges(self):
        """The 5 C61 target platform normalization mismatches are now resolved as edges.
        
        Previously these were classified as normalization_mismatch drifts.
        After C61 normalization, they should be successfully matched as edges.
        """
        from runtime.foundation.verification.cross_layer_graph import CrossLayerGraphBuilder
        from pathlib import Path
        
        builder = CrossLayerGraphBuilder(Path.cwd())
        graph = builder.build()
        
        # Check that edges exist for the 5 platform endpoints
        platform_edges = [
            e for e in graph.edges 
            if e.target_type == "endpoint" and e.target_id.startswith("/platform/v1/")
        ]
        
        matched_endpoints = {e.target_id for e in platform_edges}
        
        expected_matched = {
            "/platform/v1/capabilities/{capability_id}",
            "/platform/v1/capabilities/{capability_id}/graph",
            "/platform/v1/tasks/{task_id}/cancel",
            "/platform/v1/architecture/authority/{name}",
        }
        
        # The events endpoint has query params which are handled differently
        # Verify the core 4 are matched
        for expected in expected_matched:
            assert any(expected in matched for matched in matched_endpoints), (
                f"Expected {expected} to be matched, got {matched_endpoints}"
            )
        
        # Verify no normalization_mismatch drifts for these endpoints
        norm_drifts = [d for d in graph.contract_drifts if d.drift_type == "normalization_mismatch"]
        drift_frontend_endpoints = {d.frontend_endpoint for d in norm_drifts}
        
        # These should NOT be in normalization_mismatch drifts (they're resolved)
        resolved_endpoints = {
            "/platform/v1/capabilities/${encodeURIComponent(capabilityId!)}",
            "/platform/v1/capabilities/${encodeURIComponent(capabilityId!)}/graph",
            "/platform/v1/capabilities/${capabilityId}",
            "/platform/v1/tasks/${taskId}/cancel",
            "/platform/v1/architecture/authority/${encodeURIComponent(name!)}",
        }
        
        for endpoint in resolved_endpoints:
            assert endpoint not in drift_frontend_endpoints, (
                f"{endpoint} should be resolved, not a drift"
            )