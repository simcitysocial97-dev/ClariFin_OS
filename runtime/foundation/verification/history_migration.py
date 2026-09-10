"""One-shot migration: engineering-history.json → engineering-events.jsonl.

Imports executed verification runs from the legacy history file into the
JSONL event store so that ``AnalyticsEngine`` can see them. Only runs with
a canonical outcome (``passed`` or ``failed``, after normalising the
legacy ``pass``/``fail`` shorthand) are imported — plan-only stubs with
zero duration and no evidence are skipped.

Idempotency guard: if the event store already contains more than 100
entries the migration is skipped entirely. This prevents duplicate
import on repeated runs without requiring an explicit migration manifest
check.

Migration manifest is written to
``runtime/generated/migration-history-to-events.json`` for auditability.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
HISTORY_PATH = REPO_ROOT / "runtime" / "generated" / "engineering-history.json"
EVENT_STORE_PATH = REPO_ROOT / "runtime" / "generated" / "engineering-events.jsonl"
MANIFEST_PATH = REPO_ROOT / "runtime" / "generated" / "migration-history-to-events.json"


def _normalize_status(status: str) -> str:
    if status in ("pass", "passed"):
        return "passed"
    if status in ("fail", "failed"):
        return "failed"
    return status


def _run_id_to_event_id(run_id: str) -> str:
    """Derive a stable event_id from a legacy UUID run_id."""
    h = hashlib.sha256(f"legacy-migrate:{run_id}".encode()).hexdigest()[:8]
    return f"vm-{h}"


def migrate(target_path: Path | None = None, manifest_path: Path | None = None) -> dict[str, Any]:
    """Run the one-shot migration. Returns a summary dict."""
    target = target_path or EVENT_STORE_PATH
    manifest = manifest_path or MANIFEST_PATH

    result = {
        "migrated": 0,
        "skipped_no_outcome": 0,
        "skipped_zero_duration": 0,
        "skipped_already_exists": 0,
        "idempotency_skipped": False,
        "source_file": str(HISTORY_PATH),
        "target_file": str(target),
    }

    if not HISTORY_PATH.exists():
        result["error"] = f"history file not found: {HISTORY_PATH}"
        return result

    try:
        data = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        result["error"] = f"failed to read history: {exc}"
        return result

    records: list[dict[str, Any]] = []
    for key in ("local", "ci", "combined"):
        batch = data.get(key, [])
        if isinstance(batch, list):
            records.extend(batch)

    # Deduplicate by run_id
    seen_ids: set[str] = set()
    unique_records: list[dict[str, Any]] = []
    for rec in records:
        rid = rec.get("run_id", "")
        if rid and rid not in seen_ids:
            seen_ids.add(rid)
            unique_records.append(rec)

    # Load existing events to check for duplicates
    existing_ids: set[str] = set()
    if target.exists():
        try:
            for line in target.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    if evt.get("event_id"):
                        existing_ids.add(evt["event_id"])
                except json.JSONDecodeError:
                    continue
        except OSError:
            pass

    # Idempotency guard: skip if store already has substantial data
    if len(existing_ids) > 100:
        result["idempotency_skipped"] = True
        return result

    imported_event_ids: list[str] = []

    for rec in unique_records:
        raw_status = rec.get("status", "unknown")
        status = _normalize_status(raw_status)

        # Only import runs with a real outcome
        if status not in ("passed", "failed"):
            result["skipped_no_outcome"] += 1
            continue

        duration = rec.get("duration_seconds", 0.0)
        if duration == 0.0:
            result["skipped_zero_duration"] += 1
            continue

        run_id = rec.get("run_id", "")
        event_id = _run_id_to_event_id(run_id)

        # Skip if this event was already imported
        if event_id in existing_ids:
            result["skipped_already_exists"] += 1
            continue

        timestamp_str = rec.get("timestamp", "")
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            timestamp = datetime.now(UTC)

        event = {
            "event_id": event_id,
            "event_type": "VerificationCompleted",
            "timestamp": timestamp.isoformat(),
            "execution_context": {
                "environment": rec.get("environment", "local"),
                "source": "legacy-history",
                "runner": rec.get("runner", "unknown"),
                "verification_depth": rec.get("verification_depth", "unknown"),
                "intent": rec.get("intent", "unknown"),
                "trigger": rec.get("trigger", "unknown"),
                "commit_sha": rec.get("commit_sha", "unknown"),
                "branch": rec.get("branch", "unknown"),
            },
            "payload": {
                "profile": rec.get("profile", "unknown"),
                "status": status,
                "passed": rec.get("passed", 0),
                "failed": rec.get("failed", 0),
                "skipped": rec.get("skipped", 0),
                "duration_seconds": duration,
                "evidence_count": rec.get("evidence_count", 0),
                "cache_hit": rec.get("cache_hit", False),
                "final_decision": status,
                "legacy_run_id": run_id,
            },
            "metadata": rec.get("metadata", {}),
        }

        # Append to JSONL
        with open(target, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, default=str) + "\n")

        imported_event_ids.append(event_id)
        result["migrated"] += 1

    # Write manifest
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "migrated_at": datetime.now(UTC).isoformat(),
                "total_migrated": result["migrated"],
                "skipped_no_outcome": result["skipped_no_outcome"],
                "skipped_zero_duration": result["skipped_zero_duration"],
                "skipped_already_exists": result["skipped_already_exists"],
                "idempotency_skipped": result["idempotency_skipped"],
                "imported_event_ids": imported_event_ids,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return result
