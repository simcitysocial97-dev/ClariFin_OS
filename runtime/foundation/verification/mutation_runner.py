# runtime/foundation/verification/mutation_runner.py
#
# M9-C42.5 — Canonical mutation runner (single source of truth).
#
# Replaces the fragile bash pipeline (run_mutation_selective.sh /
# run_mutation_local_smoke.sh) with one deterministic, testable Python runner.
#
# Invoked identically locally and in CI:
#     python runtime/verify.py mutation            # authoritative full campaign
#     python runtime/verify.py mutation --smoke    # bounded infra health check
#     python runtime/verify.py mutation --target balance_engine   # incremental
#     python runtime/verify.py mutation --restore  # restore mutated source only
#
# Guarantees (per M9-C42.5):
#   * Executes intended tests against generated mutants.
#   * Produces trustworthy killed/survived/no-tests/timeout/not-checked.
#   * Behaves identically locally and in CI (uses runtime/foundation/verification/env.py).
#   * Fails explicitly on infrastructure failure; NEVER emits a fake 0/0/N/A score.
#   * Enforces the arithmetic reconciliation invariant.
#   * Detects stale/incompatible mutation cache and rebuilds safely.
#   * Restores mutated source on any exit (no atexit-only reliance).
#   * Respects the 80% threshold and src/engines scope (never reduced here).

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from runtime.foundation.verification.env import (
    PINNED_MUTMUT,
    REPO_ROOT,
    VENV_BIN,
    resolve_environment,
)
from runtime.foundation.verification.mutation_contract import (
    MutationResult,
    build_infrastructure_failure,
    classify_gates,
    compute_score,
    parse_mutmut_results,
    reconcile_counts,
)

BACKEND_DIR = REPO_ROOT / "backend"
SMOKE_DIR = BACKEND_DIR / "tests" / "mutation_infra"
FULL_CONFIG = BACKEND_DIR / "pyproject.toml"
SMOKE_CONFIG = SMOKE_DIR / "pyproject.toml"
GENERATED_DIR = BACKEND_DIR / "tests" / "generated" / "mutation"

# Default bounded runtimes (seconds). CI job timeout is 90 min; the full
# campaign is intentionally CI-only and expensive.
DEFAULT_RUNTIME = {
    "smoke": 600,
    "target": 1800,
    "full": 5400,
}


def _git_sha() -> str:
    try:
        return (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            )
            .stdout.strip()
            or "unknown"
        )
    except Exception:
        return "unknown"


def _git_tree() -> str:
    try:
        return (
            subprocess.run(
                ["git", "rev-parse", "HEAD^{tree}"],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            )
            .stdout.strip()
            or "unknown"
        )
    except Exception:
        return "unknown"


def _mutmut_bin() -> str:
    env = resolve_environment(config_dir=BACKEND_DIR)
    if env.mutmut.path:
        return env.mutmut.path
    raise RuntimeError("mutmut not resolvable from .venv or PATH")


def _pytest_version() -> str:
    env = resolve_environment()
    return env.pytest.version or "unknown"


def _cache_provenance_path(cwd: Path) -> Path:
    return cwd / ".mutmut-cache" / "provenance.json"


def _validate_cache(cwd: Path, *, no_cache: bool, config_hash: str) -> None:
    """Detect stale/incompatible mutation cache and rebuild safely."""
    cache_dir = cwd / ".mutmut-cache"
    prov = _cache_provenance_path(cwd)
    if no_cache and cache_dir.exists():
        import shutil

        shutil.rmtree(cache_dir)
        return
    if not prov.exists():
        return
    try:
        data = json.loads(prov.read_text())
    except Exception:
        import shutil

        shutil.rmtree(cache_dir, ignore_errors=True)
        return
    mismatches = []
    if data.get("repository_sha") != _git_sha():
        mismatches.append("repository_sha")
    if data.get("config_hash") != config_hash:
        mismatches.append("config_hash")
    if data.get("mutmut_version") != PINNED_MUTMUT:
        mismatches.append("mutmut_version")
    if mismatches:
        import shutil

        shutil.rmtree(cache_dir, ignore_errors=True)


def _write_cache_provenance(cwd: Path, *, config_hash: str) -> None:
    cache_dir = cwd / ".mutmut-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (_cache_provenance_path(cwd)).write_text(
        json.dumps(
            {
                "repository_sha": _git_sha(),
                "tree_sha": _git_tree(),
                "config_hash": config_hash,
                "mutmut_version": PINNED_MUTMUT,
                "python_version": resolve_environment().python.version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
    )


def _restore_source_tree(cwd: Path, scope: str) -> list[str]:
    """Restore any mutated tracked source via git. Returns restored paths."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", scope],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        ).stdout
    except Exception:
        return []
    restored: list[str] = []
    for line in out.splitlines():
        # M / M  <path>  (mutated tracked file)
        if line[:2] in (" M", "M ", "MM"):
            path = line[3:].strip()
            try:
                subprocess.run(
                    ["git", "checkout", "--", path],
                    cwd=str(REPO_ROOT),
                    capture_output=True,
                    timeout=60,
                )
                restored.append(path)
            except Exception:
                pass
    return restored


def _config_hash() -> str:
    from runtime.foundation.verification.env import hash_file

    return hash_file(FULL_CONFIG)


def execute_mutation(
    *,
    mode: str,
    target: Optional[str] = None,
    max_runtime: Optional[int] = None,
    max_children: int = 0,
    no_cache: bool = False,
    restore_only: bool = False,
) -> MutationResult:
    """Core executor. Returns a MutationResult (no file I/O side effects on callers)."""
    run_id = f"mut-{uuid.uuid4().hex[:12]}"
    sha = _git_sha()
    tree = _git_tree()
    env = resolve_environment(config_dir=BACKEND_DIR)
    config_hash = _config_hash()

    if restore_only:
        scope = "backend/src" if mode == "full" else str(SMOKE_DIR.relative_to(REPO_ROOT))
        restored = _restore_source_tree(BACKEND_DIR, scope)
        return MutationResult(
            run_id=run_id,
            repository_sha=sha,
            tree_sha=tree,
            python_version=env.python.version or "unknown",
            pytest_version=env.pytest.version or "unknown",
            mutmut_version=env.mutmut.version or "unknown",
            config_hash=config_hash,
            execution_status="PASS",
            classification_status="PASS",
            evidence_complete=True,
            mode=mode,
            target=target,
            note=f"Restored {len(restored)} mutated file(s): {restored}",
        )

    if not env.consistent:
        return build_infrastructure_failure(
            run_id=run_id,
            repository_sha=sha,
            tree_sha=tree,
            python_version=env.python.version or "unknown",
            pytest_version=env.pytest.version or "unknown",
            mutmut_version=env.mutmut.version or "unknown",
            config_hash=config_hash,
            error="; ".join(env.errors),
            mode=mode,
            target=target,
        )

    if mode == "smoke":
        cwd = SMOKE_DIR
    else:
        cwd = BACKEND_DIR

    _validate_cache(cwd, no_cache=no_cache, config_hash=config_hash)

    mutmut = env.mutmut.path
    assert mutmut is not None

    # Build the mutmut invocation. mutmut 3.7.0: `mutmut run [MUTANT_NAMES]...`.
    cmd = [mutmut, "run"]
    if mode == "target" and target:
        cmd.append(target)
    if max_children and max_children > 0:
        cmd += ["--max-children", str(max_children)]

    timeout = max_runtime or DEFAULT_RUNTIME.get(mode, 5400)

    start = time.monotonic()
    rc: Optional[int] = None
    infra_error: Optional[str] = None
    log_tail = ""
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**__import__("os").environ, "PATH": f"{VENV_BIN}:{__import__('os').environ.get('PATH','')}"},
        )
        rc = proc.returncode
        log_tail = (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired as exc:
        rc = None
        infra_error = f"mutation run exceeded max_runtime={timeout}s"
        log_tail = exc.stdout or "" + exc.stderr or ""
    except Exception as exc:  # pragma: no cover - defensive
        rc = None
        infra_error = f"mutation subprocess error: {exc}"
    finally:
        _restore_source_tree(cwd, "." if mode == "full" else str(SMOKE_DIR.relative_to(REPO_ROOT)))

    # Decide execution integrity.
    # mutmut run RC: 0=all killed, 2=survivors, 4=timeout, 8=suspicious.
    # RC 1 or crash or any 'Error:'/'Missing argument' in output => infra failure.
    infra_failure = infra_error is not None or rc is None or rc == 1
    if not infra_failure and rc is not None:
        try:
            low = (log_tail or "").lower()
            if "missing argument" in low or "error:" in low or "traceback" in low:
                infra_failure = True
                infra_error = "mutmut reported an error during execution"
        except Exception:
            pass

    if infra_failure:
        return build_infrastructure_failure(
            run_id=run_id,
            repository_sha=sha,
            tree_sha=tree,
            python_version=env.python.version or "unknown",
            pytest_version=env.pytest.version or "unknown",
            mutmut_version=env.mutmut.version or "unknown",
            config_hash=config_hash,
            error=infra_error or f"mutmut run exited with rc={rc}",
            mutmut_rc=rc,
            mode=mode,
            target=target,
        )

    # Collect evidence.
    try:
        res = subprocess.run(
            [mutmut, "results", "--all", "true"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=120,
        )
        results_text = res.stdout + res.stderr
    except Exception as exc:
        return build_infrastructure_failure(
            run_id=run_id,
            repository_sha=sha,
            tree_sha=tree,
            python_version=env.python.version or "unknown",
            pytest_version=env.pytest.version or "unknown",
            mutmut_version=env.mutmut.version or "unknown",
            config_hash=config_hash,
            error=f"mutmut results failed: {exc}",
            mutmut_rc=rc,
            mode=mode,
            target=target,
        )

    counts = parse_mutmut_results(results_text)
    invariant_ok = reconcile_counts(counts)

    duration = int(time.monotonic() - start)
    score = compute_score(counts) if invariant_ok else None

    result = MutationResult(
        run_id=run_id,
        repository_sha=sha,
        tree_sha=tree,
        python_version=env.python.version or "unknown",
        pytest_version=env.pytest.version or "unknown",
        mutmut_version=env.mutmut.version or "unknown",
        config_hash=config_hash,
        killed=counts.killed,
        survived=counts.survived,
        no_tests=counts.no_tests,
        timeout=counts.timeout,
        suspicious=counts.suspicious,
        not_checked=counts.not_checked,
        threshold_percent=80,
        execution_status="PASS",
        classification_status="PASS" if invariant_ok else "FAIL",
        evidence_complete=invariant_ok and counts.generated > 0,
        mutation_score=score,
        mode=mode,
        target=target,
        duration_seconds=duration,
        mutmut_rc=rc,
    )
    _write_cache_provenance(cwd, config_hash=config_hash)
    return result


def _write_summary(result: MutationResult, mode: str) -> Path:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    if mode == "smoke":
        out = GENERATED_DIR / "local-smoke" / "mutation-summary.json"
    else:
        out = GENERATED_DIR / "mutation-summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result.to_dict(), indent=2) + "\n")
    return out


def _print_report(result: MutationResult) -> None:
    gate_a, gate_b, gate_c, verdict = classify_gates(result)
    gate_c_display = verdict if result.mode == "full" else "N/A (infra validation only)"
    print("=" * 72)
    print("  M9-C42.5 MUTATION RUNNER")
    print("=" * 72)
    print(f"  Mode             : {result.mode}" + (f" (target={result.target})" if result.target else ""))
    print(f"  Repo SHA         : {result.repository_sha}")
    print(f"  mutmut           : {result.mutmut_version} (pinned {PINNED_MUTMUT})")
    print(f"  Killed           : {result.killed}")
    print(f"  Survived         : {result.survived}")
    print(f"  No tests         : {result.no_tests}")
    print(f"  Timeout          : {result.timeout}")
    print(f"  Suspicious       : {result.suspicious}")
    print(f"  Not checked      : {result.not_checked}")
    print(f"  Generated        : {result.mutants_generated}")
    print(f"  Mutation score   : {result.mutation_score}")
    print(f"  Threshold        : {result.threshold_percent}%")
    print("-" * 72)
    print(f"  Gate A (Execution Integrity) : {'PASS' if gate_a else 'FAIL'}")
    print(f"  Gate B (Evidence Integrity)  : {'PASS' if gate_b else 'FAIL'}")
    print(f"  Gate C (Quality Threshold)   : {gate_c_display}")
    print("=" * 72)
    if result.execution_status != "PASS":
        print(f"  INFRASTRUCTURE FAILURE: {result.error}")
        print("  Mutation score was NOT evaluated (no fake 0% emitted).")


def run_mutation_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="verify.py mutation")
    parser.add_argument("--smoke", action="store_true", help="bounded infra smoke test")
    parser.add_argument("--target", default=None, help="incremental target (engine/module)")
    parser.add_argument("--max-runtime", type=int, default=None, help="hard subprocess timeout (s)")
    parser.add_argument("--max-children", type=int, default=0, help="mutmut parallelism")
    parser.add_argument("--no-cache", action="store_true", help="discard mutation cache")
    parser.add_argument("--restore", action="store_true", help="restore mutated source and exit")
    parser.add_argument("--json", action="store_true", help="emit summary path only")
    args = parser.parse_args(argv)

    mode = "smoke" if args.smoke else ("target" if args.target else "full")

    result = execute_mutation(
        mode=mode,
        target=args.target,
        max_runtime=args.max_runtime,
        max_children=args.max_children,
        no_cache=args.no_cache,
        restore_only=args.restore,
    )

    if not args.json:
        _print_report(result)

    out_path = _write_summary(result, mode)
    if args.json:
        print(str(out_path))

    gate_a, gate_b, gate_c, verdict = classify_gates(result)
    if not gate_a or not gate_b:
        # Infrastructure / evidence failure — NOT EVALUABLE. Exit 1, never a score.
        return 1
    if mode == "full":
        # Authoritative gate: only the full campaign enforces the 80% threshold.
        return 0 if gate_c is True else 2
    # smoke / target: infrastructure-validation only. Quality is NOT gated here
    # (smoke deliberately includes a surviving mutant; target is a dev subset).
    # A healthy pipeline (A & B pass) is success.
    return 0
