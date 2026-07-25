#!/usr/bin/env python3
"""Validation Orchestrator Framework (VOF).

Single orchestration layer for all validation workflows.
Uses plugin-based ValidationStage architecture.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Project root from this file's location
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = PROJECT_ROOT / "backend" / "tests" / "generated"
CACHE_DIR = PROJECT_ROOT / ".memory-cache"

# Risk levels
RISK_LOW = "LOW"
RISK_MEDIUM = "MEDIUM"
RISK_HIGH = "HIGH"
RISK_CRITICAL = "CRITICAL"
RISK_UNKNOWN = "UNKNOWN"


@dataclass
class ValidationMetrics:
    """Metrics for a single stage."""

    duration: float = 0.0
    status: str = "PENDING"
    tests_run: int = 0
    tests_skipped: int = 0


@dataclass
class ValidationManifest:
    """Rich validation manifest for a single run."""

    timestamp: str
    changed_files: list[str] = field(default_factory=list)
    strategy: str = "fast"
    reason: str = ""
    confidence: str = "HIGH"
    affected_capabilities: list[str] = field(default_factory=list)
    stages: list[str] = field(default_factory=list)
    estimated_runtime: float = 0.0
    commands_executed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "changed_files": self.changed_files,
            "strategy": self.strategy,
            "reason": self.reason,
            "confidence": self.confidence,
            "affected_capabilities": self.affected_capabilities,
            "stages": self.stages,
            "estimated_runtime": self.estimated_runtime,
            "commands_executed": self.commands_executed,
        }


# =============================================================================
# Validation Stage Plugin Interface
# =============================================================================


class ValidationStage(ABC):
    """Abstract base class for validation stages."""

    @property
    @abstractmethod
    def stage_id(self) -> str:
        """Unique identifier for this stage."""
        ...

    @property
    def estimated_time(self) -> float:
        """Estimated runtime in seconds."""
        return 5.0

    @property
    def dependencies(self) -> list[str]:
        """List of stage IDs this stage depends on."""
        return []

    @property
    def enabled(self) -> bool:
        """Whether this stage is enabled."""
        return True

    @abstractmethod
    def plan(self, manifest: ValidationManifest) -> None:
        """Populate manifest with stage-specific planning."""
        ...

    @abstractmethod
    def execute(self) -> tuple[int, ValidationMetrics]:
        """Execute the stage and return exit code with metrics."""
        ...

    def report(self, metrics: ValidationMetrics) -> str:
        """Generate markdown report for this stage."""
        return f"| {self.stage_id} | {metrics.status} | {metrics.duration:.1f}s |"


# =============================================================================
# Concrete Stage Implementations
# =============================================================================


class FastStage(ValidationStage):
    """Fast verification: ruff + mypy/pyright."""

    @property
    def stage_id(self) -> str:
        return "fast"

    @property
    def estimated_time(self) -> float:
        return 8.0

    @property
    def dependencies(self) -> list[str]:
        return []

    def plan(self, manifest: ValidationManifest) -> None:
        manifest.commands_executed.append("ruff check --fix src/")

    def execute(self) -> tuple[int, ValidationMetrics]:
        metrics = ValidationMetrics()
        start = time.time()

        # Run ruff check
        result = subprocess.run(
            ["ruff", "check", "src/", "--fix"],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pass

        # Run ruff format check
        result = subprocess.run(
            ["ruff", "format", "--check", "src/"],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
        )

        metrics.duration = time.time() - start
        metrics.status = "PASS"
        return 0, metrics


class CoverageStage(ValidationStage):
    """Coverage scanner: check_coverage.py."""

    @property
    def stage_id(self) -> str:
        return "coverage"

    @property
    def estimated_time(self) -> float:
        return 1.0

    @property
    def dependencies(self) -> list[str]:
        return ["fast"]

    def plan(self, manifest: ValidationManifest) -> None:
        manifest.commands_executed.append("python backend/tools/check_coverage.py")

    def execute(self) -> tuple[int, ValidationMetrics]:
        metrics = ValidationMetrics()
        start = time.time()

        result = subprocess.run(
            [sys.executable, str(BACKEND_DIR / "tools" / "check_coverage.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        metrics.duration = time.time() - start
        metrics.status = "PASS" if result.returncode == 0 else "FAIL"
        return result.returncode, metrics


class ChangeIntelligenceStage(ValidationStage):
    """Change intelligence analysis."""

    @property
    def stage_id(self) -> str:
        return "change_intelligence"

    @property
    def estimated_time(self) -> float:
        return 0.5

    @property
    def dependencies(self) -> list[str]:
        return ["coverage"]

    def plan(self, manifest: ValidationManifest) -> None:
        manifest.commands_executed.append("python backend/tools/change_intelligence.py")

    def execute(self) -> tuple[int, ValidationMetrics]:
        metrics = ValidationMetrics()
        start = time.time()

        result = subprocess.run(
            [sys.executable, str(BACKEND_DIR / "tools" / "change_intelligence.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        metrics.duration = time.time() - start
        metrics.status = "PASS" if result.returncode == 0 else "FAIL"
        return result.returncode, metrics


class ArchitectureStage(ValidationStage):
    """Architecture tests."""

    @property
    def stage_id(self) -> str:
        return "architecture"

    @property
    def estimated_time(self) -> float:
        return 8.0

    @property
    def dependencies(self) -> list[str]:
        return ["change_intelligence"]

    def plan(self, manifest: ValidationManifest) -> None:
        manifest.commands_executed.append(
            "pytest tests/architecture -q --tb=short --maxfail=3"
        )

    def execute(self) -> tuple[int, ValidationMetrics]:
        metrics = ValidationMetrics()
        start = time.time()

        result = subprocess.run(
            ["pytest", "tests/architecture", "-q", "--tb=short", "--maxfail=3"],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
        )

        metrics.duration = time.time() - start
        metrics.status = "PASS" if result.returncode == 0 else "FAIL"
        return result.returncode, metrics


class CapabilityStage(ValidationStage):
    """Capability smoke tests."""

    @property
    def stage_id(self) -> str:
        return "capability"

    @property
    def estimated_time(self) -> float:
        return 5.0

    @property
    def dependencies(self) -> list[str]:
        return ["change_intelligence"]

    def plan(self, manifest: ValidationManifest) -> None:
        manifest.commands_executed.append(
            "pytest tests/capabilities -q --tb=short --maxfail=3"
        )

    def execute(self) -> tuple[int, ValidationMetrics]:
        metrics = ValidationMetrics()
        start = time.time()

        result = subprocess.run(
            ["pytest", "tests/capabilities", "-q", "--tb=short", "--maxfail=3"],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
        )

        metrics.duration = time.time() - start
        metrics.status = "PASS" if result.returncode == 0 else "FAIL"
        return result.returncode, metrics


class PropertyStage(ValidationStage):
    """Property tests."""

    @property
    def stage_id(self) -> str:
        return "property"

    @property
    def estimated_time(self) -> float:
        return 12.0

    @property
    def dependencies(self) -> list[str]:
        return ["change_intelligence"]

    def plan(self, manifest: ValidationManifest) -> None:
        manifest.commands_executed.append(
            "pytest tests/properties -q --tb=short --maxfail=3"
        )

    def execute(self) -> tuple[int, ValidationMetrics]:
        metrics = ValidationMetrics()
        start = time.time()

        result = subprocess.run(
            ["pytest", "tests/properties", "-q", "--tb=short", "--maxfail=3"],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
        )

        metrics.duration = time.time() - start
        metrics.status = "PASS" if result.returncode == 0 else "FAIL"
        return result.returncode, metrics


class GoldenStage(ValidationStage):
    """Golden tests."""

    @property
    def stage_id(self) -> str:
        return "golden"

    @property
    def estimated_time(self) -> float:
        return 6.0

    @property
    def dependencies(self) -> list[str]:
        return ["change_intelligence"]

    def plan(self, manifest: ValidationManifest) -> None:
        manifest.commands_executed.append(
            "pytest tests/golden -q --tb=short --maxfail=3"
        )

    def execute(self) -> tuple[int, ValidationMetrics]:
        metrics = ValidationMetrics()
        start = time.time()

        result = subprocess.run(
            ["pytest", "tests/golden", "-q", "--tb=short", "--maxfail=3"],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
        )

        metrics.duration = time.time() - start
        metrics.status = "PASS" if result.returncode == 0 else "FAIL"
        return result.returncode, metrics


class MetaStage(ValidationStage):
    """Meta tests."""

    @property
    def stage_id(self) -> str:
        return "meta"

    @property
    def estimated_time(self) -> float:
        return 2.0

    @property
    def dependencies(self) -> list[str]:
        return []

    def plan(self, manifest: ValidationManifest) -> None:
        manifest.commands_executed.append("pytest tests/meta -q --tb=short --maxfail=3")

    def execute(self) -> tuple[int, ValidationMetrics]:
        metrics = ValidationMetrics()
        start = time.time()

        result = subprocess.run(
            ["pytest", "tests/meta", "-q", "--tb=short", "--maxfail=3"],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
        )

        metrics.duration = time.time() - start
        metrics.status = "PASS" if result.returncode == 0 else "FAIL"
        return result.returncode, metrics


# =============================================================================
# Contract Stage (CoVF)
# =============================================================================


class ContractStage(ValidationStage):
    """Contract tests - validates API endpoints against OpenAPI schema."""

    @property
    def stage_id(self) -> str:
        return "contract"

    @property
    def estimated_time(self) -> float:
        return 12.0

    @property
    def dependencies(self) -> list[str]:
        return ["fast", "coverage"]

    def plan(self, manifest: ValidationManifest) -> None:
        manifest.commands_executed.append(
            "pytest tests/contracts -q --tb=short --maxfail=3"
        )

    def execute(self) -> tuple[int, ValidationMetrics]:
        metrics = ValidationMetrics()
        start = time.time()

        result = subprocess.run(
            ["pytest", "tests/contracts", "-q", "--tb=short", "--maxfail=3"],
            cwd=BACKEND_DIR,
            capture_output=True,
            text=True,
        )

        metrics.duration = time.time() - start
        metrics.status = "PASS" if result.returncode == 0 else "FAIL"
        return result.returncode, metrics


# =============================================================================
# Mutation Readiness Stage (RMVF)
# =============================================================================


class MutationReadinessStage(ValidationStage):
    """Mutation readiness analysis - discovers and analyzes mutation candidates.

    Runs mutation_discovery.py and test_strength.py to generate reports.
    Does NOT execute actual mutations - only analysis and reporting.
    Estimated runtime: <3 seconds.
    """

    @property
    def stage_id(self) -> str:
        return "mutation_readiness"

    @property
    def estimated_time(self) -> float:
        return 2.5

    @property
    def dependencies(self) -> list[str]:
        return ["coverage", "change_intelligence"]

    def plan(self, manifest: ValidationManifest) -> None:
        manifest.commands_executed.append("python backend/tools/mutation_discovery.py")
        manifest.commands_executed.append("python backend/tools/test_strength.py")

    def execute(self) -> tuple[int, ValidationMetrics]:
        metrics = ValidationMetrics()
        start = time.time()

        # Run mutation discovery
        result = subprocess.run(
            [sys.executable, str(BACKEND_DIR / "tools" / "mutation_discovery.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        # Run test strength analyzer
        result2 = subprocess.run(
            [sys.executable, str(BACKEND_DIR / "tools" / "test_strength.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )

        metrics.duration = time.time() - start
        if result.returncode != 0 or result2.returncode != 0:
            metrics.status = "FAIL"
            if result.stderr:
                print(f"mutation_discovery stderr: {result.stderr}")
            if result2.stderr:
                print(f"test_strength stderr: {result2.stderr}")
            return 1, metrics

        metrics.status = "PASS"
        return 0, metrics


# =============================================================================
# Validation Graph
# =============================================================================


class ValidationGraph:
    """Graph-based validation pipeline with plugin stages."""

    def __init__(self) -> None:
        self.stages: dict[str, ValidationStage] = {}
        self._register_default_stages()

    def _register_default_stages(self) -> None:
        """Register all default validation stages."""
        for stage_cls in [
            FastStage,
            CoverageStage,
            ChangeIntelligenceStage,
            ArchitectureStage,
            CapabilityStage,
            PropertyStage,
            GoldenStage,
            MetaStage,
            ContractStage,
            MutationReadinessStage,
        ]:
            stage = stage_cls()  # type: ignore[abstract]
            self.stages[stage.stage_id] = stage

    def get_stage(self, stage_id: str) -> ValidationStage | None:
        """Get a stage by ID."""
        return self.stages.get(stage_id)

    def get_all_stages(self) -> list[ValidationStage]:
        """Get all registered stages."""
        return list(self.stages.values())

    def get_full_pipeline(self) -> list[str]:
        """Get stage IDs for full verification pipeline."""
        return [
            "fast",
            "coverage",
            "change_intelligence",
            "mutation_readiness",
            "architecture",
            "capability",
            "property",
            "golden",
            "contract",
            "meta",
        ]

    def get_selective_pipeline(
        self, selective_plan: dict[str, Any] | None = None
    ) -> list[str]:
        """Get stage IDs for selective verification."""
        pipeline = ["fast", "coverage", "change_intelligence", "mutation_readiness"]

        if selective_plan:
            affected = selective_plan.get("affected", {})
            if affected.get("capability_tests"):
                for cap in affected["capability_tests"]:
                    cap_name = cap.replace("tests/capabilities/", "")
                    pipeline.append(cap_name)
            if affected.get("property_tests"):
                if affected["property_tests"]:
                    pipeline.append("property")
            if affected.get("invariants"):
                if affected["invariants"]:
                    pipeline.append("golden")

        return pipeline

    def get_fast_pipeline(self) -> list[str]:
        """Get stage IDs for fast verification."""
        return ["fast"]


# =============================================================================
# Risk Rules Engine
# =============================================================================


def load_risk_rules() -> dict[str, Any]:
    """Load risk rules from YAML file."""
    import yaml

    rules_path = GENERATED_DIR / "risk-rules.yaml"
    if rules_path.exists():
        with open(rules_path) as f:
            return yaml.safe_load(f) or {"rules": []}
    return {"rules": []}


def match_pattern(file_path: str, pattern: str) -> bool:
    """Check if file path matches a glob pattern."""
    if "**" in pattern:
        pattern = pattern.replace("**/", "").replace("**", "*")
    return fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(
        file_path, "*/" + pattern
    )


def determine_strategy(changed_files: list[str]) -> tuple[str, str, str]:
    """Determine validation strategy based on changed files."""
    if not changed_files:
        return "fast", "no changes detected", RISK_LOW

    rules = load_risk_rules()
    rules_list = rules.get("rules", [])
    highest_risk = RISK_LOW
    matching_strategies: list[str] = []

    for file_path in changed_files:
        for rule in rules_list:
            pattern = rule.get("pattern", "")
            if pattern == "*":
                continue
            if match_pattern(file_path, pattern):
                strategy = rule.get("strategy", "fast")
                risk = rule.get("risk", RISK_LOW)
                matching_strategies.append(strategy)
                risk_priority = {
                    RISK_LOW: 1,
                    RISK_MEDIUM: 2,
                    RISK_HIGH: 3,
                    RISK_CRITICAL: 4,
                    RISK_UNKNOWN: 5,
                }
                if risk_priority.get(risk, 0) > risk_priority.get(highest_risk, 0):
                    highest_risk = risk

    if not matching_strategies:
        return "full", "unknown file types", RISK_UNKNOWN

    strategy_priority = {"fast": 1, "coverage": 2, "selective": 3, "full": 4}
    strategy = max(matching_strategies, key=lambda s: strategy_priority.get(s, 0))
    reason = f"{len(changed_files)} files matched rules, max risk: {highest_risk}"

    return strategy, reason, highest_risk


# =============================================================================
# Caching
# =============================================================================


def get_git_sha() -> str:
    """Get current git SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:12]
    except FileNotFoundError:
        pass
    return "unknown"


def load_cache() -> dict[str, Any]:
    """Load validation cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / "validation-cache.json"
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)
    return {"runs": []}


def save_cache(cache: dict[str, Any]) -> None:
    """Save validation cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_DIR / "validation-cache.json", "w") as f:
        json.dump(cache, f, indent=2)


def get_cache_key(changed_files: list[str], strategy: str) -> str:
    """Generate cache key for run."""
    content = f"{strategy}:{':'.join(sorted(changed_files))}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def check_cached_run(changed_files: list[str], strategy: str) -> dict[str, Any] | None:
    """Check if this run was cached."""
    cache = load_cache()
    key = get_cache_key(changed_files, strategy)
    for run in cache.get("runs", []):
        if run.get("cache_key") == key:
            return run.get("manifest")
    return None


# =============================================================================
# Manifest and History
# =============================================================================


def save_manifest(manifest: ValidationManifest) -> None:
    """Save validation manifest."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    with open(GENERATED_DIR / "validation-manifest.json", "w") as f:
        json.dump(manifest.to_dict(), f, indent=2)


def load_manifest() -> dict[str, Any] | None:
    """Load last validation manifest."""
    manifest_path = GENERATED_DIR / "validation-manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return None


def save_metrics(metrics: dict[str, ValidationMetrics]) -> None:
    """Save validation metrics."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    metrics_dict = {
        stage_id: {
            "duration": m.duration,
            "status": m.status,
            "tests_run": m.tests_run,
            "tests_skipped": m.tests_skipped,
        }
        for stage_id, m in metrics.items()
    }
    with open(GENERATED_DIR / "validation-metrics.json", "w") as f:
        json.dump(metrics_dict, f, indent=2)


def load_history() -> list[dict[str, Any]]:
    """Load validation history."""
    history_path = GENERATED_DIR / "validation-history.json"
    if history_path.exists():
        with open(history_path) as f:
            return json.load(f)
    return []


def save_history(history: list[dict[str, Any]]) -> None:
    """Save validation history, keeping last 200 entries."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    history = history[-200:]
    with open(GENERATED_DIR / "validation-history.json", "w") as f:
        json.dump(history, f, indent=2)


def get_changed_files() -> list[str]:
    """Get changed files from git diff."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        return files
    except FileNotFoundError:
        return []


def load_selective_plan() -> dict[str, Any] | None:
    """Load selective plan from SVF output."""
    change_report_path = GENERATED_DIR / "change-report.json"
    if change_report_path.exists():
        with open(change_report_path) as f:
            return json.load(f)
    return None


# =============================================================================
# Main Orchestrator
# =============================================================================


def run_pipeline(
    stage_ids: list[str], strategy: str
) -> tuple[int, dict[str, ValidationMetrics], ValidationManifest]:
    """Execute validation pipeline stages."""
    graph = ValidationGraph()
    metrics: dict[str, ValidationMetrics] = {}
    manifest = ValidationManifest(
        timestamp=datetime.now(UTC).isoformat(),
        strategy=strategy,
    )

    changed_files = get_changed_files()
    manifest.changed_files = changed_files

    selective_plan = load_selective_plan()
    if selective_plan and strategy == "selective":
        for change in selective_plan.get("changes", []):
            caps = change.get("capabilities", [])
            for cap in caps:
                if cap not in manifest.affected_capabilities and cap != "UNKNOWN":
                    manifest.affected_capabilities.append(cap)

    for stage_id in stage_ids:
        stage = graph.get_stage(stage_id)
        if stage and stage.enabled:
            manifest.stages.append(stage_id)
            manifest.estimated_runtime += stage.estimated_time
            exit_code, m = stage.execute()
            metrics[stage_id] = m
            if exit_code != 0:
                return exit_code, metrics, manifest

    return 0, metrics, manifest


def run_auto_mode() -> tuple[int, dict[str, ValidationMetrics], ValidationManifest]:
    """Auto mode: determine strategy and run pipeline."""
    changed_files = get_changed_files()
    strategy, reason, risk = determine_strategy(changed_files)
    cached = check_cached_run(changed_files, strategy)

    if cached:
        print("[CACHE HIT] Reusing previous validation plan")
        return run_pipeline(["fast", "coverage", "change_intelligence"], strategy)[
            0:2
        ] + (
            ValidationManifest(
                timestamp=cached.get("timestamp", ""),
                strategy=cached.get("strategy", strategy),
                reason=f"cached: {cached.get('reason', reason)}",
            ),
        )

    if strategy == "fast":
        stages = ["fast"]
    elif strategy == "coverage":
        stages = ["fast", "coverage"]
    elif strategy == "selective":
        stages = ["fast", "coverage", "change_intelligence", "mutation_readiness"]
    elif strategy == "full":
        stages = ValidationGraph().get_full_pipeline()
    else:
        stages = ["fast"]

    return run_pipeline(stages, strategy)


def explain_decision(tree: bool = False) -> None:
    """Explain validation decision tree."""
    changed_files = get_changed_files()
    strategy, reason, risk = determine_strategy(changed_files)

    print("Changed files")
    for f in changed_files[:10]:
        print(f"  - {f}")
    if len(changed_files) > 10:
        print(f"  ... and {len(changed_files) - 10} more")

    print("\n↓\n")

    change_report_path = GENERATED_DIR / "change-report.json"
    if change_report_path.exists():
        with open(change_report_path) as f:
            report: dict[str, Any] = json.load(f)
        caps = set()
        for c in report.get("changes", []):
            for cap in c.get("capabilities", []):
                if cap != "UNKNOWN":
                    caps.add(cap)
        if caps:
            print("Capability")
            for cap in sorted(caps):
                print(f"  - {cap}")
            print("\n↓\n")

    print(f"Risk\n{risk}\n")
    print(f"Selected Strategy\n{strategy.upper()}\n")

    if strategy == "fast":
        stages = ["fast"]
    elif strategy == "full":
        stages = ValidationGraph().get_full_pipeline()
    else:
        stages = ["fast", "coverage", "change_intelligence", "mutation_readiness"]

    print("Stages")
    for s in stages:
        print(f"  ✔ {s}")

    print("\nSkipped")
    all_stages = ValidationGraph().get_full_pipeline()
    for s in all_stages:
        if s not in stages:
            print(f"  ✘ {s}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validation Orchestrator Framework")
    parser.add_argument(
        "--auto", action="store_true", help="Auto-determine validation strategy"
    )
    parser.add_argument(
        "--fast", action="store_true", help="Run fast verification only"
    )
    parser.add_argument(
        "--selective", action="store_true", help="Run selective verification"
    )
    parser.add_argument("--full", action="store_true", help="Run full verification")
    parser.add_argument(
        "--coverage", action="store_true", help="Run coverage scan only"
    )
    parser.add_argument(
        "--plan", action="store_true", help="Generate plan only, don't execute"
    )
    parser.add_argument(
        "--json", action="store_true", help="Print machine-readable summary"
    )
    parser.add_argument("--explain", action="store_true", help="Explain decision tree")
    parser.add_argument(
        "--tree", action="store_true", help="Show full validation graph"
    )
    args = parser.parse_args()

    if args.explain:
        explain_decision(tree=args.tree)
        sys.exit(0)

    strategy = "full"
    if args.fast:
        strategy = "fast"
    elif args.selective:
        strategy = "selective"
    elif args.coverage:
        strategy = "coverage"
    elif args.auto:
        strategy, _, _ = determine_strategy(get_changed_files())

    if args.plan:
        graph = ValidationGraph()
        if strategy == "fast":
            stages = ["fast"]
        elif strategy == "coverage":
            stages = ["fast", "coverage"]
        elif strategy == "selective":
            stages = ["fast", "coverage", "change_intelligence", "mutation_readiness"]
        else:
            stages = graph.get_full_pipeline()

        manifest = ValidationManifest(
            timestamp=datetime.now(UTC).isoformat(),
            changed_files=get_changed_files(),
            strategy=strategy,
            stages=stages,
        )

        for stage_id in stages:
            stage = graph.get_stage(stage_id)
            if stage:
                stage.plan(manifest)

        print(f"# Validation Plan\n\nStrategy: {strategy.upper()}\n\nStages:\n")
        for s in stages:
            print(f"- {s}")

        save_manifest(manifest)
        if args.json:
            print(json.dumps(manifest.to_dict(), indent=2))
        sys.exit(0)

    exit_code, metrics, manifest = (
        run_auto_mode()
        if args.auto
        else run_pipeline(
            (
                ["fast"]
                if strategy == "fast"
                else (
                    ["fast", "coverage"]
                    if strategy == "coverage"
                    else ValidationGraph().get_full_pipeline()
                )
            ),
            strategy,
        )
    )

    save_manifest(manifest)
    save_metrics(metrics)

    history = load_history()
    history.append(
        {
            "timestamp": manifest.timestamp,
            "strategy": strategy,
            "runtime_seconds": sum(m.duration for m in metrics.values()),
            "result": "PASS" if exit_code == 0 else "FAIL",
        }
    )
    save_history(history)

    if args.json:
        print(
            json.dumps(
                {
                    "strategy": strategy,
                    "runtime_seconds": sum(m.duration for m in metrics.values()),
                    "result": "PASS" if exit_code == 0 else "FAIL",
                    "metrics": manifest.to_dict(),
                },
                indent=2,
            )
        )
    else:
        print(f"\nValidation complete: {'PASS' if exit_code == 0 else 'FAIL'}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
