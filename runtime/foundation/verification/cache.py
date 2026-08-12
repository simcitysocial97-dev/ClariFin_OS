"""VEA-5 M3 — Verification Cache Integrity.

Implements the cache contract defined in ``docs/verification/VEA5_EXECUTION_MODEL.md``
§12-§13 and the M3-C acceptance gate:

    Cached successful execution  -> PASS / exit 0
    Cached failed execution      -> FAIL / exit != 0
    Missing / corrupt evidence   -> re-execute or fail safely (never assume PASS)
    Fingerprint mismatch         -> do not reuse

The cache may optimise execution, but it must never transform a previously
recorded failure into success merely because the result was cached.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """The verdict produced by the cache replay logic."""

    reusable: bool
    overall_status: str | None  # "pass" | "fail" | None
    exit_code: int | None  # 0 | 1 | None (None means caller must decide)
    reason: str


@dataclass(frozen=True, slots=True)
class CachedVerdict:
    """Evidence recorded after one verification execution."""

    overall_status: str  # "pass" | "fail"
    passed: int
    failed: int
    skipped: int
    unit_statuses: tuple[tuple[str, str], ...] = ()  # (unit_id, status)


class VerificationCache:
    """Verification cache with explicit integrity contract.

    Keys are (commit, changed_files, profile). ``replay`` is the authoritative
    entry point: it returns a ``ReplayResult`` whose ``exit_code`` is derived
    from the stored ``overall_status`` and can never be 0 when the stored
    status is "fail".
    """

    def __init__(self, path: Path | str):
        self.path = Path(path)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")

    def is_valid(self, commit: str, changed_files: list[str], profile: str) -> bool:
        cache = self._load()
        if cache.get("last_commit") != commit:
            return False
        profiles = cache.get("profiles", {})
        raw = profiles.get(profile)
        if not raw or not isinstance(raw, dict):
            return False
        profile_changed = raw.get("changed_files")
        if profile_changed is not None:
            return profile_changed == changed_files
        return cache.get("changed_files") == changed_files

    def get_verdict(self, profile: str) -> CachedVerdict | None:
        cache = self._load()
        profiles = cache.get("profiles", {})
        raw = profiles.get(profile)
        if not raw or not isinstance(raw, dict):
            return None
        status = raw.get("overall_status")
        if status not in ("pass", "fail"):
            return None
        return CachedVerdict(
            overall_status=status,
            passed=int(raw.get("passed", 0)),
            failed=int(raw.get("failed", 0)),
            skipped=int(raw.get("skipped", 0)),
            unit_statuses=tuple(raw.get("unit_statuses", [])),
        )

    def replay(self, commit: str, changed_files: list[str], profile: str) -> ReplayResult:
        """Return the cache replay verdict.

        The ``exit_code`` is derived from the stored ``overall_status`` and
        can never be 0 when the stored status is ``"fail"``.
        """
        if not self.is_valid(commit, changed_files, profile):
            return ReplayResult(
                reusable=False,
                overall_status=None,
                exit_code=None,
                reason="cache-invalid-or-missing",
            )
        verdict = self.get_verdict(profile)
        if verdict is None:
            return ReplayResult(
                reusable=False,
                overall_status=None,
                exit_code=None,
                reason="cache-corrupt-missing-status",
            )
        exit_code = 0 if verdict.overall_status == "pass" else 1
        return ReplayResult(
            reusable=True,
            overall_status=verdict.overall_status,
            exit_code=exit_code,
            reason=f"replay-{verdict.overall_status}",
        )

    def save(
        self,
        profile: str,
        commit: str,
        changed_files: list[str],
        verdict: CachedVerdict,
        duration: float = 0.0,
    ) -> None:
        cache = self._load()
        cache.setdefault("profiles", {})
        cache["last_commit"] = commit
        cache["changed_files"] = changed_files
        cache.setdefault("executed_profiles", [])
        if profile not in cache["executed_profiles"]:
            cache["executed_profiles"].append(profile)
        cache["duration"] = duration
        cache["timestamp"] = __import__("datetime").datetime.now(
            tz=__import__("datetime").timezone.utc
        ).isoformat()
        cache["profiles"][profile] = {
            "overall_status": verdict.overall_status,
            "passed": verdict.passed,
            "failed": verdict.failed,
            "skipped": verdict.skipped,
            "unit_statuses": list(verdict.unit_statuses),
            "changed_files": changed_files,
        }
        self._save(cache)
