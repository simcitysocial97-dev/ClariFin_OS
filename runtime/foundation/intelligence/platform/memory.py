"""Phase 6 — Runtime Learning (Engineering Memory).

Builds durable engineering history from evidence the runtime has already
recorded: the event store, verification history, flaky-test records and CI
health. The point is to replace heuristics with *observed frequency*.

This module is intentionally append-only in spirit: it reads recorded history
and summarises recurring signatures. It never fabricates history, and when
there is no history it says so explicitly rather than emitting confident
defaults.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = ["EngineeringMemory", "build_memory"]

REPO_ROOT = Path(__file__).resolve().parents[4]
GENERATED_DIR = REPO_ROOT / "runtime" / "generated"


@dataclass(frozen=True, slots=True)
class EngineeringMemory:
    generated_at: str
    sources: tuple[str, ...]
    recurring_failures: tuple[dict[str, Any], ...]
    recurring_repairs: tuple[dict[str, Any], ...]
    recurring_ci_failures: tuple[dict[str, Any], ...]
    recurring_ownership_problems: tuple[dict[str, Any], ...]
    recurring_verification_failures: tuple[dict[str, Any], ...]
    observations: int
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "engineering-memory/v1",
            "generated_at": self.generated_at,
            "sources": list(self.sources),
            "observations": self.observations,
            "recurring_failures": list(self.recurring_failures),
            "recurring_repairs": list(self.recurring_repairs),
            "recurring_ci_failures": list(self.recurring_ci_failures),
            "recurring_ownership_problems": list(self.recurring_ownership_problems),
            "recurring_verification_failures": list(
                self.recurring_verification_failures
            ),
            "notes": list(self.notes),
            "usage": (
                "future diagnoses should weight these observed frequencies "
                "instead of applying static heuristics"
            ),
        }

    def as_risk_input(self) -> dict[str, Any]:
        return {
            "recurring_ci_failures": list(self.recurring_ci_failures),
            "recurring_test_failures": list(self.recurring_failures),
        }


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                out.append(obj)
    except OSError:
        pass
    return out


def _top(counter: Counter, key_name: str, minimum: int = 2) -> list[dict[str, Any]]:
    """Only signatures seen at least ``minimum`` times count as *recurring*."""
    return [
        {key_name: sig, "occurrences": count}
        for sig, count in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
        if count >= minimum
    ]


def build_memory(generated_dir: Path | None = None) -> EngineeringMemory:
    """Summarise recorded engineering history into recurring signatures."""
    gen = generated_dir or GENERATED_DIR
    sources: list[str] = []
    notes: list[str] = []
    observations = 0

    failure_sigs: Counter = Counter()
    verification_sigs: Counter = Counter()
    repair_sigs: Counter = Counter()
    ci_sigs: Counter = Counter()
    ownership_sigs: Counter = Counter()

    # -- Event store ------------------------------------------------------
    events_path = gen / "engineering-events.jsonl"
    events = _read_jsonl(events_path)
    if events:
        sources.append("engineering-events.jsonl")
        observations += len(events)
        for event in events:
            payload = event.get("payload") or {}
            if not isinstance(payload, dict):
                continue
            status = str(payload.get("status", ""))
            profile = str(payload.get("profile", "unknown"))
            if status.lower() in {"failed", "failure", "error"}:
                verification_sigs[f"profile={profile} status={status}"] += 1
                failed = payload.get("failed")
                if isinstance(failed, int) and failed:
                    failure_sigs[f"profile={profile} failed_tasks={failed}"] += 1

    # -- Flaky tests ------------------------------------------------------
    flaky = _read_json(gen / "flaky-tests.json")
    if isinstance(flaky, dict):
        sources.append("flaky-tests.json")
        entries = flaky.get("flaky_tests") or flaky.get("tests") or []
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict):
                    name = str(entry.get("test") or entry.get("name") or "unknown")
                    count = int(entry.get("failures") or entry.get("count") or 2)
                    failure_sigs[f"flaky:{name}"] += max(2, count)
                    observations += 1

    # -- CI health --------------------------------------------------------
    ci_health = _read_json(gen / "github-actions-health.json")
    if isinstance(ci_health, dict):
        sources.append("github-actions-health.json")
        workflows = ci_health.get("workflows") or []
        if isinstance(workflows, list):
            for wf in workflows:
                if not isinstance(wf, dict):
                    continue
                name = str(wf.get("name") or wf.get("workflow") or "unknown")
                failures = wf.get("failure_count") or wf.get("failures") or 0
                if isinstance(failures, int) and failures >= 2:
                    ci_sigs[f"workflow:{name}"] += failures
                observations += 1

    # -- Verification history --------------------------------------------
    history = _read_json(gen / "engineering-history.json")
    if isinstance(history, dict):
        sources.append("engineering-history.json")
        for scope in ("local", "ci", "combined"):
            bucket = history.get(scope)
            if isinstance(bucket, dict):
                failed = bucket.get("failed_runs") or bucket.get("failures")
                if isinstance(failed, int) and failed >= 2:
                    verification_sigs[f"history:{scope}"] += failed
                total = bucket.get("total_runs") or bucket.get("runs")
                if isinstance(total, int):
                    observations += total

    # -- Ownership problems ----------------------------------------------
    ownership = _read_json(gen / "artifact-ownership-v3.json") or _read_json(
        gen / "artifact-ownership.json"
    )
    if isinstance(ownership, dict):
        sources.append("artifact-ownership.json")
        for key in ("unowned", "unknown_ownership", "unregistered_artifacts"):
            entries = ownership.get(key)
            if isinstance(entries, list) and entries:
                ownership_sigs[f"{key} (x{len(entries)})"] += len(entries)

    # -- Repairs ----------------------------------------------------------
    repair_order = _read_json(gen / "repair-order.json")
    if isinstance(repair_order, dict):
        sources.append("repair-order.json")
        entries = repair_order.get("repairs") or repair_order.get("order") or []
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict):
                    target = str(entry.get("target") or entry.get("id") or "unknown")
                    repair_sigs[f"repair:{target}"] += 1
                    observations += 1

    if observations == 0:
        notes.append(
            "no engineering history recorded yet; memory is empty and future "
            "diagnoses must fall back to structural evidence only"
        )
    if not sources:
        notes.append("no memory source artifacts found")

    return EngineeringMemory(
        generated_at=datetime.now(timezone.utc).isoformat(),
        sources=tuple(sorted(set(sources))),
        recurring_failures=tuple(_top(failure_sigs, "signature")),
        recurring_repairs=tuple(_top(repair_sigs, "signature")),
        recurring_ci_failures=tuple(_top(ci_sigs, "signature")),
        recurring_ownership_problems=tuple(_top(ownership_sigs, "signature", 1)),
        recurring_verification_failures=tuple(_top(verification_sigs, "signature")),
        observations=observations,
        notes=tuple(notes),
    )
