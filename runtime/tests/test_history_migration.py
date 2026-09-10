"""M9-C58 — Legacy history migration tests.

Validates that ``runtime.foundation.verification.history_migration.migrate``
correctly imports executed runs from ``engineering-history.json`` into the
JSONL event store, normalises legacy status values, and is idempotent.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from runtime.foundation.verification.history_migration import (
    _normalize_status,
    _run_id_to_event_id,
    migrate,
)
from runtime.system.observability.event_store import EngineeringEventStore


class TestNormalizeStatus:
    """Legacy shorthand converges to canonical vocabulary."""

    def test_pass_converges_to_passed(self) -> None:
        assert _normalize_status("pass") == "passed"
        assert _normalize_status("passed") == "passed"

    def test_fail_converges_to_failed(self) -> None:
        assert _normalize_status("fail") == "failed"
        assert _normalize_status("failed") == "failed"

    def test_unknown_is_preserved(self) -> None:
        assert _normalize_status("unknown") == "unknown"
        assert _normalize_status("completed") == "completed"
        assert _normalize_status("blocked") == "blocked"


class TestRunIdToEventId:
    """Legacy UUID run_ids map to stable vm- prefixed event IDs."""

    def test_deterministic(self) -> None:
        rid = "d5495eca-34e7-4383-bc9c-e2e25c279a43"
        assert _run_id_to_event_id(rid) == _run_id_to_event_id(rid)

    def test_different_idsproduce_different_events(self) -> None:
        assert _run_id_to_event_id("aaa") != _run_id_to_event_id("bbb")

    def test_format(self) -> None:
        assert _run_id_to_event_id("any").startswith("vm-")


class TestMigration:
    """End-to-end migration behaviour."""

    def test_migrates_executed_runs(
        self, tmp_path: Path
    ) -> None:
        """Only records with passed/failed status and duration>0 are imported."""
        history = tmp_path / "history.json"
        events = tmp_path / "events.jsonl"
        manifest = tmp_path / "manifest.json"

        history.write_text(
            json.dumps(
                {
                    "local": [
                        {
                            "run_id": "r1",
                            "timestamp": "2026-08-01T00:00:00+00:00",
                            "environment": "local",
                            "runner": "developer-workstation",
                            "verification_depth": "fast",
                            "intent": "developer-feedback",
                            "trigger": "manual",
                            "commit_sha": "abc123",
                            "branch": "main",
                            "profile": "quick",
                            "status": "passed",
                            "passed": 5,
                            "failed": 0,
                            "skipped": 0,
                            "duration_seconds": 10.0,
                            "blast_radius": {},
                            "evidence_count": 3,
                            "cache_hit": False,
                            "metadata": {},
                        },
                        {
                            "run_id": "r2",
                            "timestamp": "2026-08-01T01:00:00+00:00",
                            "environment": "local",
                            "runner": "developer-workstation",
                            "verification_depth": "fast",
                            "intent": "developer-feedback",
                            "trigger": "manual",
                            "commit_sha": "abc123",
                            "branch": "main",
                            "profile": "quick",
                            "status": "failed",
                            "passed": 0,
                            "failed": 2,
                            "skipped": 0,
                            "duration_seconds": 5.0,
                            "blast_radius": {},
                            "evidence_count": 1,
                            "cache_hit": False,
                            "metadata": {},
                        },
                        {
                            # Plan-only stub — should be skipped
                            "run_id": "r3",
                            "timestamp": "2026-08-01T02:00:00+00:00",
                            "environment": "local",
                            "runner": "developer-workstation",
                            "verification_depth": "fast",
                            "intent": "developer-feedback",
                            "trigger": "manual",
                            "commit_sha": "abc123",
                            "branch": "main",
                            "profile": "quick",
                            "status": "unknown",
                            "passed": 0,
                            "failed": 0,
                            "skipped": 0,
                            "duration_seconds": 0.0,
                            "blast_radius": {},
                            "evidence_count": 0,
                            "cache_hit": False,
                            "metadata": {},
                        },
                        {
                            # Zero-duration real run — skipped
                            "run_id": "r4",
                            "timestamp": "2026-08-01T03:00:00+00:00",
                            "environment": "local",
                            "runner": "developer-workstation",
                            "verification_depth": "fast",
                            "intent": "developer-feedback",
                            "trigger": "manual",
                            "commit_sha": "abc123",
                            "branch": "main",
                            "profile": "quick",
                            "status": "pass",
                            "passed": 0,
                            "failed": 0,
                            "skipped": 0,
                            "duration_seconds": 0.0,
                            "blast_radius": {},
                            "evidence_count": 0,
                            "cache_hit": True,
                            "metadata": {},
                        },
                    ],
                    "ci": [],
                    "combined": [],
                }
            ),
            encoding="utf-8",
        )

        with patch(
            "runtime.foundation.verification.history_migration.HISTORY_PATH", history
        ), patch(
            "runtime.foundation.verification.history_migration.EVENT_STORE_PATH", events
        ), patch(
            "runtime.foundation.verification.history_migration.MANIFEST_PATH", manifest
        ):
            result = migrate()

        assert result["migrated"] == 2
        assert result["skipped_no_outcome"] == 1
        assert result["skipped_zero_duration"] == 1

        # Verify events were written
        store = EngineeringEventStore(events)
        events_list = store.load_events()
        assert len(events_list) == 2
        for evt in events_list:
            assert evt.event_type == "VerificationCompleted"
            assert evt.execution_context.get("source") == "legacy-history"
            assert evt.payload.get("status") in ("passed", "failed")

    def test_normalises_legacy_pass_fail(self, tmp_path: Path) -> None:
        """Legacy 'pass'/'fail' statuses are normalised to 'passed'/'failed'."""
        history = tmp_path / "history.json"
        events = tmp_path / "events.jsonl"
        manifest = tmp_path / "manifest.json"

        history.write_text(
            json.dumps(
                {
                    "local": [
                        {
                            "run_id": "r1",
                            "timestamp": "2026-08-01T00:00:00+00:00",
                            "environment": "local",
                            "runner": "dev",
                            "verification_depth": "fast",
                            "intent": "developer-feedback",
                            "trigger": "manual",
                            "commit_sha": "abc",
                            "branch": "main",
                            "profile": "quick",
                            "status": "pass",
                            "passed": 3,
                            "failed": 0,
                            "skipped": 0,
                            "duration_seconds": 5.0,
                            "blast_radius": {},
                            "evidence_count": 2,
                            "cache_hit": False,
                            "metadata": {},
                        },
                        {
                            "run_id": "r2",
                            "timestamp": "2026-08-01T01:00:00+00:00",
                            "environment": "local",
                            "runner": "dev",
                            "verification_depth": "fast",
                            "intent": "developer-feedback",
                            "trigger": "manual",
                            "commit_sha": "abc",
                            "branch": "main",
                            "profile": "quick",
                            "status": "fail",
                            "passed": 0,
                            "failed": 1,
                            "skipped": 0,
                            "duration_seconds": 3.0,
                            "blast_radius": {},
                            "evidence_count": 1,
                            "cache_hit": False,
                            "metadata": {},
                        },
                    ],
                    "ci": [],
                    "combined": [],
                }
            ),
            encoding="utf-8",
        )

        with patch(
            "runtime.foundation.verification.history_migration.HISTORY_PATH", history
        ), patch(
            "runtime.foundation.verification.history_migration.EVENT_STORE_PATH", events
        ), patch(
            "runtime.foundation.verification.history_migration.MANIFEST_PATH", manifest
        ):
            migrate()

        store = EngineeringEventStore(events)
        events_list = store.load_events()
        statuses = {e.payload["status"] for e in events_list}
        assert statuses == {"passed", "failed"}

    def test_idempotent_on_second_run(self, tmp_path: Path) -> None:
        """Running migration twice does not duplicate events."""
        history = tmp_path / "history.json"
        events = tmp_path / "events.jsonl"
        manifest = tmp_path / "manifest.json"

        history.write_text(
            json.dumps(
                {
                    "local": [
                        {
                            "run_id": "r1",
                            "timestamp": "2026-08-01T00:00:00+00:00",
                            "environment": "local",
                            "runner": "dev",
                            "verification_depth": "fast",
                            "intent": "developer-feedback",
                            "trigger": "manual",
                            "commit_sha": "abc",
                            "branch": "main",
                            "profile": "quick",
                            "status": "passed",
                            "passed": 3,
                            "failed": 0,
                            "skipped": 0,
                            "duration_seconds": 5.0,
                            "blast_radius": {},
                            "evidence_count": 2,
                            "cache_hit": False,
                            "metadata": {},
                        },
                    ],
                    "ci": [],
                    "combined": [],
                }
            ),
            encoding="utf-8",
        )

        with patch(
            "runtime.foundation.verification.history_migration.HISTORY_PATH", history
        ), patch(
            "runtime.foundation.verification.history_migration.EVENT_STORE_PATH", events
        ), patch(
            "runtime.foundation.verification.history_migration.MANIFEST_PATH", manifest
        ):
            result1 = migrate()
            result2 = migrate()

        assert result1["migrated"] == 1
        assert result2["migrated"] == 0
        assert result2["skipped_already_exists"] == 1

        store = EngineeringEventStore(events)
        assert len(store.load_events()) == 1

    def test_idempotency_guard_skips_large_store(self, tmp_path: Path) -> None:
        """If store already has >100 entries, migration is skipped entirely."""
        history = tmp_path / "history.json"
        events = tmp_path / "events.jsonl"
        manifest = tmp_path / "manifest.json"

        # Pre-populate store with 101 events
        existing = []
        for i in range(101):
            existing.append(
                {
                    "event_id": f"existing-{i}",
                    "event_type": "VerificationCompleted",
                    "timestamp": "2026-09-01T00:00:00+00:00",
                    "execution_context": {
                        "environment": "local",
                        "source": "legacy-history",
                        "runner": "dev",
                        "verification_depth": "fast",
                        "intent": "developer-feedback",
                        "trigger": "manual",
                        "commit_sha": "abc",
                        "branch": "main",
                    },
                    "payload": {
                        "profile": "quick",
                        "status": "passed",
                        "passed": 1,
                        "failed": 0,
                        "skipped": 0,
                        "duration_seconds": 1.0,
                        "evidence_count": 1,
                        "cache_hit": False,
                        "final_decision": "certified",
                    },
                }
            )
        events.write_text(
            "\n".join(json.dumps(e) for e in existing) + "\n", encoding="utf-8"
        )

        history.write_text(
            json.dumps(
                {
                    "local": [
                        {
                            "run_id": "r1",
                            "timestamp": "2026-08-01T00:00:00+00:00",
                            "environment": "local",
                            "runner": "dev",
                            "verification_depth": "fast",
                            "intent": "developer-feedback",
                            "trigger": "manual",
                            "commit_sha": "abc",
                            "branch": "main",
                            "profile": "quick",
                            "status": "passed",
                            "passed": 3,
                            "failed": 0,
                            "skipped": 0,
                            "duration_seconds": 5.0,
                            "blast_radius": {},
                            "evidence_count": 2,
                            "cache_hit": False,
                            "metadata": {},
                        },
                    ],
                    "ci": [],
                    "combined": [],
                }
            ),
            encoding="utf-8",
        )

        with patch(
            "runtime.foundation.verification.history_migration.HISTORY_PATH", history
        ), patch(
            "runtime.foundation.verification.history_migration.EVENT_STORE_PATH", events
        ), patch(
            "runtime.foundation.verification.history_migration.MANIFEST_PATH", manifest
        ):
            result = migrate()

        assert result["idempotency_skipped"] is True
        assert result["migrated"] == 0

    def test_manifest_written(self, tmp_path: Path) -> None:
        """Migration writes a manifest file with summary."""
        history = tmp_path / "history.json"
        events = tmp_path / "events.jsonl"
        manifest = tmp_path / "manifest.json"

        history.write_text(
            json.dumps(
                {
                    "local": [
                        {
                            "run_id": "r1",
                            "timestamp": "2026-08-01T00:00:00+00:00",
                            "environment": "local",
                            "runner": "dev",
                            "verification_depth": "fast",
                            "intent": "developer-feedback",
                            "trigger": "manual",
                            "commit_sha": "abc",
                            "branch": "main",
                            "profile": "quick",
                            "status": "passed",
                            "passed": 3,
                            "failed": 0,
                            "skipped": 0,
                            "duration_seconds": 5.0,
                            "blast_radius": {},
                            "evidence_count": 2,
                            "cache_hit": False,
                            "metadata": {},
                        },
                    ],
                    "ci": [],
                    "combined": [],
                }
            ),
            encoding="utf-8",
        )

        with patch(
            "runtime.foundation.verification.history_migration.HISTORY_PATH", history
        ), patch(
            "runtime.foundation.verification.history_migration.EVENT_STORE_PATH", events
        ), patch(
            "runtime.foundation.verification.history_migration.MANIFEST_PATH", manifest
        ):
            migrate()

        assert manifest.exists()
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["total_migrated"] == 1
        assert len(data["imported_event_ids"]) == 1
        assert data["imported_event_ids"][0].startswith("vm-")

    def test_missing_history_file(self, tmp_path: Path) -> None:
        """Migration returns error when history file is missing."""
        events = tmp_path / "events.jsonl"
        manifest = tmp_path / "manifest.json"

        with patch(
            "runtime.foundation.verification.history_migration.HISTORY_PATH",
            tmp_path / "nonexistent.json",
        ), patch(
            "runtime.foundation.verification.history_migration.EVENT_STORE_PATH", events
        ), patch(
            "runtime.foundation.verification.history_migration.MANIFEST_PATH", manifest
        ):
            result = migrate()

        assert "error" in result
        assert result["migrated"] == 0
