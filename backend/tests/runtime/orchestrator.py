"""Simplified Verification Orchestrator.

Uses the unified registry and discovery systems to orchestrate verification.
Wraps the existing Validation Orchestrator Framework (VOF) with registry-driven targets.

Usage:
    python -m runtime.orchestrator --auto
    python -m runtime.orchestrator --full
    python -m runtime.orchestrator --plan
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"


@dataclass
class RuntimeManifest:
    """Verification Runtime manifest for a single run."""

    timestamp: str
    strategy: str = "full"
    changed_files: list[str] = field(default_factory=list)
    affected_capabilities: list[str] = field(default_factory=list)
    stages: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    result: str = "PENDING"

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "strategy": self.strategy,
            "changed_files": self.changed_files,
            "affected_capabilities": self.affected_capabilities,
            "stages": self.stages,
            "commands": self.commands,
            "duration_seconds": self.duration_seconds,
            "result": self.result,
        }


# =============================================================================
# Stage Runners (registry-driven)
# =============================================================================


def _run_command(
    cmd: list[str], cwd: Path, capture: bool = True
) -> tuple[int, float, str]:
    """Run a command and return (exit_code, duration, output)."""
    start = time.time()
    result = subprocess.run(cmd, cwd=cwd, capture_output=capture, text=True)
    duration = time.time() - start
    output = result.stdout if capture else ""
    return result.returncode, duration, output


def stage_fast(manifest: RuntimeManifest) -> tuple[int, float]:
    """Fast verification: ruff + black checks."""
    manifest.commands.append("ruff check --fix src/")
    manifest.commands.append("ruff format --check src/")
    exit_code, duration, _ = _run_command(
        ["ruff", "check", "src/", "--fix"], BACKEND_DIR
    )
    if exit_code != 0:
        return exit_code, duration
    exit_code, duration, _ = _run_command(
        ["ruff", "format", "--check", "src/"], BACKEND_DIR
    )
    return exit_code, duration


def stage_unit(manifest: RuntimeManifest) -> tuple[int, float]:
    """Unit tests."""
    manifest.commands.append("pytest tests/unit/ -q --tb=short --timeout=60")
    return _run_command(
        ["pytest", "tests/unit/", "-q", "--tb=short", "--timeout=60"], BACKEND_DIR
    )


def stage_property(manifest: RuntimeManifest) -> tuple[int, float]:
    """Property tests."""
    manifest.commands.append("pytest tests/properties/ -q --tb=short --timeout=60")
    return _run_command(
        ["pytest", "tests/properties/", "-q", "--tb=short", "--timeout=60"], BACKEND_DIR
    )


def stage_contract(manifest: RuntimeManifest) -> tuple[int, float]:
    """Contract tests."""
    manifest.commands.append("pytest tests/contract/ -q --tb=short --timeout=60")
    return _run_command(
        ["pytest", "tests/contract/", "-q", "--tb=short", "--timeout=60"], BACKEND_DIR
    )


def stage_capability(manifest: RuntimeManifest) -> tuple[int, float]:
    """Capability smoke tests."""
    manifest.commands.append("pytest tests/capability/ -q --tb=short --timeout=60")
    return _run_command(
        ["pytest", "tests/capability/", "-q", "--tb=short", "--timeout=60"], BACKEND_DIR
    )


def stage_invariant(manifest: RuntimeManifest) -> tuple[int, float]:
    """Invariant tests."""
    manifest.commands.append("pytest tests/invariants/ -q --tb=short --timeout=60")
    return _run_command(
        ["pytest", "tests/invariants/", "-q", "--tb=short", "--timeout=60"], BACKEND_DIR
    )


def stage_golden(manifest: RuntimeManifest) -> tuple[int, float]:
    """Golden dataset tests."""
    manifest.commands.append("pytest tests/golden/ -q --tb=short --timeout=60")
    return _run_command(
        ["pytest", "tests/golden/", "-q", "--tb=short", "--timeout=60"], BACKEND_DIR
    )


def stage_architecture(manifest: RuntimeManifest) -> tuple[int, float]:
    """Architecture boundary tests."""
    manifest.commands.append("pytest tests/architecture/ -q --tb=short --timeout=60")
    return _run_command(
        ["pytest", "tests/architecture/", "-q", "--tb=short", "--timeout=60"],
        BACKEND_DIR,
    )


def stage_meta(manifest: RuntimeManifest) -> tuple[int, float]:
    """Meta / registry tests."""
    manifest.commands.append("pytest tests/meta/ -q --tb=short --timeout=60")
    return _run_command(
        ["pytest", "tests/meta/", "-q", "--tb=short", "--timeout=60"], BACKEND_DIR
    )


# =============================================================================
# Pipeline Construction
# =============================================================================

STAGE_RUNNERS: dict[str, Any] = {
    "fast": stage_fast,
    "unit": stage_unit,
    "property": stage_property,
    "contract": stage_contract,
    "capability": stage_capability,
    "invariant": stage_invariant,
    "golden": stage_golden,
    "architecture": stage_architecture,
    "meta": stage_meta,
}

FULL_PIPELINE = [
    "fast",
    "unit",
    "property",
    "contract",
    "capability",
    "invariant",
    "golden",
    "architecture",
    "meta",
]

FAST_PIPELINE = ["fast"]

SELECTIVE_PIPELINE_BASE = ["fast", "unit"]


def build_pipeline(strategy: str, capabilities: list[str] | None = None) -> list[str]:
    """Build a verification pipeline based on strategy.

    Args:
        strategy: One of 'fast', 'full', 'selective', 'intelligent'
        capabilities: List of affected capabilities (for selective mode)

    Returns:
        List of stage IDs to execute
    """
    if strategy == "fast":
        return FAST_PIPELINE
    if strategy == "full":
        return FULL_PIPELINE
    if strategy == "selective":
        pipeline = list(SELECTIVE_PIPELINE_BASE)
        if capabilities:
            pipeline.append("property")
            pipeline.append("invariant")
            pipeline.append("golden")
            pipeline.append("capability")
        return pipeline
    if strategy == "intelligent":
        pipeline = list(SELECTIVE_PIPELINE_BASE)
        if capabilities:
            pipeline.append("property")
            pipeline.append("invariant")
            pipeline.append("golden")
            pipeline.append("capability")
            pipeline.append("architecture")
            pipeline.append("meta")
        return pipeline
    return FULL_PIPELINE


def intelligent_strategy(
    changed_files: list[str] | None = None,
) -> tuple[str, list[str]]:
    """Determine verification strategy using the intelligence layer.

    Returns (strategy, affected_capabilities).
    """
    try:
        from verification.intelligence.impact_engine import ImpactEngine

        engine = ImpactEngine()
        files = changed_files if changed_files else _get_git_changed_files()
        impact = engine.analyze(files)
        return impact.strategy, [c.id for c in impact.affected_capabilities]
    except Exception:
        return "full", []


def _get_git_changed_files() -> list[str]:
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
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except FileNotFoundError:
        return []


# =============================================================================
# Main Orchestrator
# =============================================================================


def run_verification(
    strategy: str = "full", capabilities: list[str] | None = None
) -> RuntimeManifest:
    """Run the verification pipeline.

    Args:
        strategy: Verification strategy ('fast', 'full', 'selective')
        capabilities: Affected capabilities for selective mode

    Returns:
        RuntimeManifest with results
    """
    manifest = RuntimeManifest(
        timestamp=datetime.now(UTC).isoformat(), strategy=strategy
    )
    pipeline = build_pipeline(strategy, capabilities)
    manifest.stages = pipeline

    start_time = time.time()
    exit_code = 0

    for stage_id in pipeline:
        runner = STAGE_RUNNERS.get(stage_id)
        if not runner:
            continue
        stage_exit, stage_duration = runner(manifest)
        if stage_exit != 0:
            exit_code = stage_exit
            break

    manifest.duration_seconds = time.time() - start_time
    manifest.result = "PASS" if exit_code == 0 else "FAIL"

    return manifest


def save_manifest(manifest: RuntimeManifest) -> None:
    """Save manifest to generated artifacts."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    path = GENERATED_DIR / "verification-runtime-manifest.json"
    with open(path, "w") as f:
        json.dump(manifest.to_dict(), f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verification Runtime")
    parser.add_argument("--auto", action="store_true", help="Auto-determine strategy")
    parser.add_argument("--fast", action="store_true", help="Fast verification only")
    parser.add_argument("--full", action="store_true", help="Full verification")
    parser.add_argument(
        "--selective", action="store_true", help="Selective verification"
    )
    parser.add_argument(
        "--intelligent",
        action="store_true",
        help="Intelligence-driven verification",
    )
    parser.add_argument("--plan", action="store_true", help="Generate plan only")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--capabilities", nargs="*", help="Affected capabilities for selective mode"
    )

    args = parser.parse_args()

    if args.fast:
        strategy = "fast"
    elif args.full:
        strategy = "full"
    elif args.selective:
        strategy = "selective"
    elif args.intelligent:
        strategy = "intelligent"
    elif args.auto:
        strategy = "full"
    else:
        strategy = "full"

    if args.plan:
        pipeline = build_pipeline(strategy, args.capabilities)
        manifest = RuntimeManifest(
            timestamp=datetime.now(UTC).isoformat(),
            strategy=strategy,
            affected_capabilities=args.capabilities or [],
            stages=pipeline,
        )
        print(
            f"# Verification Runtime Plan\n\nStrategy: {strategy.upper()}\n\nStages:\n"
        )
        for s in pipeline:
            print(f"- {s}")
        if args.json:
            print(json.dumps(manifest.to_dict(), indent=2))
        sys.exit(0)

    if strategy == "intelligent":
        strategy, affected = intelligent_strategy()
        manifest = run_verification(strategy, affected)
    else:
        manifest = run_verification(strategy, args.capabilities)

    save_manifest(manifest)

    if args.json:
        print(json.dumps(manifest.to_dict(), indent=2))
    else:
        print(f"\nVerification Runtime: {manifest.result}")
        print(f"Strategy: {manifest.strategy}")
        print(f"Duration: {manifest.duration_seconds:.1f}s")
        print(f"Stages: {', '.join(manifest.stages)}")

    sys.exit(0 if manifest.result == "PASS" else 1)


if __name__ == "__main__":
    main()
