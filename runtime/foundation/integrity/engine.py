"""Architectural Integrity Engine — Program 10.

Deterministic architectural validation.  The engine never modifies
code, repairs code, or rewrites files.  It only detects violations
and reports them.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from runtime.foundation.integrity.models import (
    IntegrityReport,
    Violation,
    ViolationSeverity,
)
from runtime.foundation.integrity.registry import (
    ConstitutionalRegistry,
    get_constitution,
)
from runtime.foundation.integrity.rules import run_rule
from runtime.foundation.integrity.scanner import ArchitecturalScanner


class ArchitecturalIntegrityEngine:
    """Constitutional validation engine for the Financial OS.

    The engine performs deterministic architectural validation only.
    It must NEVER modify code, repair code, or rewrite files.
    It only detects architectural violations and reports them.
    """

    def __init__(
        self,
        repo_root: str | None = None,
        registry: ConstitutionalRegistry | None = None,
        scanner: ArchitecturalScanner | None = None,
    ) -> None:
        self._repo_root = repo_root
        self._registry = registry or get_constitution()
        self._scanner = scanner

    def evaluate(self) -> IntegrityReport:
        """Run every constitutional rule and produce an IntegrityReport.

        Returns:
            Immutable IntegrityReport with all violations, summary
            counts, and suggested engineering actions.
        """
        scanner = self._scanner or ArchitecturalScanner(
            repo_root=(
                self._repo_root and __import__("pathlib").Path(self._repo_root)
            )
        )
        graph = scanner.scan()
        violations: list[Violation] = []

        for rule in self._registry.all_rules():
            rule_violations = run_rule(rule, graph)
            violations.extend(rule_violations)

        severity_counts = self._count_severities(violations)

        return IntegrityReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            rules_evaluated=self._registry.total_count,
            rules_passed=self._registry.total_count - len(
                {v.rule_id for v in violations}
            ),
            rules_failed=len({v.rule_id for v in violations}),
            violations=tuple(violations),
            files_scanned=graph.files_scanned,
            cross_layer_entries=len(graph.cross_layer_map),
            graph_nodes=len(graph.graph_nodes),
            graph_edges=len(graph.graph_edges),
            scan_errors=graph.scan_errors,
            critical_count=severity_counts.get("CRITICAL", 0),
            high_count=severity_counts.get("HIGH", 0),
            medium_count=severity_counts.get("MEDIUM", 0),
            low_count=severity_counts.get("LOW", 0),
            info_count=severity_counts.get("INFO", 0),
        )

    def _count_severities(self, violations: list[Violation]) -> dict[str, int]:
        counts: dict[str, int] = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "INFO": 0,
        }
        for v in violations:
            counts[v.severity.value] = counts.get(v.severity.value, 0) + 1
        return counts


def evaluate_integrity(repo_root: str | None = None) -> IntegrityReport:
    """Convenience function to run a full integrity evaluation."""
    engine = ArchitecturalIntegrityEngine(repo_root=repo_root)
    return engine.evaluate()