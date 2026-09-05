"""AI Orchestrator (Phase 13).

Top-level coordinator for AI runs. Manages run lifecycle, step execution,
mode enforcement, and audit trail. Does NOT connect to any LLM.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["AIOrchestrator", "AI_ORCHESTRATOR_INSTANCE"]


class AIOrchestrator:
    """Central coordinator for AI run lifecycle."""

    def __init__(self) -> None:
        self._runs: dict[str, dict[str, Any]] = {}
        self._runs_dir = Path("runtime/generated/ai-runs")
        self._runs_dir.mkdir(parents=True, exist_ok=True)

    def start_run(
        self,
        *,
        symptom: str,
        mode: str = "MANUAL",
        capability_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new AI run in PENDING state."""
        run_id = f"ai-{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        run = {
            "id": run_id,
            "symptom": symptom,
            "mode": mode,
            "capability_id": capability_id,
            "status": "PENDING",
            "steps": [],
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
            "error": None,
            "audit_trail": [],
        }
        self._runs[run_id] = run
        self._persist_run(run_id)
        self._audit(run_id, "run_created", {"symptom": symptom, "mode": mode, "capability_id": capability_id})
        return run

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Retrieve an AI run by ID."""
        if run_id in self._runs:
            return self._runs[run_id]
        # Try loading from disk
        path = self._runs_dir / f"{run_id}.json"
        if path.exists():
            run = json.loads(path.read_text())
            self._runs[run_id] = run
            return run
        return None

    def list_runs(self, *, limit: int = 50, status: str | None = None) -> list[dict[str, Any]]:
        """List AI runs, optionally filtered by status."""
        runs = list(self._runs.values())
        # Also load from disk for runs not in memory
        for path in self._runs_dir.glob("*.json"):
            run_id = path.stem
            if run_id not in self._runs:
                try:
                    run = json.loads(path.read_text())
                    self._runs[run_id] = run
                    runs.append(run)
                except Exception:
                    pass

        if status:
            runs = [r for r in runs if r["status"] == status]

        # Sort by created_at descending
        runs.sort(key=lambda r: r["created_at"], reverse=True)
        return runs[:limit]

    def execute_step(
        self,
        run_id: str,
        tool_name: str,
        arguments: dict[str, Any],
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, Any] | None:
        """Execute a tool step within an AI run."""
        run = self.get_run(run_id)
        if not run:
            return None

        if run["status"] not in ("PENDING", "RUNNING"):
            raise ValueError(f"Run {run_id} is not executable (status: {run['status']})")

        step_number = len(run["steps"]) + 1
        started_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        step = {
            "step_number": step_number,
            "tool_name": tool_name,
            "arguments": arguments,
            "result": None,
            "error": None,
            "started_at": started_at,
            "completed_at": None,
            "evidence_id": None,
            "duration_ms": None,
        }

        run["status"] = "RUNNING"
        run["steps"].append(step)
        run["updated_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        self._persist_run(run_id)

        # The actual tool execution is delegated to the policy engine / tool registry
        # This method just records the step initiation.
        self._audit(run_id, "step_started", {"step": step_number, "tool": tool_name, "arguments": arguments})

        return step

    def complete_step(
        self,
        run_id: str,
        step_number: int,
        *,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        evidence_id: str | None = None,
    ) -> bool:
        """Mark a step as completed with result or error."""
        run = self.get_run(run_id)
        if not run:
            return False

        step = next((s for s in run["steps"] if s["step_number"] == step_number), None)
        if not step:
            return False

        completed_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        start_dt = datetime.fromisoformat(step["started_at"].replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
        duration_ms = int((end_dt - start_dt).total_seconds() * 1000)

        step["completed_at"] = completed_at
        step["result"] = result
        step["error"] = error
        step["evidence_id"] = evidence_id
        step["duration_ms"] = duration_ms

        # If this is the last step (no more pending), mark run as completed
        pending_steps = [s for s in run["steps"] if s["completed_at"] is None]
        if not pending_steps:
            run["status"] = "COMPLETED" if error is None else "FAILED"
            run["completed_at"] = completed_at
        else:
            run["status"] = "RUNNING"

        run["updated_at"] = completed_at
        self._persist_run(run_id)

        self._audit(run_id, "step_completed", {
            "step": step_number,
            "tool": step["tool_name"],
            "success": error is None,
            "evidence_id": evidence_id,
            "duration_ms": duration_ms,
        })

        return True

    def cancel_run(self, run_id: str) -> bool:
        """Cancel a pending or running AI run."""
        run = self.get_run(run_id)
        if not run:
            return False

        if run["status"] in ("COMPLETED", "FAILED", "CANCELLED"):
            return False

        run["status"] = "CANCELLED"
        run["completed_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        run["updated_at"] = run["completed_at"]
        self._persist_run(run_id)

        self._audit(run_id, "run_cancelled", {})
        return True

    def _persist_run(self, run_id: str) -> None:
        run = self._runs.get(run_id)
        if run:
            path = self._runs_dir / f"{run_id}.json"
            path.write_text(json.dumps(run, indent=2, default=str))

    def _audit(self, run_id: str, event_type: str, payload: dict[str, Any]) -> None:
        """Record an audit event for this run."""
        run = self._runs.get(run_id)
        if run:
            event = {
                "event_id": f"audit-{uuid.uuid4().hex[:12]}",
                "event_type": event_type,
                "run_id": run_id,
                "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "payload": payload,
            }
            run.setdefault("audit_trail", []).append(event)


# Singleton instance
AI_ORCHESTRATOR_INSTANCE = AIOrchestrator()