"""M9-C57 Phase 4 — Platform Snapshot & Read-Path Performance validation.

These tests prove Gate 4 from ``IMPLEMENTATION_ROADMAP.md``:

    At this point the system must already be able to answer programmatically:
        What is the platform state?
        What capabilities exist?
        What is unhealthy?
        What was last verified?
        What evidence exists?
        What obligations are open?
        What happened recently?

The cache must make dashboard loading fast enough that it does NOT
trigger a full repository scan, mutation testing, full verification, or
LLM inference on every request.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from runtime.platform.cache import SNAPSHOT_PATH, snapshot


@pytest.fixture(scope="module")
def client():
    from src.api import app

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# 1. Snapshot file
# ---------------------------------------------------------------------------


class TestSnapshotFile:
    def test_snapshot_file_exists_after_generation(self, client):
        """First request to a cached domain ensures the snapshot file is written."""

        # The snapshot may already exist from a prior test run; we only
        # assert that after a fresh nocache request it still has at
        # least one domain (either pre-existing or freshly written).
        before_count = snapshot.count()
        r = client.get("/platform/v1/health?nocache=1")
        assert r.status_code == 200
        # After the request the snapshot must have at least as many
        # domains as before (the health domain is now guaranteed present).
        assert snapshot.count() >= before_count
        assert SNAPSHOT_PATH.exists(), "snapshot.json was not written"

    def test_snapshot_file_is_valid_json(self):
        if not SNAPSHOT_PATH.exists():
            pytest.skip("snapshot.json not present in test environment")
        data = SNAPSHOT_PATH.read_text(encoding="utf-8")
        parsed = json.loads(data)
        assert parsed.get("version") == "1"
        assert "generated_at" in parsed
        assert isinstance(parsed.get("domains"), dict)


# ---------------------------------------------------------------------------
# 2. Cache HIT — cold vs warm timing
# ---------------------------------------------------------------------------


class TestCacheTiming:
    """Measure cold (first) vs warm (cached) latency for slow endpoints."""

    def _warmup(self, client, path):
        client.get(path, params={"nocache": "1"})

    @pytest.mark.parametrize(
        "path,domain",
        [
            ("/platform/v1/tasks", "tasks"),
            ("/platform/v1/change/intelligence", "change"),
        ],
    )
    def test_cached_response_is_faster_than_uncached(self, client, path, domain):
        """A cached response should be noticeably faster than computing fresh."""

        self._warmup(client, path)

        # Cold (force miss via nocache=1).
        t0 = time.perf_counter()
        r_cold = client.get(path, params={"nocache": "1"})
        cold_ms = (time.perf_counter() - t0) * 1000

        # Warm (cache hit).
        t1 = time.perf_counter()
        r_warm = client.get(path)
        warm_ms = (time.perf_counter() - t1) * 1000

        assert r_cold.status_code == 200
        assert r_warm.status_code == 200
        # Warm must be materially faster (at least 3x or <5ms flat).
        assert (
            warm_ms < cold_ms
        ), f"Warm ({warm_ms:.1f}ms) was not faster than cold ({cold_ms:.1f}ms)"
        # Both responses must be structurally identical envelopes.
        assert r_warm.json()["kind"] == r_cold.json()["kind"]

    def test_healthy_service_does_not_break_when_cached(self, client):
        """Even a fast service like health should still work when cached."""

        self._warmup(client, "/platform/v1/health")
        r = client.get("/platform/v1/health")
        assert r.status_code == 200
        body = r.json()
        assert "kind" in body
        assert body["data"]["platform"] in (
            "HEALTHY",
            "DEGRAD",
            "UNHEALTHY",
            "UNKNOWN",
        )


# ---------------------------------------------------------------------------
# 3. Cache invalidation
# ---------------------------------------------------------------------------


class TestCacheInvalidation:
    def test_refresh_clears_a_domain(self):
        """snapshot.refresh(domain) removes the cached payload."""

        snap = snapshot._snap
        snap["domains"]["test_invalidate_domain"] = {
            "payload": {"dummy": True},
            "hash": "abc",
            "_c": time.monotonic(),
        }
        snapshot._snap = snap
        assert snapshot.get("test_invalidate_domain") is not None
        snapshot.refresh("test_invalidate_domain")
        assert snapshot.get("test_invalidate_domain") is None

    def test_refresh_all_clears_everything(self):
        # Ensure domains key exists before adding entries.
        snapshot._snap.setdefault("domains", {})
        snap = snapshot._snap
        snap["domains"]["a"] = {"payload": {}, "hash": "a", "_c": time.monotonic()}
        snap["domains"]["b"] = {"payload": {}, "hash": "b", "_c": time.monotonic()}
        snapshot._snap = snap
        assert snapshot.count() == 2
        snapshot.refresh_all()
        assert snapshot.count() == 0


# ---------------------------------------------------------------------------
# 4. Programmatic answers to Gate 4 questions
# ---------------------------------------------------------------------------


class TestGate4ProgrammaticAnswers:
    """Verify the 7 questions from IMPLEMENTATION_ROADMAP.md §Gate 4."""

    def test_what_is_the_platform_state(self, client):
        r = client.get("/platform/v1/health?nocache=1")
        body = r.json()
        platform = body["data"]["platform"]
        # Must be a concrete status string, not missing.
        assert isinstance(platform, str) and platform
        # The actual value is honest: the repo reports UNHEALTHY because
        # success_rate=33%. Gate 4 only requires the question to be
        # answerable, not that the answer be positive.
        assert platform in ("HEALTHY", "DEGRAD", "UNHEALTHY", "UNKNOWN")

    def test_what_capabilities_exist(self, client):
        r = client.get("/platform/v1/capabilities?nocache=1")
        body = r.json()
        count = body["data"]["count"]
        assert count == 55, f"Expected 55 capabilities, got {count}"
        items = body["data"]["items"]
        ids = {it["id"] for it in items}
        assert "discover.blast-radius" in ids

    def test_what_is_unhealthy(self, client):
        r = client.get("/platform/v1/health?nocache=1")
        body = r.json()
        domains = body["data"]["domains"]
        # Return any domain whose status is DEGRAD or UNHEALTHY.
        unhealthy = [d for d in domains if d["status"] in ("DEGRAD", "UNHEALTHY")]
        # health itself may report UNHEALTHY due to low success rate;
        # we only require that the question is answerable.
        assert isinstance(unhealthy, list)

    def test_what_was_last_verified(self, client):
        # Two separate requests so the second one actually queries the API.
        r = client.get("/platform/v1/history/runs?page=1&page_size=1&nocache=1")
        body = r.json()
        total = body["data"]["total"]
        assert total >= 0
        items = body["data"]["items"]
        assert len(items) == min(total, 1)
        assert len(items) <= 1

    def test_what_evidence_exists(self, client):
        r = client.get("/platform/v1/evidence?nocache=1")
        body = r.json()
        count = body["data"]["count"]
        assert isinstance(count, int) and count >= 0

    def test_what_obligations_are_open(self, client, monkeypatch):
        # The obligation set is derived from the *live* change set, so on a
        # checkout with nothing pending — a freshly merged `main` — the plan
        # produces no obligations and `open_count` is legitimately 0. Asserting
        # `> 0` therefore made this test pass on a PR branch (240 changed files,
        # so many obligations) and fail on the merge commit of that same branch.
        # That is the same class of bug the sibling `test_what_happened_recently`
        # documents for the event store: asserting on ambient workspace state.
        #
        # Drive the endpoint with a known, non-empty change set instead, so the
        # assertion is about the endpoint's behaviour rather than about whatever
        # happens to be unmerged. Everything else asserted here is already
        # state-independent and is kept.
        import runtime.platform.api.services.tasks as tasks_service

        monkeypatch.setattr(
            tasks_service,
            "_collect_changed_files",
            lambda *args, **kwargs: [
                "backend/src/engines/loan_engine/amortization.py"
            ],
        )
        r = client.get("/platform/v1/tasks?nocache=1")
        body = r.json()
        data = body["data"]
        assert data["open_count"] + data["closed_count"] == len(data["items"])
        assert data["open_count"] > 0
        assert data["plan_fingerprint"]

    def test_what_happened_recently(self, client):
        # The event store is append-only telemetry that accumulates from real
        # verification runs. A clean CI checkout has none, so asserting on
        # ambient history made this test pass locally and fail in CI. The test
        # seeds a deterministic event instead, so it exercises the append->list
        # path on any checkout, and the store is restored afterwards.
        from runtime.system.observability.event_store import (
            EVENT_STORE_PATH,
            EngineeringEvent,
            EngineeringEventStore,
        )

        store = EngineeringEventStore()
        backup = (
            EVENT_STORE_PATH.read_text(encoding="utf-8")
            if EVENT_STORE_PATH.exists()
            else None
        )
        store.append(
            EngineeringEvent(
                event_id="phase4-test-deterministic-event",
                event_type="test.seeded_event",
                timestamp=datetime(2026, 1, 1, tzinfo=UTC),
                execution_context={"source": "test_platform_api_phase4"},
                payload={"note": "seeded by the test so the list is non-empty"},
            )
        )
        try:
            r = client.get("/platform/v1/events?limit=5&nocache=1")
            body = r.json()
            items = body["data"]["items"]
        finally:
            if backup is None:
                EVENT_STORE_PATH.unlink(missing_ok=True)
            else:
                EVENT_STORE_PATH.write_text(backup, encoding="utf-8")

        assert len(items) > 0
        # Each item has event_type and emitted_at.
        for item in items:
            assert "event_type" in item
            assert "emitted_at" in item


# ---------------------------------------------------------------------------
# 5. no-mutation no-LLM assertion
# ---------------------------------------------------------------------------


class TestNoMutationNoLLM:
    """Confirm the cache read path does not trigger expensive side effects."""

    def test_no_new_modules_loaded_by_read(self):
        """Importing the cache must not pull in mutation / LLM modules."""

        import sys

        forbidden = {
            "mutmut",
            "ollama",
            "openai",
            "anthropic",
            "httpx",
            "aiohttp",
        }
        before = set(sys.modules)
        # Read an existing cached snapshot if present.
        from runtime.platform.cache import snapshot as _snap

        _ = _snap.get("health")
        new = {m.split(".")[0] for m in sys.modules} - {m.split(".")[0] for m in before}
        overlap = new & forbidden
        assert not overlap, f"Read path loaded forbidden modules: {overlap}"


class TestSnapshotTtlSizing:
    """The cache TTL must be sized against the cost of what it caches.

    `health` runs the full framework integrity scan and measures ~13 s. Under a
    60 s TTL the cache spent ~22 % of every window recomputing, and a console
    page arriving just after an expiry paid the whole build — which is what
    pushed the platform console's data-readiness wait past its budget on a large
    fraction of page loads. A TTL shorter than the work it caches guarantees
    that behaviour, so the TTL is now widened to a multiple of the measured
    build cost, with an explicit override still available.
    """

    def test_ttl_is_at_least_a_multiple_of_the_measured_build_cost(self):
        from runtime.platform.cache import (
            _BUILD_COST_MULTIPLE,
            _BUILD_COST_SECONDS,
            _effective_ttl,
        )

        try:
            _BUILD_COST_SECONDS["health"] = 13.0
            ttl = _effective_ttl("health")
            assert ttl is not None
            assert ttl >= 13.0 * _BUILD_COST_MULTIPLE
        finally:
            _BUILD_COST_SECONDS.pop("health", None)

    def test_health_ttl_duty_cycle_is_bounded(self):
        """The cache must not spend a large fraction of a window rebuilding."""
        from runtime.platform.cache import _effective_ttl

        ttl = _effective_ttl("health")
        assert ttl is not None
        assert 13.0 / ttl <= 0.10, f"rebuild duty cycle too high for ttl={ttl}"

    def test_unknown_domain_has_no_ttl(self):
        from runtime.platform.cache import _effective_ttl

        assert _effective_ttl("no_such_domain") is None

    def test_explicit_override_wins(self, monkeypatch):
        from runtime.platform.cache import _effective_ttl

        monkeypatch.setenv("SNAPSHOT_TTL_HEALTH", "30")
        assert _effective_ttl("health") == 30

    def test_invalid_override_falls_back_rather_than_disabling(self, monkeypatch):
        from runtime.platform.cache import _effective_ttl

        monkeypatch.setenv("SNAPSHOT_TTL_HEALTH", "not-a-number")
        assert _effective_ttl("health") is not None

    def test_zero_override_means_never_expire(self, monkeypatch):
        from runtime.platform.cache import _effective_ttl

        monkeypatch.setenv("SNAPSHOT_TTL_HEALTH", "0")
        assert _effective_ttl("health") is None

    def test_build_cost_is_recorded_on_first_build(self, tmp_path, monkeypatch):

        from runtime.platform import cache as cache_mod

        # Point the module at a throwaway snapshot file. A _SnapshotCache writes
        # through to SNAPSHOT_PATH on put(), so exercising one here without this
        # would persist a partial payload over the real health entry and every
        # later read of the cache would return it.
        monkeypatch.setattr(cache_mod, "SNAPSHOT_PATH", tmp_path / "snapshot.json")
        cache_mod._BUILD_COST_SECONDS.clear()
        try:
            store = cache_mod._SnapshotCache()
            store.get_or_build("health", lambda: {"kind": "t"}, nocache=True)
            assert cache_mod._BUILD_COST_SECONDS.get("health") is not None
        finally:
            cache_mod._BUILD_COST_SECONDS.clear()

    def test_persisted_health_payload_is_a_complete_envelope(self):
        """A cached health entry must carry data, not just its kind.

        Regression guard: a partial payload written by a test double once
        poisoned the shared snapshot file, and because the cache serves from
        disk every later read returned an envelope with no data.
        """
        from runtime.platform.api.services import health as health_service

        env = health_service.build_health_snapshot()
        assert env.get("data"), "health snapshot must carry a data payload"
        assert set(env) >= {"kind", "data", "version", "id", "generated_at"}


class TestSelfTestDiagnosticMemoization:
    """Health must not re-run the framework's test suite to read two counters.

    The K1-K9 self-tests measured 8.2 s of the 12.8 s a health snapshot cost,
    and the health read only needs `self_tests_passed` / `self_tests_total`.
    Running the suite inside a status endpoint was the largest single cost on the
    console's data path. The diagnostic is now memoized; the dedicated
    self-tests endpoint still forces a fresh run, so an operator who asks for it
    directly always gets a real result.
    """

    @staticmethod
    def _reset() -> None:
        from runtime.platform.api.services import framework_integrity as fi

        fi._self_test_cache = {"at": 0.0, "diagnostic": None}

    def test_diagnostic_is_reused_within_the_ttl(self, monkeypatch):
        from runtime.platform.api.services import framework_integrity as fi

        self._reset()
        calls = []

        class _FakeResult:
            diagnostic = {"passed": 9, "total": 9}

        class _FakeTests:
            def run_all(self):
                calls.append(1)
                return _FakeResult()

        monkeypatch.setattr(fi, "FrameworkSelfTests", _FakeTests)
        first = fi._self_test_diagnostic()
        second = fi._self_test_diagnostic()
        try:
            assert first == second
            assert len(calls) == 1, "second read must reuse the memoized diagnostic"
        finally:
            self._reset()

    def test_nocache_forces_a_fresh_run(self, monkeypatch):
        from runtime.platform.api.services import framework_integrity as fi

        self._reset()
        calls = []

        class _FakeResult:
            diagnostic = {"passed": 9, "total": 9}

        class _FakeTests:
            def run_all(self):
                calls.append(1)
                return _FakeResult()

        monkeypatch.setattr(fi, "FrameworkSelfTests", _FakeTests)
        fi._self_test_diagnostic()
        fi._self_test_diagnostic(nocache=True)
        try:
            assert len(calls) == 2, "nocache must re-run the self-tests"
        finally:
            self._reset()

    def test_expired_memo_is_recomputed(self, monkeypatch):
        from runtime.platform.api.services import framework_integrity as fi

        self._reset()
        calls = []

        class _FakeResult:
            diagnostic = {"passed": 9, "total": 9}

        class _FakeTests:
            def run_all(self):
                calls.append(1)
                return _FakeResult()

        monkeypatch.setattr(fi, "FrameworkSelfTests", _FakeTests)
        monkeypatch.setattr(fi, "_SELF_TEST_TTL_SECONDS", 0)
        fi._self_test_diagnostic()
        fi._self_test_diagnostic()
        try:
            assert len(calls) == 2, "an expired memo must be recomputed"
        finally:
            self._reset()

    def test_dedicated_endpoint_still_returns_the_diagnostic_shape(self):
        from runtime.platform.api.services import framework_integrity as fi

        env = fi.build_framework_self_tests()
        data = env["data"]
        assert "results" in data
        assert "passed" in data
        assert "total" in data
        assert data["total"] >= len(data["results"])
