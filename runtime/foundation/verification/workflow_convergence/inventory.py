"""
M9-C54 — Workflow inventory (Q1).

Extracted from workflow_convergence.py. Contains WorkflowStep, WorkflowJob,
WorkflowInventory dataclasses and the inventory_workflows() function plus
all helper routines used by it.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

from runtime.foundation.verification.ci_evidence import (  # noqa: E402
    CommandSemantics,
    ExecutionMode,
    build_ci_bindings,
    resolve_command_semantics,
    verification_bindings,
)

C54_SCHEMA = "m9-c54/workflow-convergence/v1"
C54_ARTIFACT_DIR = REPO_ROOT / "runtime" / "generated" / "m9-c54"


# ---------------------------------------------------------------------------
# Workflow inventory (Q1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    index: int
    name: str
    uses: str
    run: str
    is_verification: bool
    semantics: CommandSemantics | None
    continue_on_error: bool
    if_condition: str | None
    env: dict[str, str]
    timeout_minutes: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "name": self.name,
            "uses": self.uses,
            "run": self.run,
            "is_verification": self.is_verification,
            "semantics": (
                {
                    "task_kind": self.semantics.task_kind,
                    "verification_task": self.semantics.verification_task,
                    "evidence_kind": self.semantics.evidence_kind,
                    "execution_mode": self.semantics.execution_mode,
                    "reusable_evidence": self.semantics.reusable_evidence,
                    "scope": self.semantics.scope,
                    "description": self.semantics.description,
                }
                if self.semantics
                else None
            ),
            "continue_on_error": self.continue_on_error,
            "if_condition": self.if_condition,
            "env": dict(self.env),
            "timeout_minutes": self.timeout_minutes,
        }


@dataclass(frozen=True, slots=True)
class WorkflowJob:
    job_id: str
    name: str
    runs_on: str
    timeout_minutes: int | None
    needs: tuple[str, ...]
    strategy: dict[str, Any] | None
    steps: tuple[WorkflowStep, ...]
    verification_steps: tuple[WorkflowStep, ...]
    non_verification_steps: tuple[WorkflowStep, ...]
    has_continue_on_error: bool
    has_verification_upload: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "runs_on": self.runs_on,
            "timeout_minutes": self.timeout_minutes,
            "needs": list(self.needs),
            "strategy": self.strategy,
            "steps": [s.to_dict() for s in self.steps],
            "verification_steps": [s.to_dict() for s in self.verification_steps],
            "non_verification_steps": [
                s.to_dict() for s in self.non_verification_steps
            ],
            "has_continue_on_error": self.has_continue_on_error,
            "has_verification_upload": self.has_verification_upload,
        }


@dataclass(frozen=True, slots=True)
class WorkflowInventory:
    filename: str
    name: str
    triggers: dict[str, Any]
    concurrency: dict[str, Any]
    permissions: dict[str, str]
    jobs: tuple[WorkflowJob, ...]
    verification_jobs: tuple[WorkflowJob, ...]
    non_verification_jobs: tuple[WorkflowJob, ...]
    total_steps: int
    verification_steps: int
    has_upload_steps: bool
    has_continue_on_error: bool
    has_if_always: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "name": self.name,
            "triggers": self.triggers,
            "concurrency": self.concurrency,
            "permissions": self.permissions,
            "jobs": [j.to_dict() for j in self.jobs],
            "verification_jobs": [j.to_dict() for j in self.verification_jobs],
            "non_verification_jobs": [j.to_dict() for j in self.non_verification_jobs],
            "total_steps": self.total_steps,
            "verification_steps": self.verification_steps,
            "has_upload_steps": self.has_upload_steps,
            "has_continue_on_error": self.has_continue_on_error,
            "has_if_always": self.has_if_always,
        }


def _safe_parse_yaml(text: str) -> dict[str, Any] | None:
    """Parse YAML without requiring pyyaml if possible."""
    try:
        import yaml

        result = yaml.safe_load(text)
        return result if isinstance(result, dict) else None
    except Exception:
        return None


def _extract_env(step: dict[str, Any]) -> dict[str, str]:
    env = step.get("env") or {}
    return {str(k): str(v) for k, v in env.items()}


def _extract_timeout(step: dict[str, Any]) -> int | None:
    tm = step.get("timeout-minutes")
    if tm is not None:
        try:
            return int(tm)
        except (TypeError, ValueError):
            return None
    return None


def _is_upload_step(step: dict[str, Any]) -> bool:
    uses = step.get("uses") or ""
    return "upload" in uses.lower() or "upload" in (step.get("name") or "").lower()


def _is_verification_uses(uses: str) -> bool:
    """Check if a `uses` reference is a verification action."""
    verification_actions = {
        "codeql-action",
        "github/codeql-action",
    }
    return any(va in uses for va in verification_actions)


# Additional command patterns not in the certified COMMAND_MATCHERS
# but that are still verification commands (verify.py profiles).
_ADDITIONAL_VERIFY_PATTERNS: dict[str, CommandSemantics] = {}


def _build_additional_patterns() -> dict[str, CommandSemantics]:
    """Build additional verification patterns that supplement the certified COMMAND_MATCHERS."""
    if _ADDITIONAL_VERIFY_PATTERNS:
        return _ADDITIONAL_VERIFY_PATTERNS

    def _sem(
        task_kind: str,
        task: str,
        evidence: str,
        mode: ExecutionMode,
        reusable: bool,
        scope: Literal[
            "population",
            "component",
            "capability_all",
            "surface_only",
            "infra_health",
        ],
        cfg: bool,
        desc: str,
    ) -> CommandSemantics:
        return CommandSemantics(
            task_kind=task_kind,
            verification_task=task,
            evidence_kind=evidence,
            execution_mode=mode,
            reusable_evidence=reusable,
            scope=scope,
            depends_on_config=cfg,
            description=desc,
        )

    extras = {
        "verify.py api-contracts": _sem(
            "contract",
            "task::contract::api",
            "contract-evidence",
            "observational",
            True,
            "surface_only",
            False,
            "API contract integrity verification",
        ),
        "verify.py golden": _sem(
            "golden",
            "task::golden::regression",
            "golden",
            "observational",
            True,
            "surface_only",
            False,
            "golden dataset regression comparison",
        ),
        "codeql-action/init": _sem(
            "static",
            "task::static::codeql-init",
            "security-scan",
            "observational",
            False,
            "surface_only",
            False,
            "CodeQL initialization (GitHub-native action)",
        ),
        "codeql-action/autobuild": _sem(
            "static",
            "task::static::codeql-build",
            "security-scan",
            "observational",
            False,
            "surface_only",
            False,
            "CodeQL autobuild (GitHub-native action)",
        ),
        "codeql-action/analyze": _sem(
            "static",
            "task::static::codeql",
            "security-scan",
            "observational",
            False,
            "surface_only",
            False,
            "CodeQL security analysis (GitHub-native action)",
        ),
    }
    _ADDITIONAL_VERIFY_PATTERNS.update(extras)
    return _ADDITIONAL_VERIFY_PATTERNS


def resolve_extended_semantics(command: str) -> CommandSemantics | None:
    """Resolve command semantics using certified matchers first, then additional patterns."""
    sem = resolve_command_semantics(command)
    if sem is not None:
        return sem
    patterns = _build_additional_patterns()
    norm = " ".join(command.split())
    for pattern, cmd_sem in patterns.items():
        if pattern in norm:
            return cmd_sem
    return None


def inventory_workflows(
    workflow_dir: Path | None = None,
) -> list[WorkflowInventory]:
    """Parse every workflow file into a structured inventory."""
    import yaml

    wf_dir = Path(workflow_dir) if workflow_dir else REPO_ROOT / ".github" / "workflows"
    inventories: list[WorkflowInventory] = []
    if not wf_dir.exists():
        return inventories

    for wf_file in sorted(wf_dir.glob("*.yml")):
        try:
            doc = yaml.safe_load(wf_file.read_text())
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue

        name = str(doc.get("name", wf_file.stem))
        triggers = dict((doc.get("on") or doc.get(True) or {}).items())
        concurrency_raw = doc.get("concurrency") or {}
        concurrency: dict[str, Any] = {}
        if isinstance(concurrency_raw, dict):
            concurrency = {
                "group": concurrency_raw.get("group", ""),
                "cancel_in_progress": concurrency_raw.get("cancel-in-progress", False),
            }
        permissions = {
            str(k): str(v) for k, v in (doc.get("permissions") or {}).items()
        }

        jobs_obj = doc.get("jobs") or {}
        if not isinstance(jobs_obj, dict):
            continue

        jobs: list[WorkflowJob] = []
        for job_id, job_def in sorted(jobs_obj.items()):
            if not isinstance(job_def, dict):
                continue
            runs_on = str(job_def.get("runs-on", ""))
            timeout = job_def.get("timeout-minutes")
            try:
                timeout = int(timeout) if timeout is not None else None
            except (TypeError, ValueError):
                timeout = None
            needs_raw = job_def.get("needs") or []
            needs: tuple[str, ...]
            if isinstance(needs_raw, str):
                needs = (needs_raw,)
            else:
                needs = tuple(str(n) for n in needs_raw)
            strategy_raw = job_def.get("strategy")
            strategy = None
            if isinstance(strategy_raw, dict):
                strategy = {
                    "fail_fast": strategy_raw.get("fail-fast", True),
                    "matrix": strategy_raw.get("matrix", {}),
                }

            raw_steps = job_def.get("steps") or []
            steps_list: list[WorkflowStep] = []
            for idx, step in enumerate(raw_steps):
                if not isinstance(step, dict):
                    continue
                step_name = str(step.get("name", f"step-{idx}"))
                uses = str(step.get("uses") or "")
                run = str(step.get("run") or "")
                raw_cmd = run or uses
                continue_on_error = bool(step.get("continue-on-error", False))
                if_condition = step.get("if")
                env = _extract_env(step)
                step_timeout = _extract_timeout(step)

                sem = resolve_extended_semantics(raw_cmd) if raw_cmd else None
                is_verif = sem is not None or bool(uses and _is_verification_uses(uses))

                steps_list.append(
                    WorkflowStep(
                        index=idx,
                        name=step_name,
                        uses=uses,
                        run=run,
                        is_verification=is_verif,
                        semantics=sem,
                        continue_on_error=continue_on_error,
                        if_condition=str(if_condition) if if_condition else None,
                        env=env,
                        timeout_minutes=step_timeout,
                    )
                )

            steps = tuple(steps_list)
            verif_steps = tuple(s for s in steps if s.is_verification)
            non_verif_steps = tuple(s for s in steps if not s.is_verification)
            has_continue = any(s.continue_on_error for s in steps)
            has_upload = any(
                _is_upload_step({"uses": s.uses, "name": s.name}) for s in steps
            )

            jobs.append(
                WorkflowJob(
                    job_id=str(job_id),
                    name=str(job_def.get("name", job_id)),
                    runs_on=runs_on,
                    timeout_minutes=timeout,
                    needs=needs,
                    strategy=strategy,
                    steps=steps,
                    verification_steps=verif_steps,
                    non_verification_steps=non_verif_steps,
                    has_continue_on_error=has_continue,
                    has_verification_upload=has_upload,
                )
            )

        all_steps = sum(len(j.steps) for j in jobs)
        all_verif = sum(len(j.verification_steps) for j in jobs)
        verif_jobs = tuple(j for j in jobs if j.verification_steps)
        non_verif_jobs = tuple(j for j in jobs if not j.verification_steps)
        has_any_continue = any(j.has_continue_on_error for j in jobs)
        has_any_upload = any(j.has_verification_upload for j in jobs)
        has_any_always = False
        for j in jobs:
            for s in j.steps:
                if s.if_condition and "always()" in s.if_condition:
                    has_any_always = True
                    break

        inventories.append(
            WorkflowInventory(
                filename=wf_file.name,
                name=name,
                triggers=triggers,
                concurrency=concurrency,
                permissions=permissions,
                jobs=tuple(jobs),
                verification_jobs=verif_jobs,
                non_verification_jobs=non_verif_jobs,
                total_steps=all_steps,
                verification_steps=all_verif,
                has_upload_steps=has_any_upload,
                has_continue_on_error=has_any_continue,
                has_if_always=has_any_always,
            )
        )

    return inventories
