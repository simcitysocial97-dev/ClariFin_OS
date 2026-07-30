"""Repository scanners — Phase 3.

Each scanner discovers a specific category of repository artifacts and
returns ``(nodes, edges)`` tuples that populate the repository graph.

Scanners are designed to be:
- **Deterministic**: same input always produces same output (no timestamps).
- **Non-executing**: scanners parse source files with AST/regex, they never
  import or run repository code.
- **Composable**: each scanner operates independently; the indexer merges
  results.
"""

from __future__ import annotations

from repo_intelligence.scanner.base import BaseScanner, ScanResult
from repo_intelligence.scanner.backend_scanner import BackendScanner
from repo_intelligence.scanner.frontend_scanner import FrontendScanner
from repo_intelligence.scanner.api_scanner import ApiScanner
from repo_intelligence.scanner.test_scanner import TestScanner
from repo_intelligence.scanner.docs_scanner import DocsScanner
from repo_intelligence.scanner.workflow_scanner import WorkflowScanner
from repo_intelligence.scanner.script_scanner import ScriptScanner
from repo_intelligence.scanner.migration_scanner import MigrationScanner
from repo_intelligence.scanner.metadata_scanner import MetadataScanner

__all__ = [
    "BaseScanner",
    "ScanResult",
    "BackendScanner",
    "FrontendScanner",
    "ApiScanner",
    "TestScanner",
    "DocsScanner",
    "WorkflowScanner",
    "ScriptScanner",
    "MigrationScanner",
    "MetadataScanner",
]
