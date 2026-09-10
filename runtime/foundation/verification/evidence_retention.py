"""
M9-C55 — Evidence Retention Policy & Cleanup.

Manages the lifecycle of artifacts in runtime/generated/ by enforcing
retention policies per category. Prevents indefinite growth during local
development while preserving current-run evidence and anything referenced
by active caches.

Retention categories (days):
    milestones  — m9-c*/  directories (certification artifacts)  → 90
    logs        — m9-c49/logs/ (execution logs)                 → 30
    cache       — verification-cache.json                       → 7
    metrics     — metrics/                                      → 90
    ai-runs     — ai-runs/                                      → 30
    evidence    — evidence/                                     → 60
"""
from __future__ import annotations

import json
import re
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GENERATED_DIR = REPO_ROOT / "runtime" / "generated"

# Default retention policy: category_name → max_age_days
DEFAULT_RETENTION_POLICY: dict[str, int] = {
    "milestones": 90,
    "logs": 30,
    "cache": 7,
    "metrics": 90,
    "ai-runs": 30,
    "evidence": 60,
}

# Regex patterns for category classification
_RE_MILESTONE_DIR = re.compile(r"^m9-c\d+(?:\.\d+)?/?$")
_RE_LOG_DIR = re.compile(r"^m9-c49/logs/?$")
_RE_METRICS_DIR = re.compile(r"^metrics/?$")
_RE_AI_RUNS_DIR = re.compile(r"^ai-runs/?$")
_RE_EVIDENCE_DIR = re.compile(r"^evidence/?$")


@dataclass(frozen=True, slots=True)
class ExpiredArtifact:
    """An artifact identified as expired by the retention policy."""

    path: str
    category: str
    age_days: int
    size_bytes: int


@dataclass(frozen=True, slots=True)
class CleanupReport:
    """Result of a cleanup pass."""

    scanned: int
    expired: int
    deleted: int
    freed_bytes: int
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scanned": self.scanned,
            "expired": self.expired,
            "deleted": self.deleted,
            "freed_bytes": self.freed_bytes,
            "errors": self.errors,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


class EvidenceRetention:
    """Scans and cleans up runtime/generated/ according to retention policies."""

    def __init__(
        self,
        generated_dir: Path | None = None,
        retention_policy: dict[str, int] | None = None,
    ):
        self._generated_dir = generated_dir or GENERATED_DIR
        self._policy = retention_policy or DEFAULT_RETENTION_POLICY
        self._now_ts = time.time()

    def get_retention_config(self) -> dict[str, int]:
        """Return the active retention policy (category → max_age_days)."""
        return dict(self._policy)

    def _classify(self, path: Path) -> str | None:
        """Return the category for a path, or None if unmanaged."""
        if not path.is_relative_to(self._generated_dir):
            return None
        name = path.name
        # Directories first
        for category, pattern in [
            ("milestones", _RE_MILESTONE_DIR),
            ("logs", _RE_LOG_DIR),
            ("metrics", _RE_METRICS_DIR),
            ("ai-runs", _RE_AI_RUNS_DIR),
            ("evidence", _RE_EVIDENCE_DIR),
        ]:
            if pattern.match(name) and path.is_dir():
                return category
        # File-level rules
        rel = path.relative_to(self._generated_dir)
        if rel.name == "verification-cache.json":
            return "cache"
        return None

    def _age_days(self, path: Path) -> int:
        """Return the age of a path in days based on modification time."""
        try:
            mtime = path.stat().st_mtime
            return int((self._now_ts - mtime) / 86400)
        except OSError:
            return 0

    def _size_bytes(self, path: Path) -> int:
        """Return size in bytes (directory size via walk)."""
        if path.is_file():
            try:
                return path.stat().st_size
            except OSError:
                return 0
        total = 0
        try:
            for dirpath, _, filenames in path.walk(top_down=False):
                for f in filenames:
                    fp = dirpath / f
                    try:
                        total += fp.stat().st_size
                    except OSError:
                        pass
        except OSError:
            pass
        return total

    def _is_current_run(self, path: Path) -> bool:
        """Heuristic: mark paths touched within the last 1 day as current run."""
        try:
            mtime = path.stat().st_mtime
            return (self._now_ts - mtime) < 86400  # 1 day
        except OSError:
            return False

    def scan_expired(self, dry_run: bool = True) -> list[ExpiredArtifact]:
        """Scan generated/ and return list of expired artifacts.

        Args:
            dry_run: If True, only report; do not delete.

        Returns:
            List of ExpiredArtifact for every path exceeding its category's
            retention period.
        """
        expired: list[ExpiredArtifact] = []
        if not self._generated_dir.exists():
            return expired

        for child in sorted(self._generated_dir.iterdir()):
            try:
                cat = self._classify(child)
                if cat is None:
                    continue
                age = self._age_days(child)
                max_days = self._policy.get(cat)
                if max_days is None:
                    continue
                if age > max_days and not self._is_current_run(child):
                    size = self._size_bytes(child)
                    expired.append(
                        ExpiredArtifact(
                            path=str(child.relative_to(REPO_ROOT)),
                            category=cat,
                            age_days=age,
                            size_bytes=size,
                        )
                    )
            except OSError:
                pass  # skip inaccessible paths

        return expired

    def cleanup(self, dry_run: bool = True) -> CleanupReport:
        """Execute cleanup of expired artifacts.

        Args:
            dry_run: If True, report what would be deleted without deleting.

        Returns:
            CleanupReport with counts and details.
        """
        expired = self.scan_expired(dry_run=False)
        deleted = 0
        freed = 0
        errors: list[str] = []

        for artifact in expired:
            path = REPO_ROOT / artifact.path
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                elif path.is_file():
                    path.unlink()
                deleted += 1
                freed += artifact.size_bytes
            except OSError as e:
                errors.append(f"{artifact.path}: {e}")

        return CleanupReport(
            scanned=len(expired) + deleted,
            expired=len(expired),
            deleted=deleted,
            freed_bytes=freed,
            errors=errors,
        )

    def format_report(self, report: CleanupReport, dry_run: bool = True) -> str:
        """Human-readable report from a CleanupReport."""
        status = "DRY RUN — no files deleted" if dry_run else "EXECUTED"
        lines = [
            f"Evidence Retention Report [{status}]",
            f"  Generated at: {datetime.now(timezone.utc).isoformat()}",
            f"  Scanned:      {report.scanned} paths",
            f"  Expired:      {report.expired} paths",
            f"  Deleted:      {report.deleted} paths",
            f"  Freed:        {report.freed_bytes:,} bytes",
        ]
        if report.errors:
            lines.append(f"  Errors:       {len(report.errors)}")
            for err in report.errors[:10]:
                lines.append(f"    - {err}")
        return "\n".join(lines)


def cmd_evidence_cleanup(args: list[str]) -> int:
    """CLI entry-point for `verify inspect evidence-cleanup`."""
    dry_run = "--execute" not in args

    retention = EvidenceRetention()
    config = retention.get_retention_config()

    print("Evidence Retention Policy:")
    for cat, days in sorted(config.items()):
        print(f"  {cat:12s} → {days} days")
    print()

    if dry_run:
        print("Mode: DRY RUN (use --execute to apply cleanup)")
        print()

    expired = retention.scan_expired(dry_run=dry_run)

    if expired:
        print(f"Expired artifacts ({len(expired)}):")
        for a in sorted(expired, key=lambda x: (-x.age_days, x.category)):
            size_kb = a.size_bytes / 1024
            print(
                f"  [{a.category:10s}] age={a.age_days:4d}d  "
                f"size={size_kb:8.1f}KB  {a.path}"
            )
    else:
        print("No expired artifacts found.")

    report = retention.cleanup(dry_run=dry_run)
    print()
    print(retention.format_report(report, dry_run=dry_run))

    return 0
