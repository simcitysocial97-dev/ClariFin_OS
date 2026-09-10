# runtime/foundation/verification/regression_detector.py
#
# Tier 1 — Regression Trend Detection.
#
# Compares current run metrics to historical baseline on a per-branch basis.
# Stores run metrics as JSON under runtime/generated/metrics/{branch}/{run_id}.json
# and maintains a branch index (last 100 runs) for baseline selection.

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from runtime.foundation.verification.config_loader import get_threshold

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
METRICS_DIR = REPO_ROOT / "runtime" / "generated" / "metrics"
MAX_RUNS_PER_BRANCH = 100


@dataclass(frozen=True)
class RunMetrics:
    """A single verification run's metric snapshot."""

    run_id: str
    timestamp: str
    branch: str
    commit_sha: str
    coverage_pct: float
    mutation_score: float
    test_count: int
    passed: int
    failed: int
    duration_seconds: float


@dataclass(frozen=True, slots=True)
class RegressionReport:
    """Result of comparing current metrics against a baseline."""

    has_regression: bool
    coverage_delta: float
    mutation_delta: float
    test_delta: int
    alerts: list[str]


class RegressionDetector:
    """Store run metrics and detect regressions against branch baselines."""

    def __init__(self, metrics_dir: Path | str | None = None) -> None:
        self.metrics_dir = Path(metrics_dir) if metrics_dir is not None else METRICS_DIR

    # ── Storage ──────────────────────────────────────────────────────────────

    def store_run_metrics(
        self,
        run_id: str,
        branch: str,
        metrics: dict[str, Any],
    ) -> None:
        """Persist a run's metrics to runtime/generated/metrics/{branch}/{run_id}.json.

        Args:
            run_id: Unique identifier for this run.
            branch: Git branch name.
            metrics: Dict with keys matching RunMetrics fields.
        """
        branch_dir = self.metrics_dir / branch
        branch_dir.mkdir(parents=True, exist_ok=True)

        run_file = branch_dir / f"{run_id}.json"
        payload = {
            "run_id": metrics.get("run_id", run_id),
            "timestamp": metrics.get(
                "timestamp", datetime.now(UTC).isoformat()
            ),
            "branch": branch,
            "commit_sha": metrics.get("commit_sha", ""),
            "coverage_pct": float(metrics.get("coverage_pct", 0.0)),
            "mutation_score": float(metrics.get("mutation_score", 0.0)),
            "test_count": int(metrics.get("test_count", 0)),
            "passed": int(metrics.get("passed", 0)),
            "failed": int(metrics.get("failed", 0)),
            "duration_seconds": float(metrics.get("duration_seconds", 0.0)),
        }
        run_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        self._append_to_index(branch, run_id, payload["timestamp"])

    def _index_path(self, branch: str) -> Path:
        return self.metrics_dir / branch / ".index.json"

    def _load_index(self, branch: str) -> list[dict[str, str]]:
        idx_path = self._index_path(branch)
        if not idx_path.exists():
            return []
        try:
            return json.loads(idx_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _append_to_index(
        self, branch: str, run_id: str, timestamp: str
    ) -> None:
        entries = self._load_index(branch)
        entry = {"run_id": run_id, "timestamp": timestamp}
        entries.append(entry)
        entries.sort(key=lambda e: e["timestamp"], reverse=True)
        entries = entries[:MAX_RUNS_PER_BRANCH]
        self._index_path(branch).write_text(
            json.dumps(entries, indent=2) + "\n", encoding="utf-8"
        )

    # ── Baseline ─────────────────────────────────────────────────────────────

    def get_baseline_metrics(
        self, branch: str = "main"
    ) -> dict[str, Any] | None:
        """Return the most recent stored run on *branch*, or None."""
        entries = self._load_index(branch)
        for entry in entries:
            rid = entry.get("run_id", "")
            run_file = self.metrics_dir / branch / f"{rid}.json"
            if not run_file.exists():
                continue
            try:
                return json.loads(run_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
        return None

    # ── Detection ────────────────────────────────────────────────────────────

    @staticmethod
    def detect_regressions(
        current_metrics: RunMetrics | dict[str, Any],
        baseline_metrics: dict[str, Any],
    ) -> RegressionReport:
        """Compare current run metrics against baseline.

        Thresholds:
            coverage drop > 5%  → WARNING
            coverage drop > 10% → CRITICAL
            mutation drop > 10% → WARNING
            mutation drop > 15% → CRITICAL
            test count drop > 20% → WARNING
        """
        if isinstance(current_metrics, RunMetrics):
            cur = asdict(current_metrics)
        else:
            cur = current_metrics

        cov_base = float(baseline_metrics.get("coverage_pct", 0.0))
        mut_base = float(baseline_metrics.get("mutation_score", 0.0))
        tc_base = int(baseline_metrics.get("test_count", 0))

        cov_cur = float(cur.get("coverage_pct", 0.0))
        mut_cur = float(cur.get("mutation_score", 0.0))
        tc_cur = int(cur.get("test_count", 0))

        coverage_delta = cov_cur - cov_base
        mutation_delta = mut_cur - mut_base
        test_delta = tc_cur - tc_base

        alerts: list[str] = []

        cov_warn = float(get_threshold("regression_thresholds", "coverage_drop_warning", 5))
        cov_crit = float(get_threshold("regression_thresholds", "coverage_drop_critical", 10))
        mut_warn = float(get_threshold("regression_thresholds", "mutation_drop_warning", 10))
        mut_crit = float(get_threshold("regression_thresholds", "mutation_drop_critical", 15))
        tc_warn = float(get_threshold("regression_thresholds", "test_count_drop_warning", 20))

        if coverage_delta < -cov_crit:
            alerts.append(
                f"CRITICAL: Coverage dropped by {abs(coverage_delta):.1f}%"
            )
        elif coverage_delta < -cov_warn:
            alerts.append(
                f"WARNING: Coverage dropped by {abs(coverage_delta):.1f}%"
            )

        if mutation_delta < -mut_crit:
            alerts.append(
                f"CRITICAL: Mutation score dropped by {abs(mutation_delta):.1f}%"
            )
        elif mutation_delta < -mut_warn:
            alerts.append(
                f"WARNING: Mutation score dropped by {abs(mutation_delta):.1f}%"
            )

        if test_delta < 0 and tc_base > 0:
            pct_drop = abs(test_delta) / tc_base * 100
            if pct_drop > tc_warn:
                alerts.append(
                    f"WARNING: Test count dropped by {pct_drop:.1f}%"
                )

        return RegressionReport(
            has_regression=len(alerts) > 0,
            coverage_delta=round(coverage_delta, 2),
            mutation_delta=round(mutation_delta, 2),
            test_delta=test_delta,
            alerts=alerts,
        )

    # ── Alerting ─────────────────────────────────────────────────────────────

    def alert_on_regression(self, report: RegressionReport) -> None:
        """Log warnings for every alert in the report."""
        for alert in report.alerts:
            level = logging.WARNING if "WARNING" in alert else logging.ERROR
            logger.log(level, "Regression alert: %s", alert)
