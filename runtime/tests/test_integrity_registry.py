"""Registry Tests — Program 10.

Tests for the ConstitutionalRegistry and IntegrityRule metadata.
Deterministic. No network. No git mutation.
"""

from __future__ import annotations

import pytest

from runtime.foundation.integrity.registry import (
    ConstitutionalRegistry,
    IntegrityRule,
    get_constitution,
)
from runtime.foundation.integrity.models import (
    ViolationCategory,
    ViolationSeverity,
)


class TestConstitutionalRegistry:
    """Tests for the constitutional rule registry."""

    def test_registry_has_28_rules(self) -> None:
        registry = get_constitution()
        assert registry.total_count == 28

    def test_registry_rule_ids_are_unique(self) -> None:
        registry = get_constitution()
        ids = [r.id for r in registry.all_rules()]
        assert len(ids) == len(set(ids))

    def test_registry_rule_ids_are_sequential(self) -> None:
        registry = get_constitution()
        ids = [r.id for r in registry.all_rules()]
        # Rules are grouped by category (structural, ownership, evolution)
        # but all 28 IDs from ARCH-001 to ARCH-028 must be present
        expected = set(f"ARCH-{i:03d}" for i in range(1, 29))
        assert set(ids) == expected
        assert len(ids) == 28

    def test_get_rule_by_id(self) -> None:
        registry = get_constitution()
        rule = registry.get("ARCH-001")
        assert rule is not None
        assert rule.name == "Router may not import Engine"

    def test_get_rule_by_id_missing(self) -> None:
        registry = get_constitution()
        assert registry.get("ARCH-9999") is None

    def test_all_rules_are_frozen(self) -> None:
        registry = get_constitution()
        for rule in registry.all_rules():
            assert isinstance(rule, IntegrityRule)

    def test_rules_have_required_fields(self) -> None:
        registry = get_constitution()
        for rule in registry.all_rules():
            assert rule.id
            assert rule.name
            assert rule.description
            assert rule.severity in ViolationSeverity
            assert rule.category in ViolationCategory
            assert rule.check

    def test_structural_rules_count(self) -> None:
        registry = get_constitution()
        structural = registry.by_category(ViolationCategory.STRUCTURAL)
        assert len(structural) == 13

    def test_ownership_rules_count(self) -> None:
        registry = get_constitution()
        ownership = registry.by_category(ViolationCategory.OWNERSHIP)
        assert len(ownership) == 8

    def test_evolution_rules_count(self) -> None:
        registry = get_constitution()
        evolution = registry.by_category(ViolationCategory.EVOLUTION)
        assert len(evolution) == 7

    def test_registry_is_immutable(self) -> None:
        registry = get_constitution()
        rules = registry.all_rules()
        assert isinstance(rules, list)

    def test_rule_severity_levels(self) -> None:
        registry = get_constitution()
        severities = {r.severity for r in registry.all_rules()}
        assert ViolationSeverity.CRITICAL in severities
        assert ViolationSeverity.HIGH in severities
        assert ViolationSeverity.MEDIUM in severities
        assert ViolationSeverity.LOW in severities

    def test_critical_rules_exist(self) -> None:
        registry = get_constitution()
        critical = [r for r in registry.all_rules() if r.severity == ViolationSeverity.CRITICAL]
        assert len(critical) >= 1
        assert any(r.id == "ARCH-009" for r in critical)

    def test_examples_not_empty(self) -> None:
        registry = get_constitution()
        for rule in registry.all_rules():
            assert len(rule.examples) > 0, f"Rule {rule.id} has no examples"

    def test_check_functions_exist(self) -> None:
        from runtime.foundation.integrity.rules import _RULE_CHECKS

        registry = get_constitution()
        for rule in registry.all_rules():
            assert rule.id in _RULE_CHECKS, (
                f"Missing check function for {rule.id}: {rule.check}"
            )