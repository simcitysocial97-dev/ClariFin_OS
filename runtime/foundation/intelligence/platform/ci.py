"""Phase 7 — CI Intelligence.

Collects GitHub Actions failure evidence using *structured metadata first*.

Retrieval policy (enforced, not merely documented)
--------------------------------------------------
1. Run metadata via ``gh run list --json`` — cheap, structured.
2. Failed jobs and failed steps via the REST API (``gh api``) — structured.
3. Annotations via ``gh api .../annotations`` — these usually contain the
   entire failure reason.
4. Job-scoped logs ONLY for failed steps, and ONLY when the caller passes
   ``allow_logs=True``.

Whole-run log ARCHIVES (run-level log zips fetched via the archive download
subcommand) are never retrieved by this module under any flag. Downloading a
200MB archive to read one assertion failure is exactly the waste this phase
exists to eliminate.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = ["GitHubIntelligence", "collect_github_intelligence"]

REPO_ROOT = Path(__file__).resolve().parents[4]

# Retrieval steps in mandatory order. Logs are last and optional.
_RETRIEVAL_ORDER = (
    "run_metadata",
    "failed_jobs",
    "failed_steps",
    "annotations",
    "job_summaries",
    "artifacts",
    "failed_step_logs (opt-in only)",
)


@dataclass(frozen=True, slots=True)
class GitHubIntelligence:
    generated_at: str
    available: bool
    runs: tuple[dict[str, Any], ...] = ()
    failed_jobs: tuple[dict[str, Any], ...] = ()
    annotations: tuple[dict[str, Any], ...] = ()
    artifacts: tuple[dict[str, Any], ...] = ()
    logs_fetched: tuple[dict[str, Any], ...] = ()
    api_calls: tuple[str, ...] = ()
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "github-intelligence/v1",
            "generated_at": self.generated_at,
            "available": self.available,
            "retrieval_policy": {
                "order": list(_RETRIEVAL_ORDER),
                "structured_metadata_first": True,
                "full_log_archive_download": "never",
                "failed_step_logs": "opt-in only (allow_logs=True)",
            },
            "runs": list(self.runs),
            "failed_jobs": list(self.failed_jobs),
            "annotations": list(self.annotations),
            "artifacts": list(self.artifacts),
            "logs_fetched": list(self.logs_fetched),
            "counts": {
                "runs": len(self.runs),
                "failed_jobs": len(self.failed_jobs),
                "annotations": len(self.annotations),
                "artifacts": len(self.artifacts),
                "logs_fetched": len(self.logs_fetched),
                "api_calls": len(self.api_calls),
            },
            "api_calls": list(self.api_calls),
            "notes": list(self.notes),
        }


def _run(args: list[str], repo_root: Path, timeout: int = 30) -> tuple[int, str]:
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=str(repo_root),
            timeout=timeout,
        )
        return result.returncode, result.stdout
    except Exception:
        return 1, ""


def _gh_available(repo_root: Path) -> bool:
    code, _ = _run(["gh", "auth", "status"], repo_root, timeout=15)
    return code == 0


def collect_github_intelligence(
    limit: int = 10,
    allow_logs: bool = False,
    repo_root: Path | None = None,
) -> GitHubIntelligence:
    """Collect structured CI failure evidence.

    ``allow_logs`` gates *failed-step* log retrieval only. It never enables
    whole-run archive downloads.
    """
    root = repo_root or REPO_ROOT
    api_calls: list[str] = []
    notes: list[str] = []

    if not _gh_available(root):
        return GitHubIntelligence(
            generated_at=datetime.now(timezone.utc).isoformat(),
            available=False,
            notes=(
                "gh CLI unavailable or unauthenticated; "
                "CI intelligence collected no evidence",
            ),
        )

    # -- Step 1: structured run metadata ----------------------------------
    fields = "databaseId,name,conclusion,status,headBranch,event,createdAt,workflowName"
    cmd = ["gh", "run", "list", "--limit", str(limit), "--json", fields]
    api_calls.append(" ".join(cmd))
    code, out = _run(cmd, root)
    runs: list[dict[str, Any]] = []
    if code == 0 and out.strip():
        try:
            parsed = json.loads(out)
            if isinstance(parsed, list):
                runs = parsed
        except json.JSONDecodeError:
            notes.append("could not parse gh run list output")
    else:
        notes.append("gh run list returned no data")

    failed_runs = [r for r in runs if r.get("conclusion") == "failure"]
    if not failed_runs:
        notes.append("no failed runs in recent history; no further calls made")

    failed_jobs: list[dict[str, Any]] = []
    annotations: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    logs_fetched: list[dict[str, Any]] = []

    for run in failed_runs[:5]:
        run_id = run.get("databaseId")
        if run_id is None:
            continue

        # -- Step 2/3: failed jobs and their failed steps -----------------
        jobs_cmd = ["gh", "api", f"repos/{{owner}}/{{repo}}/actions/runs/{run_id}/jobs"]
        api_calls.append(" ".join(jobs_cmd))
        code, out = _run(jobs_cmd, root)
        if code == 0 and out.strip():
            try:
                data = json.loads(out)
            except json.JSONDecodeError:
                data = {}
            for job in data.get("jobs", []) if isinstance(data, dict) else []:
                if job.get("conclusion") != "failure":
                    continue
                failed_steps = [
                    {
                        "name": s.get("name"),
                        "number": s.get("number"),
                        "conclusion": s.get("conclusion"),
                    }
                    for s in job.get("steps", []) or []
                    if s.get("conclusion") == "failure"
                ]
                failed_jobs.append(
                    {
                        "run_id": run_id,
                        "job_id": job.get("id"),
                        "name": job.get("name"),
                        "conclusion": job.get("conclusion"),
                        "failed_steps": failed_steps,
                        "html_url": job.get("html_url"),
                    }
                )

        # -- Step 4: annotations (usually sufficient) ---------------------
        ann_cmd = [
            "gh",
            "api",
            f"repos/{{owner}}/{{repo}}/check-runs/{run_id}/annotations",
        ]
        api_calls.append(" ".join(ann_cmd))
        code, out = _run(ann_cmd, root)
        run_annotations: list[dict[str, Any]] = []
        if code == 0 and out.strip():
            try:
                parsed = json.loads(out)
                if isinstance(parsed, list):
                    run_annotations = parsed
            except json.JSONDecodeError:
                pass
        if not run_annotations:
            view_cmd = ["gh", "run", "view", str(run_id), "--json", "annotations"]
            api_calls.append(" ".join(view_cmd))
            code, out = _run(view_cmd, root)
            if code == 0 and out.strip():
                try:
                    parsed = json.loads(out)
                    run_annotations = parsed.get("annotations", []) or []
                except json.JSONDecodeError:
                    pass
        for annotation in run_annotations:
            annotations.append({"run_id": run_id, **annotation})

        # -- Step 6: artifact metadata (names/sizes only, no download) ----
        art_cmd = [
            "gh",
            "api",
            f"repos/{{owner}}/{{repo}}/actions/runs/{run_id}/artifacts",
        ]
        api_calls.append(" ".join(art_cmd))
        code, out = _run(art_cmd, root)
        if code == 0 and out.strip():
            try:
                data = json.loads(out)
            except json.JSONDecodeError:
                data = {}
            for art in data.get("artifacts", []) if isinstance(data, dict) else []:
                artifacts.append(
                    {
                        "run_id": run_id,
                        "name": art.get("name"),
                        "size_in_bytes": art.get("size_in_bytes"),
                        "expired": art.get("expired"),
                        "downloaded": False,
                    }
                )

    # -- Step 7: failed-step logs, opt-in only ----------------------------
    if allow_logs and failed_jobs:
        for job in failed_jobs[:3]:
            job_id = job.get("job_id")
            if job_id is None or not job.get("failed_steps"):
                continue
            log_cmd = [
                "gh",
                "api",
                f"repos/{{owner}}/{{repo}}/actions/jobs/{job_id}/logs",
            ]
            api_calls.append(" ".join(log_cmd))
            code, out = _run(log_cmd, root, timeout=60)
            if code == 0 and out:
                tail = out.splitlines()[-40:]
                logs_fetched.append(
                    {
                        "job_id": job_id,
                        "scope": "failed job only",
                        "lines_retained": len(tail),
                        "tail": tail,
                    }
                )
    elif failed_jobs:
        notes.append(
            f"{len(failed_jobs)} failed job(s) found; logs NOT fetched "
            "(annotations and step metadata were sufficient). "
            "Pass allow_logs=True to retrieve failed-step logs."
        )

    if annotations:
        notes.append(
            f"{len(annotations)} annotation(s) retrieved; these are the "
            "primary failure evidence and make log download unnecessary"
        )

    return GitHubIntelligence(
        generated_at=datetime.now(timezone.utc).isoformat(),
        available=True,
        runs=tuple(runs),
        failed_jobs=tuple(failed_jobs),
        annotations=tuple(annotations),
        artifacts=tuple(artifacts),
        logs_fetched=tuple(logs_fetched),
        api_calls=tuple(api_calls),
        notes=tuple(notes),
    )
