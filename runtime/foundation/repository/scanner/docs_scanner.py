"""Documentation scanner — discovers documentation files across the repo.

Scans:
- ``docs/`` directory
- ``memory-bank/`` directory
- ``backend/docs/`` directory
- Root-level markdown documentation files
- Frontend documentation (ARCHITECTURE.md, README.md, etc.)

Creates ``documentation`` nodes and ``documents`` edges from capabilities
to their documentation (matched by keyword in filename/content).
"""

from __future__ import annotations

import re
from pathlib import Path

from runtime.foundation.repository.scanner.base import BaseScanner, ScanResult

# Documentation directories to scan
_DOCS_DIRS: list[str] = [
    "docs",
    "memory-bank",
    "backend/docs",
    "frontend/docs",
]

# Root-level documentation files
_ROOT_DOC_FILES: list[str] = [
    "README.md",
    "CAPABILITY_AUDIT.md",
    "CAPABILITY_COVERAGE.md",
    "CAPABILITY_QUALITY_SCORE.md",
    "ENGINE_BUG_REGISTRY.json",
    "ENGINE_FAILURE_BASELINE_REPORT.md",
    "ENGINE_IMPLEMENTATION_REPORT.md",
    "GENERATOR_DETERMINISM_REPORT.md",
    "PHASE_2_5_VERIFICATION_STABILIZATION_REPORT.md",
    "PHASE_3.3_COMPLETION_SUMMARY.md",
    "PRIORITIZED_ENGINE_IMPLEMENTATION_PLAN.md",
    "SELECTIVE_VERIFICATION_IMPACT_REPORT.md",
    "STAGE_9B_CERTIFICATION_REPORT.md",
    "TEST_EXECUTION_STRATEGY.md",
    "TEST_INFRASTRUCTURE_REPORT.md",
]

# Capability keywords for matching docs to capabilities
_CAP_KEYWORDS: dict[str, list[str]] = {
    "account_management": ["account", "balance", "dormant", "lifecycle"],
    "credit_cards": ["credit", "card", "emi", "foreclosure", "utilization"],
    "debt_management": ["debt", "loan", "loan_prepayment", "loan_rate"],
    "financial_events": ["financial_event", "event_lifecycle"],
    "financial_health": ["health", "wellness", "nudge", "insight"],
    "forecasting": ["forecast", "projection", "cashflow"],
    "household_cashflow": ["household", "cashflow", "cash_flow"],
    "pattern_analysis": ["pattern", "behavior", "behaviour", "anomaly"],
    "recommendations": ["recommendation", "opportunity", "nudge"],
    "reconciliation": ["reconciliation", "reconcile", "audit"],
    "transaction_intelligence": ["transaction", "categorization", "category"],
    "verification": ["verification", "evidence", "contract", "mutation"],
}


class DocsScanner(BaseScanner):
    """Discover documentation files and link them to capabilities."""

    def scan(self) -> ScanResult:
        result = ScanResult()
        self._scan_docs_dirs(result)
        self._scan_root_docs(result)
        self._scan_capability_docs(result)
        return result

    def _scan_docs_dirs(self, result: ScanResult) -> None:
        """Scan documentation directories for .md files."""
        for dir_name in _DOCS_DIRS:
            docs_dir = self.repo_root / dir_name
            if not docs_dir.exists():
                continue

            for md_file in docs_dir.rglob("*.md"):
                rel = self.rel_path(md_file, self.repo_root)
                title = self._extract_title(md_file)
                result.add_node(
                    node_type="documentation",
                    name=title or md_file.stem,
                    path=rel,
                    source=f"filesystem:{dir_name}",
                    properties={
                        "title": title,
                        "directory": dir_name,
                        "word_count": self._word_count(md_file),
                    },
                )

    def _scan_root_docs(self, result: ScanResult) -> None:
        """Scan root-level documentation files."""
        for doc_file in _ROOT_DOC_FILES:
            file_path = self.repo_root / doc_file
            if not file_path.exists():
                continue

            rel = self.rel_path(file_path, self.repo_root)
            title = self._extract_title(file_path)
            result.add_node(
                node_type="documentation",
                name=title or doc_file,
                path=rel,
                source="filesystem:root",
                properties={
                    "title": title,
                    "directory": "root",
                    "word_count": self._word_count(file_path),
                },
            )

    def _scan_capability_docs(self, result: ScanResult) -> None:
        """Create documents edges from capabilities to their documentation."""
        for doc_node in list(result.nodes):
            if doc_node.type != "documentation":
                continue

            content = self.safe_read(self.repo_root / doc_node.path)
            if content is None:
                continue

            content_lower = content.lower()
            for cap_id, keywords in _CAP_KEYWORDS.items():
                for kw in keywords:
                    if kw in content_lower or kw in doc_node.path.lower():
                        result.add_edge(
                            source_id=f"capability:{cap_id}",
                            target_id=doc_node.id,
                            relationship="documents",
                            confidence=0.7,
                            evidence=f"keyword:{kw}",
                        )
                        break

    @staticmethod
    def _extract_title(md_file: Path) -> str | None:
        """Extract the first H1 title from a markdown file."""
        content = DocsScanner.safe_read(md_file)
        if content is None:
            return None
        match = re.match(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def _word_count(file_path: Path) -> int:
        """Count words in a file."""
        content = DocsScanner.safe_read(file_path)
        if content is None:
            return 0
        return len(content.split())
