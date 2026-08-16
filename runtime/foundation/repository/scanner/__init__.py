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

from runtime.foundation.repository.scanner.base import BaseScanner, ScanResult
from runtime.foundation.repository.scanner.backend_scanner import BackendScanner
from runtime.foundation.repository.scanner.frontend_scanner import FrontendScanner
from runtime.foundation.repository.scanner.api_scanner import ApiScanner
from runtime.foundation.repository.scanner.test_scanner import TestScanner
from runtime.foundation.repository.scanner.docs_scanner import DocsScanner
from runtime.foundation.repository.scanner.workflow_scanner import WorkflowScanner
from runtime.foundation.repository.scanner.script_scanner import ScriptScanner
from runtime.foundation.repository.scanner.migration_scanner import MigrationScanner
from runtime.foundation.repository.scanner.metadata_scanner import MetadataScanner

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
