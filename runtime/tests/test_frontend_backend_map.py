# runtime/tests/test_frontend_backend_map.py
#
# Tests for the FrontendBackendMapper — frontend API consumer scanner.

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from runtime.foundation.verification.frontend_backend_map import (
    ConsumerInfo,
    FrontendBackendMapper,
    _normalize_path,
)


# ---------------------------------------------------------------------------
# Normalisation tests
# ---------------------------------------------------------------------------


class TestNormalizePath:
    def test_static_path(self):
        assert _normalize_path("/api/accounts") == "/api/accounts"

    def test_template_literal_with_single_var(self):
        assert _normalize_path("/api/loans/${id}") == "/api/loans/:param"

    def test_template_literal_with_multiple_vars(self):
        assert _normalize_path("/api/loans/${loanId}/schedule") == "/api/loans/:param/schedule"

    def test_query_string_stripped(self):
        assert _normalize_path("/api/cashflow/monthly?months=12") == "/api/cashflow/monthly"

    def test_template_with_query_and_var(self):
        assert _normalize_path("/api/cashflow/monthly?months=${months}") == "/api/cashflow/monthly"

    def test_double_quoted_string(self):
        assert _normalize_path('/api/analytics') == "/api/analytics"

    def test_platform_path(self):
        assert _normalize_path("/platform/v1/health") == "/platform/v1/health"

    def test_platform_path_with_var(self):
        assert _normalize_path("/platform/v1/errors/${window}") == "/platform/v1/errors/:param"

    def test_trailing_slash_stripped(self):
        assert _normalize_path("/api/loans/") == "/api/loans"

    def test_ampersand_query_params_stripped(self):
        assert (
            _normalize_path("/platform/history/compare?current=:param&baseline=:param")
            == "/platform/history/compare"
        )


# ---------------------------------------------------------------------------
# Line-level extraction tests
# ---------------------------------------------------------------------------


class TestExtractPathsFromFile:
    def _make_file(self, tmp_path: Path, content: str) -> Path:
        f = tmp_path / "test.ts"
        f.write_text(content, encoding="utf-8")
        return f

    def test_api_fetch_single_quote(self, tmp_path: Path):
        f = self._make_file(tmp_path, """
async function fetchAccounts() {
  const res = await apiFetch('/api/accounts/manage');
}
""")
        mapper = FrontendBackendMapper()
        paths = mapper._extract_paths_from_file(f)
        assert "/api/accounts/manage" in paths

    def test_api_fetch_double_quote(self, tmp_path: Path):
        f = self._make_file(tmp_path, '''
const res = await apiFetch("/api/analytics");
''')
        mapper = FrontendBackendMapper()
        paths = mapper._extract_paths_from_file(f)
        assert "/api/analytics" in paths

    def test_api_fetch_template_literal(self, tmp_path: Path):
        f = self._make_file(tmp_path, """
const res = await apiFetch(`/api/loans/${id}`);
""")
        mapper = FrontendBackendMapper()
        paths = mapper._extract_paths_from_file(f)
        assert "/api/loans/:param" in paths

    def test_api_fetch_json_string(self, tmp_path: Path):
        f = self._make_file(tmp_path, """
const raw = await apiFetchJson('/api/v1/accounts');
""")
        mapper = FrontendBackendMapper()
        paths = mapper._extract_paths_from_file(f)
        assert "/api/v1/accounts" in paths

    def test_direct_fetch_call(self, tmp_path: Path):
        f = self._make_file(tmp_path, """
const res = await fetch('/platform/v1/health');
""")
        mapper = FrontendBackendMapper()
        paths = mapper._extract_paths_from_file(f)
        assert "/platform/v1/health" in paths

    def test_usequery_inline_fetch(self, tmp_path: Path):
        f = self._make_file(tmp_path, """
return useQuery({
  queryFn: () => apiFetchJson('/api/cards'),
});
""")
        mapper = FrontendBackendMapper()
        paths = mapper._extract_paths_from_file(f)
        assert "/api/cards" in paths

    def test_comment_line_skipped(self, tmp_path: Path):
        f = self._make_file(tmp_path, """
// const res = await apiFetch('/api/should-not-appear');
/* const x = '/api/also-skipped'; */
""")
        mapper = FrontendBackendMapper()
        paths = mapper._extract_paths_from_file(f)
        assert "/api/should-not-appear" not in paths
        assert "/api/also-skipped" not in paths

    def test_import_line_skipped(self, tmp_path: Path):
        f = self._make_file(tmp_path, """
import { apiFetch } from '@/lib/api/gateway';
import somePath from '/api/not-a-real-import';
""")
        mapper = FrontendBackendMapper()
        paths = mapper._extract_paths_from_file(f)
        # Import lines should be skipped entirely.
        assert "/api/not-a-real-import" not in paths

    def test_indirect_variable_assignment(self, tmp_path: Path):
        f = self._make_file(tmp_path, """
const url = '/api/reconciliation/pending';
const res = await apiFetch(url);
""")
        mapper = FrontendBackendMapper()
        paths = mapper._extract_paths_from_file(f)
        assert "/api/reconciliation/pending" in paths

    def test_multiple_endpoints_in_one_file(self, tmp_path: Path):
        f = self._make_file(tmp_path, """
const a = await apiFetch('/api/accounts/manage');
const b = await apiFetch('/api/loans');
const c = await apiFetch('/api/cards');
""")
        mapper = FrontendBackendMapper()
        paths = mapper._extract_paths_from_file(f)
        assert "/api/accounts/manage" in paths
        assert "/api/loans" in paths
        assert "/api/cards" in paths
        assert len(paths) == 3


# ---------------------------------------------------------------------------
# ConsumerInfo dataclass tests
# ---------------------------------------------------------------------------


class TestConsumerInfo:
    def test_to_dict(self):
        info = ConsumerInfo(
            endpoint="/api/loans",
            hook_files=["frontend/lib/hooks/use-loans.ts"],
            component_files=["frontend/app/loans/page.tsx"],
            total_references=2,
            last_scanned=1234567890.0,
        )
        d = info.to_dict()
        assert d["endpoint"] == "/api/loans"
        assert d["hook_files"] == ["frontend/lib/hooks/use-loans.ts"]
        assert d["component_files"] == ["frontend/app/loans/page.tsx"]
        assert d["total_references"] == 2
        assert d["last_scanned"] == 1234567890.0

    def test_default_values(self):
        info = ConsumerInfo(endpoint="/api/test")
        assert info.hook_files == []
        assert info.component_files == []
        assert info.total_references == 0
        assert info.last_scanned == 0.0


# ---------------------------------------------------------------------------
# Mapper integration tests (real filesystem)
# ---------------------------------------------------------------------------


class TestFrontendBackendMapper:
    def _real_root(self) -> Path:
        """Return the actual repository root for integration tests."""
        return Path(__file__).resolve().parent.parent.parent

    def test_build_consumer_map_nonempty(self):
        mapper = FrontendBackendMapper(root=self._real_root())
        result = mapper.build_consumer_map()
        assert len(result) > 0, f"No endpoints found — mapper returned {len(result)}"

    def test_cached_result_is_json_serializable(self):
        mapper = FrontendBackendMapper(root=self._real_root())
        result = mapper.build_consumer_map()
        # Should round-trip through JSON without error.
        raw = json.dumps(result, default=lambda o: o.to_dict() if hasattr(o, "to_dict") else str(o))
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)
        assert len(parsed) > 0

    def test_get_consumers_for_known_endpoint(self):
        mapper = FrontendBackendMapper(root=self._real_root())
        result = mapper.build_consumer_map()
        # Pick an endpoint we know exists.
        sample_ep = "/api/accounts/manage"
        consumers = mapper.get_consumers_for_endpoint(sample_ep)
        # At minimum the hook file should appear.
        assert len(consumers) > 0
        assert any("use-accounts" in str(c) for c in consumers)

    def test_get_endpoints_for_file(self):
        mapper = FrontendBackendMapper(root=self._real_root())
        mapper.build_consumer_map()
        hook_file = self._real_root() / "frontend" / "lib" / "hooks" / "use-accounts.ts"
        endpoints = mapper.get_endpoints_for_file(hook_file)
        assert len(endpoints) > 0
        assert "/api/accounts/manage" in endpoints

    def test_get_endpoints_for_missing_file(self):
        mapper = FrontendBackendMapper(root=self._real_root())
        mapper.build_consumer_map()
        missing = self._real_root() / "frontend" / "lib" / "hooks" / "nonexistent.ts"
        endpoints = mapper.get_endpoints_for_file(missing)
        assert endpoints == []

    def test_scan_frontend_hooks_returns_dict(self):
        mapper = FrontendBackendMapper(root=self._real_root())
        result = mapper.scan_frontend_hooks()
        assert isinstance(result, dict)
        assert len(result) > 0
        for ep, files in result.items():
            assert isinstance(ep, str)
            assert all(isinstance(f, Path) for f in files)

    def test_scan_frontend_components_returns_dict(self):
        mapper = FrontendBackendMapper(root=self._real_root())
        result = mapper.scan_frontend_components()
        assert isinstance(result, dict)
        # App pages should show up as components.
        for ep, files in result.items():
            assert isinstance(ep, str)
            assert all(isinstance(f, Path) for f in files)

    def test_cache_file_created(self, tmp_path: Path):
        mapper = FrontendBackendMapper(root=self._real_root())
        # Bypass any existing default cache so build_consumer_map forces a scan.
        mapper._consumer_map = {}
        mapper._file_mtimes = {}
        # Point cache to temp dir.
        mapper._cache_path = tmp_path / "frontend-backend-map.json"
        mapper.build_consumer_map()
        assert (tmp_path / "frontend-backend-map.json").exists()

    def test_cache_loaded_on_subsequent_init(self, tmp_path: Path):
        cache_file = tmp_path / "frontend-backend-map.json"
        mapper1 = FrontendBackendMapper(root=self._real_root())
        mapper1._cache_path = cache_file
        result1 = mapper1.build_consumer_map()
        count1 = len(result1)

        # Second mapper should load from cache without re-scanning.
        mapper2 = FrontendBackendMapper(root=self._real_root())
        mapper2._cache_path = cache_file
        result2 = mapper2.build_consumer_map()
        count2 = len(result2)

        assert count1 == count2
        assert count1 > 0

    def test_dynamic_endpoint_normalized(self):
        mapper = FrontendBackendMapper(root=self._real_root())
        result = mapper.build_consumer_map()
        # Dynamic loan path should be normalised, not contain ${}.
        dynamic_keys = [ep for ep in result if "${" in ep]
        assert dynamic_keys == [], f"Dynamic vars not normalised: {dynamic_keys}"

    def test_no_query_strings_in_keys(self):
        mapper = FrontendBackendMapper(root=self._real_root())
        result = mapper.build_consumer_map()
        query_keys = [ep for ep in result if "?" in ep]
        assert query_keys == [], f"Query strings in endpoint keys: {query_keys}"


# ---------------------------------------------------------------------------
# Gate check
# ---------------------------------------------------------------------------


def test_gate_1_1():
    """Gate 1.1: must map more than 10 endpoints."""
    from runtime.foundation.verification.frontend_backend_map import FrontendBackendMapper

    m = FrontendBackendMapper(root=Path(__file__).resolve().parent.parent.parent)
    r = m.build_consumer_map()
    assert len(r) > 10, f"Only found {len(r)} endpoints"
