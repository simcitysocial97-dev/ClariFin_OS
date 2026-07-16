"""Tests for Capability Registry."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from src.core.capability_registry import (
    CapabilityNotFoundError,
    all_capabilities,
    backend_routes,
    capability_dependencies,
    capability_ids,
    frontend_routes,
    get_capability,
    get_registry,
    query_keys,
    validate_registry,
)


class TestCapabilityRegistry:
    """Test capability registry module."""

    def test_registry_loads_successfully(self) -> None:
        """Registry should load without errors."""
        registry = get_registry()
        assert registry is not None

    def test_all_capabilities_returns_list(self) -> None:
        """all_capabilities should return a list."""
        caps = all_capabilities()
        assert isinstance(caps, list)
        assert len(caps) >= 11  # We have 11 capabilities

    def test_capability_ids_returns_strings(self) -> None:
        """capability_ids should return list of strings."""
        ids = capability_ids()
        assert isinstance(ids, list)
        assert all(isinstance(i, str) for i in ids)
        assert "household_cashflow" in ids
        assert "debt_management" in ids
        assert "credit_cards" in ids

    def test_get_capability_returns_dict(self) -> None:
        """get_capability should return capability dict."""
        cap = get_capability("household_cashflow")
        assert isinstance(cap, dict)
        assert cap.get("id") == "household_cashflow"
        assert cap.get("name") == "Household Cashflow"

    def test_get_capability_not_found_raises(self) -> None:
        """get_capability should raise for unknown ID."""
        with pytest.raises(CapabilityNotFoundError):
            get_capability("nonexistent_capability")

    def test_dependencies_returns_list(self) -> None:
        """capability_dependencies should return list of dependency IDs."""
        deps = capability_dependencies("debt_management")
        assert isinstance(deps, list)
        assert "household_cashflow" in deps

    def test_frontend_routes_returns_dict(self) -> None:
        """frontend_routes should return dict mapping IDs to routes."""
        routes = frontend_routes()
        assert isinstance(routes, dict)
        assert "household_cashflow" in routes
        assert "/dashboard" in routes.get("household_cashflow", [])

    def test_backend_routes_returns_dict(self) -> None:
        """backend_routes should return dict mapping IDs to routes."""
        routes = backend_routes()
        assert isinstance(routes, dict)
        assert "household_cashflow" in routes

    def test_query_keys_returns_dict(self) -> None:
        """query_keys should return dict mapping IDs to query keys."""
        keys = query_keys()
        assert isinstance(keys, dict)
        assert "household_cashflow" in keys

    def test_validate_registry_returns_empty_on_valid(self) -> None:
        """validate_registry should return empty list for valid registry."""
        errors = validate_registry()
        assert isinstance(errors, list)


class TestRegistrySchema:
    """Test registry schema validation."""

    def test_all_capabilities_have_required_fields(self) -> None:
        """All capabilities should have required fields."""
        required = ["id", "name", "maturity", "status", "dependencies"]
        for cap in all_capabilities():
            for field in required:
                assert field in cap, f"Capability {cap.get('id')} missing {field}"

    def test_all_capabilities_have_valid_maturity(self) -> None:
        """All capabilities should have valid maturity level."""
        valid_maturity = {"functional", "analytical", "explainable", "optimized"}
        for cap in all_capabilities():
            maturity = cap.get("maturity")
            assert maturity in valid_maturity, f"Invalid maturity '{maturity}' in {cap.get('id')}"

    def test_all_capabilities_have_valid_status(self) -> None:
        """All capabilities should have valid status."""
        valid_status = {"active", "deprecated", "maintenance"}
        for cap in all_capabilities():
            status = cap.get("status")
            assert status in valid_status, f"Invalid status '{status}' in {cap.get('id')}"


class TestNoDuplicateQueryKeys:
    """Ensure no duplicate query keys across capabilities."""

    def test_query_keys_are_unique(self) -> None:
        """Each query key should be used by only one capability."""
        all_keys: dict[str, str] = {}
        for cap in all_capabilities():
            cap_id = cap.get("id", "")
            for key in cap.get("query_keys", []):
                if key in all_keys:
                    pytest.fail(f"Duplicate query key '{key}' in '{all_keys[key]}' and '{cap_id}'")
                all_keys[key] = cap_id
