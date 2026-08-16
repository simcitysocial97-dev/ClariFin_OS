"""Architectural Integrity Engine — Program 10.

Deterministic constitutional validation for the Financial OS.

Usage:
    python runtime/verify.py integrity

The engine scans the repository, evaluates all constitutional rules,
and produces a deterministic IntegrityReport.  It never modifies
code, repairs code, or rewrites files.
"""

from __future__ import annotations

from runtime.foundation.integrity.engine import (
    ArchitecturalIntegrityEngine,
    evaluate_integrity,
)
from runtime.foundation.integrity.formatter import (
    format_integrity_report,
    format_violation_detail,
)
from runtime.foundation.integrity.models import (
    ArchitectureLayer,
    IntegrityReport,
    Violation,
    ViolationCategory,
    ViolationSeverity,
)
from runtime.foundation.integrity.registry import (
    ConstitutionalRegistry,
    IntegrityRule,
    get_constitution,
)
from runtime.foundation.integrity.scanner import (
    ArchitecturalGraph,
    ArchitecturalScanner,
    ScannedFile,
    classify_layer,
    discover_source_files,
)

__all__ = [
    "ArchitecturalIntegrityEngine",
    "evaluate_integrity",
    "format_integrity_report",
    "format_violation_detail",
    "ArchitectureLayer",
    "IntegrityReport",
    "Violation",
    "ViolationCategory",
    "ViolationSeverity",
    "ConstitutionalRegistry",
    "IntegrityRule",
    "get_constitution",
    "ArchitecturalGraph",
    "ArchitecturalScanner",
    "ScannedFile",
    "classify_layer",
    "discover_source_files",
]