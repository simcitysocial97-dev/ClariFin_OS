"""M9-C65 — Workflow inspection capability.

Provides `verify inspect workflows` as a first-class enumeration of
`.github/workflows/*.yml` with full metadata:

    workflow_id, name, path, triggers, jobs, commands,
    canonical_command, local_executable, boundary_classification,
    environment_requirements, parity_status
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class BoundaryClassification(str, Enum):
    LOCAL = "LOCAL"
    GITHUB_ONLY = "GITHUB_ONLY"
    ENVIRONMENT_BOUNDARY = "ENVIRONMENT_BOUNDARY"
    EXTERNAL_SERVICE = "EXTERNAL_SERVICE"
    EXTERNAL_TOOLING = "EXTERNAL_TOOLING"
    BROWSER = "BROWSER"
    NETWORK = "NETWORK"
    HARDWARE = "HARDWARE"


# Workflow-to-boundary classification heuristics.
# These are rules-of-thumb; the authoritative source is the workflow YAML itself.
_WORKFLOW_BOUNDARY_RULES: dict[str, tuple[BoundaryClassification, list[str]]] = {
    "release.yml": (BoundaryClassification.GITHUB_ONLY, ["docker", "push", "tag"]),
    "security-codeql.yml": (BoundaryClassification.GITHUB_ONLY, ["codeql", "security"]),
    "playwright.yml": (BoundaryClassification.BROWSER, ["playwright", "browser", "e2e"]),
    "frontend-verify.yml": (BoundaryClassification.ENVIRONMENT_BOUNDARY, ["frontend", "next"]),
    "golden.yml": (BoundaryClassification.ENVIRONMENT_BOUNDARY, ["golden"]),
    "mutation.yml": (BoundaryClassification.EXTERNAL_TOOLING, ["mutmut"]),
    "mutation-pr.yml": (BoundaryClassification.EXTERNAL_TOOLING, ["mutmut"]),
    "api-contracts.yml": (BoundaryClassification.EXTERNAL_SERVICE, ["schema", "contract"]),
    "dependency-update.yml": (BoundaryClassification.GITHUB_ONLY, ["dependabot"]),
    "quality.yml": (BoundaryClassification.ENVIRONMENT_BOUNDARY, ["ruff", "mypy"]),
}


@dataclass(frozen=True, slots=True)
class WorkflowJob:
    """A single job inside a workflow."""

    job_id: str
    runs_on: str = ""
    steps: list[str] = field(default_factory=list)
    timeout_minutes: int = 0


@dataclass(frozen=True, slots=True)
class WorkflowRecord:
    """Complete metadata for one CI workflow."""

    workflow_id: str
    name: str
    path: str
    triggers: list[str] = field(default_factory=list)
    jobs: list[WorkflowJob] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    canonical_command: str | None = None
    local_executable: bool = False
    boundary_classification: BoundaryClassification = BoundaryClassification.LOCAL
    environment_requirements: list[str] = field(default_factory=list)
    parity_status: str = "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "path": self.path,
            "triggers": self.triggers,
            "jobs": [asdict(j) for j in self.jobs],
            "commands": self.commands,
            "canonical_command": self.canonical_command,
            "local_executable": self.local_executable,
            "boundary_classification": self.boundary_classification.value,
            "environment_requirements": self.environment_requirements,
            "parity_status": self.parity_status,
        }


def _classify_boundary(filename: str, doc: dict) -> BoundaryClassification:
    """Classify workflow boundary based on filename heuristics and content."""
    if filename in _WORKFLOW_BOUNDARY_RULES:
        cls, _ = _WORKFLOW_BOUNDARY_RULES[filename]
        return cls

    # Infer from content
    jobs = doc.get("jobs") or {}
    all_steps = []
    for job in jobs.values():
        if isinstance(job, dict):
            for step in job.get("steps") or []:
                if isinstance(step, dict):
                    run = step.get("run", "")
                    uses = step.get("uses", "")
                    if run:
                        all_steps.append(run)
                    if uses:
                        all_steps.append(uses)

    combined = " ".join(all_steps).lower()
    if any(k in combined for k in ["playwright", "browser", "cypress"]):
        return BoundaryClassification.BROWSER
    if any(k in combined for k in ["mutmut", "mutation"]):
        return BoundaryClassification.EXTERNAL_TOOLING
    if any(k in combined for k in ["docker push", "release", "publish"]):
        return BoundaryClassification.GITHUB_ONLY
    if any(k in combined for k in ["codeql", "security scan"]):
        return BoundaryClassification.GITHUB_ONLY
    if "frontend" in combined or "next build" in combined:
        return BoundaryClassification.ENVIRONMENT_BOUNDARY
    if any(k in combined for k in ["schema", "contract", "api test"]):
        return BoundaryClassification.EXTERNAL_SERVICE

    return BoundaryClassification.LOCAL


def _extract_canonical_command(filename: str, steps: list[str]) -> str | None:
    """Map workflow to its canonical verify.py command, if any."""
    step_str = " ".join(steps).lower()
    if "verify.py check" in step_str or "verify.py ci" in step_str:
        return "verify ci"
    if "verify.py strengthen" in step_str or "mutmut" in step_str:
        return "verify strengthen"
    if "playwright" in step_str:
        return "verify inspect evidence"  # proxy for E2E
    if "ruff" in step_str or "mypy" in step_str:
        return "verify doctor"  # proxy for quality
    return None


def enumerate_workflows(workflow_dir: Path | None = None) -> list[WorkflowRecord]:
    """Enumerate all CI workflows with full metadata."""
    import yaml

    wf_dir = workflow_dir or (REPO_ROOT / ".github" / "workflows")
    records: list[WorkflowRecord] = []

    if not wf_dir.exists():
        return records

    for wf_file in sorted(wf_dir.glob("*.yml")):
        try:
            doc = yaml.safe_load(wf_file.read_text())
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue

        # Triggers
        on = doc.get("on", [])
        if isinstance(on, dict):
            triggers = [str(k) for k in on.keys()]
        elif isinstance(on, list):
            triggers = [str(x) for x in on]
        else:
            triggers = [str(on)] if on else []

        # Jobs
        jobs = doc.get("jobs") or {}
        job_records = []
        all_commands = []
        for job_id, job in sorted((jobs or {}).items()):
            if not isinstance(job, dict):
                continue
            runs_on = str(job.get("runs-on", ""))
            steps = job.get("steps") or []
            step_commands = []
            for step in steps:
                if isinstance(step, dict):
                    run = step.get("run", "")
                    uses = step.get("uses", "")
                    if run:
                        step_commands.append(run)
                        all_commands.append(run)
                    if uses:
                        step_commands.append(uses)
            timeout = job.get("timeout-minutes", 0) or 0
            job_records.append(
                WorkflowJob(
                    job_id=str(job_id),
                    runs_on=runs_on,
                    steps=step_commands[:5],  # truncate long step lists
                    timeout_minutes=timeout,
                )
            )

        # Classify
        boundary = _classify_boundary(wf_file.name, doc)
        canonical = _extract_canonical_command(wf_file.name, all_commands)
        local_exec = boundary == BoundaryClassification.LOCAL

        # Parity status — compare against known verify profiles
        parity = "UNKNOWN"
        if canonical:
            parity = "PARITY_OK"
        elif boundary == BoundaryClassification.GITHUB_ONLY:
            parity = "GITHUB_ONLY"
        elif boundary in (
            BoundaryClassification.BROWSER,
            BoundaryClassification.ENVIRONMENT_BOUNDARY,
        ):
            parity = "ENVIRONMENT_BOUNDARY"

        records.append(
            WorkflowRecord(
                workflow_id=wf_file.stem,
                name=wf_file.stem,
                path=f".github/workflows/{wf_file.name}",
                triggers=triggers,
                jobs=job_records,
                commands=all_commands[:10],  # truncate
                canonical_command=canonical,
                local_executable=local_exec,
                boundary_classification=boundary,
                environment_requirements=[
                    r.value for r in (
                        [BoundaryClassification.BROWSER]
                        if boundary == BoundaryClassification.BROWSER
                        else []
                    )
                ],
                parity_status=parity,
            )
        )

    return records


def format_workflows_table(records: list[WorkflowRecord]) -> str:
    """Render workflows as a human-readable table."""
    lines = []
    lines.append("=" * 80)
    lines.append("  CI WORKFLOW INVENTORY")
    lines.append(f"  Total workflows: {len(records)}")
    lines.append("=" * 80)
    lines.append(
        f"  {'Workflow':<30} {'Canonical Command':<25} {'Local':<6} {'Boundary':<22}"
    )
    lines.append("-" * 80)
    for w in records:
        canon = (w.canonical_command or "-")[:24]
        local = "yes" if w.local_executable else "no"
        lines.append(
            f"  {w.workflow_id:<30} {canon:<25} {local:<6} {w.boundary_classification.value:<22}"
        )
    lines.append("-" * 80)

    local_count = sum(1 for w in records if w.local_executable)
    github_only = sum(1 for w in records if w.boundary_classification == BoundaryClassification.GITHUB_ONLY)
    env_boundary = sum(
        1
        for w in records
        if w.boundary_classification
        in (BoundaryClassification.ENVIRONMENT_BOUNDARY, BoundaryClassification.BROWSER)
    )
    external = sum(
        1
        for w in records
        if w.boundary_classification
        in (BoundaryClassification.EXTERNAL_SERVICE, BoundaryClassification.EXTERNAL_TOOLING)
    )
    lines.append(f"  Local executable: {local_count}")
    lines.append(f"  GitHub-only: {github_only}")
    lines.append(f"  Environment boundary: {env_boundary}")
    lines.append(f"  External service/tooling: {external}")
    lines.append("=" * 80)
    return "\n".join(lines)


def cmd_inspect_workflows(argv: list[str]) -> int:
    """verify.py inspect workflows — enumerate CI workflows with metadata."""
    parser = argparse.ArgumentParser(prog="verify.py inspect workflows")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", default=None, help="output file path")
    args = parser.parse_args(argv)

    records = enumerate_workflows()

    if args.json:
        output = json.dumps(
            {
                "schema": "m9-c65-workflow-inventory/v1",
                "generated_at": datetime.now(UTC).isoformat(),
                "total_workflows": len(records),
                "workflows": [r.to_dict() for r in records],
            },
            indent=2,
        )
    else:
        output = format_workflows_table(records)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"Written to {args.out}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(cmd_inspect_workflows(sys.argv[1:]))
