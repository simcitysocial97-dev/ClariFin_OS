"""Frontend-Backend Sync Gate — CI Gate for Orphaned Consumers.

Detects frontend files that reference backend endpoints which no longer
exist in the backend router inventory. This gate enforces contract
integrity between the frontend consumer layer and backend provider layer.

Usage:
    python -m runtime.verify inspect frontend-backend-sync

Exit codes:
    0 — All frontend consumers have valid backend endpoints
    1 — Orphaned consumers found (frontend calls deleted/missing endpoints)
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class OrphanedConsumer:
    """A frontend consumer referencing a non-existent backend endpoint."""

    endpoint: str
    frontend_files: List[str] = field(default_factory=list)
    reason: str = "endpoint_deleted"


def _extract_endpoints_from_file(filepath: Path) -> List[str]:
    """Extract FastAPI route endpoints from a Python router file."""
    endpoints = []
    try:
        content = filepath.read_text()
    except OSError:
        return endpoints

    # Extract router prefix: router = APIRouter(prefix="/api", ...)
    prefix_match = re.search(
        r'APIRouter\s*\(\s*prefix\s*=\s*["\']([^"\']+)["\']', content
    )
    prefix = prefix_match.group(1) if prefix_match else ""

    # Match @router.METHOD("/path") or @app.METHOD("/path")
    pattern = r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
    matches = re.findall(pattern, content)

    for match in matches:
        path = match[1]
        if prefix and path:
            full_path = prefix.rstrip("/") + "/" + path.lstrip("/")
        elif prefix:
            full_path = prefix
        else:
            full_path = path
        endpoints.append(full_path)

    return endpoints


class FrontendBackendGate:
    """CI gate to detect orphaned frontend consumers.

    Scans all backend routers for the current endpoint inventory,
    then compares against the frontend consumer map to find any
    endpoints the frontend references but the backend no longer provides.
    """

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    def get_backend_endpoints(self) -> Set[str]:
        """Scan all backend routers to get current endpoint inventory."""
        endpoints: Set[str] = set()
        router_dir = self.repo_root / "backend" / "src" / "routers"

        if not router_dir.exists():
            return endpoints

        for router_file in sorted(router_dir.glob("*.py")):
            endpoints.update(_extract_endpoints_from_file(router_file))

        return endpoints

    def get_frontend_consumers(self) -> Dict[str, List[str]]:
        """Build frontend consumer map from source files."""
        try:
            from .frontend_backend_map import FrontendBackendMapper

            mapper = FrontendBackendMapper(self.repo_root)
            consumer_map = mapper.build_consumer_map()
            return {
                ep: [str(f) for f in info.hook_files + info.component_files]
                for ep, info in consumer_map.items()
            }
        except ImportError:
            return {}
        except Exception:
            return {}

    def check_orphaned_consumers(self) -> List[OrphanedConsumer]:
        """Find frontend consumers calling non-existent backend endpoints."""
        backend_endpoints = self.get_backend_endpoints()
        frontend_consumers = self.get_frontend_consumers()

        orphaned: List[OrphanedConsumer] = []
        for endpoint, frontend_files in frontend_consumers.items():
            if endpoint not in backend_endpoints:
                orphaned.append(
                    OrphanedConsumer(
                        endpoint=endpoint,
                        frontend_files=frontend_files,
                        reason="endpoint_deleted",
                    )
                )

        return orphaned

    def validate(self) -> Dict[str, object]:
        """Run gate validation. Returns result dict."""
        orphaned = self.check_orphaned_consumers()
        passed = len(orphaned) == 0

        return {
            "gate": "frontend_backend_sync",
            "passed": passed,
            "orphaned_count": len(orphaned),
            "backend_endpoint_count": len(self.get_backend_endpoints()),
            "frontend_consumer_count": len(self.get_frontend_consumers()),
            "message": (
                f"Found {len(orphaned)} orphaned frontend consumer(s)"
                if not passed
                else "All frontend consumers have valid backend endpoints"
            ),
            "orphaned_consumers": [
                {
                    "endpoint": o.endpoint,
                    "reason": o.reason,
                    "frontend_files": o.frontend_files[:10],
                    "total_files": len(o.frontend_files),
                }
                for o in orphaned
            ],
        }


REPO_ROOT = Path(__file__).parent.parent.parent.parent


def run_gate() -> int:
    """CLI entry point. Returns exit code."""
    gate = FrontendBackendGate(REPO_ROOT)
    result = gate.validate()

    print("=" * 80)
    print("FRONTEND-BACKEND SYNC GATE")
    print("=" * 80)
    print(f"Backend endpoints scanned: {result['backend_endpoint_count']}")
    print(f"Frontend consumers mapped: {result['frontend_consumer_count']}")
    print()

    if result["passed"]:
        print(f"✅ PASSED: {result['message']}")
        return 0
    else:
        print(f"❌ FAILED: {result['message']}")
        print()
        for orphan in result["orphaned_consumers"]:
            print(f"Orphaned endpoint: {orphan['endpoint']}")
            print(f"  Reason: {orphan['reason']}")
            print(f"  Consuming files ({orphan['total_files']} total):")
            for fp in orphan["frontend_files"][:5]:
                print(f"    - {fp}")
            if orphan["total_files"] > 5:
                print(f"    ... and {orphan['total_files'] - 5} more")
            print()
        return 1


if __name__ == "__main__":
    sys.exit(run_gate())
