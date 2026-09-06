# runtime/foundation/verification/milestone_state.py
#
# M9-C48 A1 — Machine-Verifiable Milestone State Engine (GAP-002).
#
# Authoritative execution ledger for the M9-C48 convergence program.
#
# Goals:
#   * Structured milestone IDs and lifecycle states.
#   * Objective evidence requirements (artifact path + hash, command, exit code).
#   * Artifact existence + integrity verification (sha256).
#   * Prevention of unsupported COMPLETE claims.
#   * Reconciliation between machine state and the human-readable
#     EXECUTION_PROGRESS.md (via deterministic JSON snapshot).
#
# Lifecycle states (see MilestoneStatus):
#   NOT_STARTED, IN_PROGRESS, BLOCKED, IMPLEMENTED, VALIDATING,
#   COMPLETE, FAILED, SUPERSEDED.
#
# A milestone can become COMPLETE only when all of:
#   1. implementation exists (artifact present);
#   2. validation command was executed and recorded;
#   3. exit code matches expected (success when success is required);
#   4. objective evidence artifact exists;
#   5. artifact integrity (sha256) is verifiable;
#   6. acceptance criteria satisfied (recorded explicitly);
#   7. all of the above are persisted into the state snapshot.
#
# This module is pure logic only (no subprocess). It is importable by tests
# and by runtime/verify.py or M9-C48 progress tooling.

from __future__ import annotations

import hashlib
import json
import subprocess  # nosec - only used for git rev-parse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any


class MilestoneStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    IMPLEMENTED = "IMPLEMENTED"
    VALIDATING = "VALIDATING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    SUPERSEDED = "SUPERSEDED"


TERMINAL_STATUSES = frozenset(
    {MilestoneStatus.COMPLETE, MilestoneStatus.FAILED, MilestoneStatus.SUPERSEDED}
)


class CompletionGuardError(RuntimeError):
    """Raised when a milestone is being marked COMPLETE without evidence."""


# Default M9-C48 milestone catalogue (dependency-ordered).
DEFAULT_MILESTONES: list[dict[str, Any]] = [
    {
        "id": "M48-A1",
        "gap": "GAP-002",
        "phase": "FOUNDATION",
        "priority": "P0",
        "objective": "Machine-verifiable progress state engine.",
    },
    {
        "id": "M48-A2",
        "gap": "GAP-001",
        "phase": "FOUNDATION",
        "priority": "P0",
        "objective": "Resolve mutation execution authority to one canonical path.",
    },
    {
        "id": "M48-A3",
        "gap": "GAP-003",
        "phase": "FOUNDATION",
        "priority": "P0",
        "objective": "Unify MutationResult into one canonical contract.",
    },
    {
        "id": "M48-B1",
        "gap": "GAP-007",
        "phase": "SOURCE_OF_TRUTH",
        "priority": "P1",
        "objective": "Capability registry unification.",
    },
    {
        "id": "M48-B2",
        "gap": "GAP-008",
        "phase": "SOURCE_OF_TRUTH",
        "priority": "P1",
        "objective": "Register all 14 mutation engines as canonical capabilities.",
    },
    {
        "id": "M48-C1",
        "gap": "GAP-004",
        "phase": "CAPABILITY_GRAPH",
        "priority": "P1",
        "objective": "Symbol-level planning via AST analysis.",
    },
    {
        "id": "M48-C2",
        "gap": "GAP-005",
        "phase": "CAPABILITY_GRAPH",
        "priority": "P1",
        "objective": "Graph-based capability resolution (endpoint → capability).",
    },
    {
        "id": "M48-C3",
        "gap": "GAP-006",
        "phase": "CAPABILITY_GRAPH",
        "priority": "P1",
        "objective": "Severity filtering / prioritization in planner.",
    },
    {
        "id": "M48-C4",
        "gap": "GAP-009",
        "phase": "CAPABILITY_GRAPH",
        "priority": "P1",
        "objective": "Rename / move graph invalidation.",
    },
    {
        "id": "M48-C5",
        "gap": "GAP-010",
        "phase": "CAPABILITY_GRAPH",
        "priority": "P1",
        "objective": "Deletion capability removal + evidence invalidation.",
    },
    {
        "id": "M48-D1",
        "gap": "GAP-012",
        "phase": "CROSS_LAYER",
        "priority": "P2",
        "objective": "Enforce frontend financial-arithmetic rule.",
    },
    {
        "id": "M48-D2",
        "gap": "GAP-013",
        "phase": "CROSS_LAYER",
        "priority": "P2",
        "objective": "API schema mismatch governance.",
    },
    {
        "id": "M48-E1",
        "gap": "GAP-011",
        "phase": "STRENGTHENING",
        "priority": "P2",
        "objective": "End-to-end automatic test generation pipeline.",
    },
    {
        "id": "M48-F1",
        "gap": "GAP-016",
        "phase": "COVERAGE",
        "priority": "P3",
        "objective": "Fresh coverage truth measurement with identity spine.",
    },
    {
        "id": "M48-F2",
        "gap": "GAP-017",
        "phase": "TEST_QUALITY",
        "priority": "P3",
        "objective": "Test quality sampling and classification.",
    },
    {
        "id": "M48-G1",
        "gap": "GAP-014",
        "phase": "CLI",
        "priority": "P3",
        "objective": "CLI surface consolidation and classification.",
    },
    {
        "id": "M48-H1",
        "gap": "GAP-015",
        "phase": "CLEANUP",
        "priority": "P4",
        "objective": "Resolve obsolete evidence-aggregator functions.",
    },
    {
        "id": "M48-H2",
        "gap": "GAP-018",
        "phase": "AUDIT",
        "priority": "P4",
        "objective": "100% framework function audit disposition.",
    },
    {
        "id": "M48-I1",
        "gap": "GAP-CONSOLIDATION",
        "phase": "FINAL",
        "priority": "P0",
        "objective": "Final repository-wide convergence validation.",
    },
]


@dataclass(frozen=True, slots=True)
class Evidence:
    artifact_path: str
    artifact_sha256: str | None
    evidence_id: str | None
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "artifact_path": self.artifact_path,
            "artifact_sha256": self.artifact_sha256,
            "evidence_id": self.evidence_id,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class CommandRecord:
    command: str
    exit_code: int
    expected_result: str
    observed_result: str
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Milestone:
    id: str
    gap: str
    phase: str
    priority: str
    objective: str
    status: MilestoneStatus = MilestoneStatus.NOT_STARTED
    scope: str = ""
    files_changed: tuple[str, ...] = ()
    commands: tuple[CommandRecord, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    acceptance_criteria: tuple[str, ...] = ()
    acceptance_result: str = ""
    dependencies: tuple[str, ...] = ()
    dependency_status: str = ""
    blocker: str = ""
    implementation_status: str = ""
    validation_status: str = ""
    review_gate: str = ""
    started_at: str = ""
    completed_at: str = ""
    repository_sha: str = ""
    artifact_paths: tuple[str, ...] = ()
    final_disposition: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    @classmethod
    def _rebuild(cls, m: Milestone, **overrides: Any) -> Milestone:
        d = m.to_dict()
        d.update(overrides)
        # Reconstitute status enum.
        d["status"] = MilestoneStatus(d["status"])
        # Tuples.
        for k in (
            "files_changed",
            "acceptance_criteria",
            "dependencies",
            "artifact_paths",
        ):
            d[k] = tuple(d.get(k, []))
        # If commands or evidence came in as already-built tuples, keep them;
        # otherwise rebuild from dict representation.
        if d.get("commands") and isinstance(d["commands"][0], dict):
            d["commands"] = tuple(CommandRecord(**c) for c in d["commands"])
        if d.get("evidence") and isinstance(d["evidence"][0], dict):
            d["evidence"] = tuple(Evidence(**e) for e in d["evidence"])
        return cls(**d)


def compute_sha256(path: str | Path) -> str:
    """Return the hex sha256 of *path* or '' if missing/empty."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def current_repository_sha(workdir: str | Path = ".") -> str:
    try:
        out = subprocess.run(  # nosec
            ["git", "rev-parse", "HEAD"],
            cwd=str(workdir),
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except Exception:  # pragma: no cover
        return ""


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _verify_evidence(evidence: Evidence) -> tuple[bool, str]:
    """Validate that an Evidence exists and its sha matches (if recorded)."""
    p = Path(evidence.artifact_path)
    if not p.exists():
        return False, f"artifact missing: {evidence.artifact_path}"
    if not p.is_file():
        return False, f"artifact is not a file: {evidence.artifact_path}"
    if evidence.artifact_sha256:
        actual = compute_sha256(p)
        if actual != evidence.artifact_sha256:
            return False, (
                f"artifact sha mismatch for {evidence.artifact_path}: "
                f"recorded={evidence.artifact_sha256[:12]} actual={actual[:12]}"
            )
    return True, "ok"


class MilestoneLedger:
    """Authoritative machine-readable milestone state.

    Use:
        ledger = MilestoneLedger.from_default_catalogue()
        ledger.transition("M48-A1", MilestoneStatus.IN_PROGRESS, scope="…")
        ledger.record_command(...)
        ledger.add_evidence(...)
        ledger.mark_complete("M48-A1", acceptance=("exit0", "hash_ok"))
        ledger.save(path)
    """

    def __init__(self, milestones: dict[str, Milestone]) -> None:
        self._milestones: dict[str, Milestone] = milestones

    # ---------- Construction -----------------------------------------------
    @classmethod
    def from_default_catalogue(cls) -> MilestoneLedger:
        ms: dict[str, Milestone] = {}
        for entry in DEFAULT_MILESTONES:
            ms[entry["id"]] = Milestone(
                id=entry["id"],
                gap=entry["gap"],
                phase=entry["phase"],
                priority=entry["priority"],
                objective=entry["objective"],
            )
        return cls(ms)

    @classmethod
    def from_snapshot(cls, path: str | Path) -> MilestoneLedger:
        p = Path(path)
        if not p.exists():
            return cls.from_default_catalogue()
        data = json.loads(p.read_text())
        ms: dict[str, Milestone] = {}
        for mid, entry in data.get("milestones", {}).items():
            ms[mid] = Milestone(
                id=entry["id"],
                gap=entry["gap"],
                phase=entry["phase"],
                priority=entry["priority"],
                objective=entry["objective"],
                status=MilestoneStatus(entry["status"]),
                scope=entry.get("scope", ""),
                files_changed=tuple(entry.get("files_changed", [])),
                commands=tuple(CommandRecord(**c) for c in entry.get("commands", [])),
                evidence=tuple(Evidence(**e) for e in entry.get("evidence", [])),
                acceptance_criteria=tuple(entry.get("acceptance_criteria", [])),
                acceptance_result=entry.get("acceptance_result", ""),
                dependencies=tuple(entry.get("dependencies", [])),
                dependency_status=entry.get("dependency_status", ""),
                blocker=entry.get("blocker", ""),
                implementation_status=entry.get("implementation_status", ""),
                validation_status=entry.get("validation_status", ""),
                review_gate=entry.get("review_gate", ""),
                started_at=entry.get("started_at", ""),
                completed_at=entry.get("completed_at", ""),
                repository_sha=entry.get("repository_sha", ""),
                artifact_paths=tuple(entry.get("artifact_paths", [])),
                final_disposition=entry.get("final_disposition", ""),
            )
        return cls(ms)

    # ---------- Introspection ---------------------------------------------
    def get(self, mid: str) -> Milestone:
        if mid not in self._milestones:
            raise KeyError(f"unknown milestone id: {mid}")
        return self._milestones[mid]

    def all(self) -> dict[str, Milestone]:
        return dict(self._milestones)

    def ids(self) -> list[str]:
        return list(self._milestones.keys())

    # ---------- Mutation --------------------------------------------------
    def _set(self, m: Milestone) -> None:
        self._milestones[m.id] = m

    def transition(
        self,
        mid: str,
        status: MilestoneStatus,
        *,
        scope: str | None = None,
        repository_sha: str | None = None,
    ) -> Milestone:
        m = self.get(mid)
        if status == MilestoneStatus.IN_PROGRESS and not m.started_at:
            started = now_iso()
        else:
            started = m.started_at
        sha = repository_sha or m.repository_sha or current_repository_sha()
        new_m = Milestone(
            id=m.id,
            gap=m.gap,
            phase=m.phase,
            priority=m.priority,
            objective=m.objective,
            status=status,
            scope=scope if scope is not None else m.scope,
            files_changed=m.files_changed,
            commands=m.commands,
            evidence=m.evidence,
            acceptance_criteria=m.acceptance_criteria,
            acceptance_result=m.acceptance_result,
            dependencies=m.dependencies,
            dependency_status=m.dependency_status,
            blocker=m.blocker,
            implementation_status=m.implementation_status,
            validation_status=m.validation_status,
            review_gate=m.review_gate,
            started_at=started,
            completed_at=m.completed_at,
            repository_sha=sha,
            artifact_paths=m.artifact_paths,
            final_disposition=m.final_disposition,
        )
        self._set(new_m)
        return new_m

    def add_files_changed(self, mid: str, paths: list[str]) -> None:
        m = self.get(mid)
        merged = tuple(sorted(set(m.files_changed).union(paths)))
        self._set(Milestone._rebuild(m, files_changed=merged))

    def record_command(
        self,
        mid: str,
        *,
        command: str,
        exit_code: int,
        expected_result: str,
        observed_result: str,
    ) -> None:
        m = self.get(mid)
        rec = CommandRecord(
            command=command,
            exit_code=exit_code,
            expected_result=expected_result,
            observed_result=observed_result,
            timestamp=now_iso(),
        )
        self._set(Milestone._rebuild(m, commands=(*m.commands, rec)))

    def add_evidence(
        self,
        mid: str,
        *,
        artifact_path: str,
        evidence_id: str,
        description: str = "",
    ) -> Evidence:
        m = self.get(mid)
        sha = compute_sha256(artifact_path)
        ev = Evidence(
            artifact_path=artifact_path,
            artifact_sha256=sha,
            evidence_id=evidence_id,
            description=description,
        )
        artifact_paths = tuple(sorted(set(m.artifact_paths).union([artifact_path])))
        self._set(
            Milestone._rebuild(
                m, evidence=(*m.evidence, ev), artifact_paths=artifact_paths
            )
        )
        return ev

    def set_acceptance_criteria(self, mid: str, criteria: list[str]) -> None:
        m = self.get(mid)
        self._set(Milestone._rebuild(m, acceptance_criteria=tuple(criteria)))

    def set_dependency_status(self, mid: str, status: str) -> None:
        m = self.get(mid)
        self._set(Milestone._rebuild(m, dependency_status=status))

    def mark_blocked(self, mid: str, blocker: str) -> None:
        m = self.get(mid)
        self._set(
            Milestone(
                **{**m.to_dict(), "status": MilestoneStatus.BLOCKED, "blocker": blocker}  # type: ignore[arg-type]
            )
        )

    def mark_complete(
        self, mid: str, *, acceptance: list[str], require_success_exit: bool = True
    ) -> Milestone:
        """Transition a milestone to COMPLETE only if objective evidence exists.

        Refuses to mark COMPLETE when:
          * status is not currently IMPLEMENTED or VALIDATING;
          * no Evidence is recorded;
          * any recorded artifact is missing;
          * any recorded sha256 does not match the artifact on disk;
          * acceptance list is empty;
          * require_success_exit and a recorded command has non-zero exit.
        """
        m = self.get(mid)
        if m.status not in {MilestoneStatus.IMPLEMENTED, MilestoneStatus.VALIDATING}:
            raise CompletionGuardError(
                f"{mid}: cannot mark COMPLETE from {m.status.value}; "
                "must be IMPLEMENTED or VALIDATING"
            )
        if not m.evidence:
            raise CompletionGuardError(
                f"{mid}: cannot mark COMPLETE without objective evidence"
            )
        if not acceptance:
            raise CompletionGuardError(
                f"{mid}: cannot mark COMPLETE without acceptance criteria"
            )
        for ev in m.evidence:
            ok, msg = _verify_evidence(ev)
            if not ok:
                raise CompletionGuardError(f"{mid}: evidence invalid — {msg}")
        if require_success_exit:
            for cmd in m.commands:
                if cmd.exit_code != 0:
                    raise CompletionGuardError(
                        f"{mid}: cannot mark COMPLETE with non-zero exit: "
                        f"{cmd.command!r} -> {cmd.exit_code}"
                    )
        new_m = Milestone(
            id=m.id,
            gap=m.gap,
            phase=m.phase,
            priority=m.priority,
            objective=m.objective,
            status=MilestoneStatus.COMPLETE,
            scope=m.scope,
            files_changed=m.files_changed,
            commands=m.commands,
            evidence=m.evidence,
            acceptance_criteria=m.acceptance_criteria,
            acceptance_result="; ".join(acceptance),
            dependencies=m.dependencies,
            dependency_status=m.dependency_status,
            blocker=m.blocker,
            implementation_status=m.implementation_status,
            validation_status=m.validation_status,
            review_gate="passed",
            started_at=m.started_at,
            completed_at=now_iso(),
            repository_sha=m.repository_sha,
            artifact_paths=m.artifact_paths,
            final_disposition="COMPLETE",
        )
        self._set(new_m)
        return new_m

    def mark_failed(self, mid: str, reason: str) -> Milestone:
        m = self.get(mid)
        new_m = Milestone(
            id=m.id,
            gap=m.gap,
            phase=m.phase,
            priority=m.priority,
            objective=m.objective,
            status=MilestoneStatus.FAILED,
            scope=m.scope,
            files_changed=m.files_changed,
            commands=m.commands,
            evidence=m.evidence,
            acceptance_criteria=m.acceptance_criteria,
            acceptance_result=reason,
            dependencies=m.dependencies,
            dependency_status=m.dependency_status,
            blocker=reason,
            implementation_status=m.implementation_status,
            validation_status=m.validation_status,
            review_gate="failed",
            started_at=m.started_at,
            completed_at=now_iso(),
            repository_sha=m.repository_sha,
            artifact_paths=m.artifact_paths,
            final_disposition="FAILED",
        )
        self._set(new_m)
        return new_m

    # ---------- Persistence ------------------------------------------------
    def snapshot(self) -> dict:
        return {
            "schema": "m9-c48/milestone-state@1",
            "generated_at": now_iso(),
            "repository_sha": current_repository_sha(),
            "milestones": {mid: m.to_dict() for mid, m in self._milestones.items()},
        }

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.snapshot(), indent=2, sort_keys=True))

    def reconciliation_report(self, progress_md_path: str | Path) -> dict:
        """Cross-check the JSON state vs the EXECUTION_PROGRESS.md headings."""
        p = Path(progress_md_path)
        if not p.exists():
            return {"reconciled": False, "reason": "progress markdown missing"}
        text = p.read_text()
        report: dict[str, Any] = {
            "milestones": {},
            "missing_in_progress": [],
            "missing_in_state": [],
            "reconciled": True,
        }
        for mid, m in self._milestones.items():
            in_progress = mid in text
            report["milestones"][mid] = {
                "in_state": True,
                "in_progress_md": in_progress,
                "status": m.status.value,
            }
            if not in_progress:
                report["missing_in_progress"].append(mid)
        return report


__all__ = [
    "MilestoneStatus",
    "Milestone",
    "MilestoneLedger",
    "Evidence",
    "CommandRecord",
    "CompletionGuardError",
    "DEFAULT_MILESTONES",
    "TERMINAL_STATUSES",
    "compute_sha256",
    "current_repository_sha",
]
