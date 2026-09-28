"""M9-C57 — E2E Route Mapper.

Maps frontend Next.js app routes to Playwright E2E test files by scanning
the frontend directory structure and test file contents.

Usage:
    from runtime.foundation.verification.e2e_route_mapper import E2ERouteMapper
    mapper = E2ERouteMapper()
    routes = mapper.scan_frontend_routes()
    tests = mapper.scan_e2e_tests()
    route_map = mapper.build_route_test_map()
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_FRONTEND_DIR = REPO_ROOT / "frontend" / "app"
DEFAULT_E2E_DIR = REPO_ROOT / "frontend" / "tests" / "e2e" / "specs"
CACHE_PATH = REPO_ROOT / "runtime" / "generated" / "e2e-route-map.json"


@dataclass
class RouteInfo:
    """A single frontend route."""

    path: str
    file: str
    is_dynamic: bool = False
    param_name: str | None = None


@dataclass
class TestFileInfo:
    """Metadata about a single E2E test file."""

    path: str
    routes: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=list)


class E2ERouteMapper:
    """Map frontend routes to Playwright E2E test files."""

    # Patterns that indicate a route navigation in test files
    ROUTE_PATTERNS = [
        re.compile(r"page\.goto\(['\"](/[^'\"]+)['\"]\)"),
        re.compile(r"await\s+page\.goto\(['\"](/[^'\"]+)['\"]\)"),
        re.compile(r"goto\(['\"](/[^'\"]+)['\"]\)"),
        re.compile(r"browser\.newPage\(['\"](/[^'\"]+)['\"]\)"),
        re.compile(r"navigateTo\(['\"](/[^'\"]+)['\"]\)"),
        re.compile(r"route\.path\s*[:=]\s*['\"](/[^'\"]+)['\"]"),
    ]

    # Dynamic route patterns in Next.js app directory
    DYNAMIC_ROUTE_PATTERN = re.compile(r"\[(.+?)\]")

    def __init__(
        self,
        frontend_dir: Path | str | None = None,
        e2e_dir: Path | str | None = None,
        cache_path: Path | str | None = None,
    ):
        self.frontend_dir = Path(frontend_dir) if frontend_dir else DEFAULT_FRONTEND_DIR
        self.e2e_dir = Path(e2e_dir) if e2e_dir else DEFAULT_E2E_DIR
        self.cache_path = Path(cache_path) if cache_path else CACHE_PATH

    def scan_frontend_routes(self) -> list[str]:
        """Scan frontend/app/ for route definitions.

        Returns:
            List of route paths (e.g. ['/dashboard', '/accounts', '/']).
        """
        routes: set[str] = set()

        if not self.frontend_dir.exists():
            return sorted(routes)

        # Scan for directory-based routes (Next.js app router convention)
        for path in self.frontend_dir.rglob("page.tsx"):
            route_path = self._extract_route_from_path(path)
            if route_path:
                routes.add(route_path)

        # Also check for route definitions in layout.tsx files
        for path in self.frontend_dir.rglob("layout.tsx"):
            route_path = self._extract_route_from_path(path)
            if route_path:
                routes.add(route_path)

        # Always include root route
        routes.add("/")

        return sorted(routes)

    def _extract_route_from_path(self, file_path: Path) -> str | None:
        """Extract route path from a file path in the Next.js app directory."""
        try:
            rel = file_path.relative_to(self.frontend_dir)
        except ValueError:
            return None

        parts = list(rel.parts)

        # Remove page.tsx or layout.tsx
        if parts and parts[-1] in ("page.tsx", "layout.tsx"):
            parts = parts[:-1]

        if not parts:
            return "/"

        route = "/" + "/".join(parts)

        # Clean up trailing slashes
        route = route.rstrip("/") or "/"

        return route

    def scan_e2e_tests(self) -> dict[str, list[str]]:
        """Scan E2E test files and extract routes they test.

        Returns:
            Dict mapping test file paths to list of routes tested.
        """
        test_map: dict[str, list[str]] = {}

        if not self.e2e_dir.exists():
            return test_map

        for spec_file in sorted(self.e2e_dir.glob("*.spec.ts")):
            try:
                content = spec_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            routes = self._extract_routes_from_content(content)
            if routes:
                test_map[str(spec_file)] = sorted(set(routes))

        return test_map

    def _extract_routes_from_content(self, content: str) -> list[str]:
        """Extract all route paths from test file content."""
        routes: list[str] = []

        for pattern in self.ROUTE_PATTERNS:
            matches = pattern.findall(content)
            for match in matches:
                # Clean up the route
                route = match.strip().rstrip("/").split("?")[0].split("#")[0]
                if route and route not in ("", "/"):
                    routes.append(route)

        return routes

    def build_route_test_map(self) -> dict[str, list[str]]:
        """Build complete route-to-test-files mapping.

        Returns:
            Dict mapping route paths to list of test file paths.
        """
        routes = self.scan_frontend_routes()
        test_file_routes = self.scan_e2e_tests()

        route_map: dict[str, list[str]] = {route: [] for route in routes}

        for test_file, tested_routes in test_file_routes.items():
            for route in tested_routes:
                # Match exact route or parent route
                for route_key in route_map:
                    if route == route_key or route.startswith(route_key + "/"):
                        if test_file not in route_map[route_key]:
                            route_map[route_key].append(test_file)

        # Cache the result
        self._save_cache(route_map)

        return route_map

    def get_tests_for_route(self, route: str) -> list[str]:
        """Get all E2E test files that exercise a given route.

        Args:
            route: The route path (e.g. '/dashboard').

        Returns:
            List of test file paths.
        """
        route_map = self._load_cache() or self.build_route_test_map()
        return route_map.get(route, [])

    def _save_cache(self, route_map: dict[str, list[str]]) -> None:
        """Save the route map to cache."""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "schema": "e2e-route-map/v1",
                "routes": list(route_map.keys()),
                "mapping": {k: v for k, v in sorted(route_map.items())},
                "generated_at": __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                ).isoformat(),
            }
            self.cache_path.write_text(json.dumps(payload, indent=2) + "\n")
        except OSError:
            pass

    def _load_cache(self) -> dict[str, list[str]] | None:
        """Load cached route map if available."""
        if not self.cache_path.exists():
            return None
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            return data.get("mapping", {})
        except (json.JSONDecodeError, OSError):
            return None

    def get_coverage_summary(self) -> dict[str, Any]:
        """Get a summary of E2E test coverage for all routes."""
        routes = self.scan_frontend_routes()
        route_map = self.build_route_test_map()

        covered = sum(1 for r in routes if route_map.get(r))
        uncovered = [r for r in routes if not route_map.get(r)]

        return {
            "total_routes": len(routes),
            "covered_routes": covered,
            "uncovered_routes": len(uncovered),
            "coverage_pct": round(100.0 * covered / len(routes), 1) if routes else 0,
            "uncovered": uncovered[:20],  # Top 20 uncovered
        }
