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
import atexit
import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from runtime.foundation.verification.env import (
    PINNED_MUTMUT,
    REPO_ROOT,
    VENV_BIN,
    resolve_environment,
)
from runtime.foundation.verification.mutation_contract import (
    ENGINE_SELECTION,
    SELECTION_METHOD,
    MutationResult,
    build_infrastructure_failure,
    classify_gates,
    compute_score,
    is_valid_engine,
    parse_mutmut_results,
    reconcile_counts,
    write_backend_mutmut_config,
)

BACKEND_DIR = REPO_ROOT / "backend"
SMOKE_DIR = BACKEND_DIR / "tests" / "mutation_infra"
FULL_CONFIG = BACKEND_DIR / "pyproject.toml"
SMOKE_CONFIG = SMOKE_DIR / "pyproject.toml"
GENERATED_DIR = BACKEND_DIR / "tests" / "generated" / "mutation"


# ── Mutation execution safety context (R3a, R4) ──────────────────────────────
class _MutationSafety:
    """Context manager for mutation execution safety.

    Guarantees:
    - Signal handlers (SIGTERM, SIGINT) restore config on abnormal exit
    - atexit handler restores config on normal exit
    - Pre-run capture of backend/pyproject.toml + mutation scope hashes
    - Post-run verification of exact restoration
    - Dirty-worktree refusal with override flag
    """

    def __init__(self, mode: str, allow_dirty: bool = False):
        self.mode = mode
        self.allow_dirty = allow_dirty
        self.config_restored = False
        self.original_config_text: str | None = None
        self.captured_hashes: dict[str, str] = {}
        self._signal_handlers_installed = False

    def _hash_file(self, path: Path) -> str:
        if path.exists():
            return hashlib.sha256(path.read_bytes()).hexdigest()
        return ""

    def _capture_hashes(self) -> None:
        """Capture hashes of files that mutation should NOT modify."""
        # Always capture backend/pyproject.toml (config file we rewrite)
        self.captured_hashes = {
            "backend/pyproject.toml": self._hash_file(FULL_CONFIG),
        }
        # For full/target mode, also capture backend/src (source files mutation should not modify directly)
        if self.mode in ("full", "target"):
            self.captured_hashes["backend/src"] = self._hash_dir(BACKEND_DIR / "src")
        # For smoke mode, mutation runs in mutation_infra/ which is expected to change
        # (mutants, cache), so we don't hash it

    def _hash_dir(self, path: Path) -> str:
        if not path.exists():
            return ""
        hashes = []
        for f in sorted(path.rglob("*")):
            if f.is_file() and not any(part.startswith(".") for part in f.parts):
                hashes.append(self._hash_file(f))
        return hashlib.sha256("".join(hashes).encode()).hexdigest()

    def _verify_restoration(self) -> list[str]:
        """Verify exact restoration of protected files. Returns list of unexpected changes."""
        unexpected = []
        for rel_path, expected_hash in self.captured_hashes.items():
            abs_path = REPO_ROOT / rel_path
            actual_hash = (
                self._hash_file(abs_path)
                if abs_path.is_file()
                else self._hash_dir(abs_path)
            )
            if actual_hash != expected_hash:
                unexpected.append(
                    f"{rel_path}: hash changed (expected {expected_hash[:8]}, got {actual_hash[:8]})"
                )
        return unexpected

    def _check_dirty_worktree(self) -> list[str]:
        """Check for unexpected tracked modifications in restore scope."""
        # Determine restore scope
        if self.mode == "full" or self.mode == "target":
            scope = "backend/src"
        else:
            scope = str(SMOKE_DIR.relative_to(REPO_ROOT))

        try:
            out = subprocess.run(
                ["git", "status", "--porcelain", scope],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            ).stdout
        except Exception:
            return []

        dirty = []
        for line in out.splitlines():
            if line[:2] in (" M", "M ", "MM", "??", "A ", "D "):
                dirty.append(line[3:].strip())
        return dirty

    def install_signal_handlers(self) -> None:
        """Install SIGTERM/SIGINT handlers for config restoration."""
        if self._signal_handlers_installed:
            return

        def _signal_handler(signum, frame):
            self._restore_config()
            # Re-raise with default handler
            signal.signal(signum, signal.SIG_DFL)
            os.kill(os.getpid(), signum)

        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)
        self._signal_handlers_installed = True

    def _restore_config(self) -> None:
        """Restore backend/pyproject.toml if we modified it."""
        if self.config_restored or self.original_config_text is None:
            return
        try:
            FULL_CONFIG.write_text(self.original_config_text)
        except Exception:
            pass
        self.config_restored = True

    def enter(self) -> None:
        """Enter the safety context."""
        # Check dirty worktree BEFORE capturing hashes (to avoid false positives)
        if not self.allow_dirty:
            dirty = self._check_dirty_worktree()
            if dirty:
                raise RuntimeError(
                    f"Dirty worktree detected in mutation scope. "
                    f"Unexpected tracked changes: {dirty}. "
                    f"Use --allow-dirty to override."
                )

        self._capture_hashes()
        self.install_signal_handlers()
        atexit.register(self._restore_config)

    def exit(self, installed_config_original: str | None) -> None:
        """Exit the safety context, verify restoration."""
        self.original_config_text = installed_config_original
        self._restore_config()

        # Verify exact restoration of protected files
        unexpected = self._verify_restoration()
        if unexpected:
            raise RuntimeError(
                f"Mutation execution left unexpected file modifications: {unexpected}. "
                f"This indicates a safety violation — config/source not properly restored."
            )

        # Clean up atexit
        try:
            atexit.unregister(self._restore_config)
        except Exception:
            pass


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
            ).stdout.strip()
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
            ).stdout.strip()
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
                "timestamp": datetime.now(UTC).isoformat(),
            },
            indent=2,
        )
    )


def _restore_source_tree(cwd: Path, scope: str) -> list[str]:
    """Restore any mutated tracked source via git. Returns restored paths.

    For full mode, scope is "backend/src" (the actual mutated source).
    For target mode, scope is "backend/src".
    For smoke mode, scope is the mutation_infra directory.
    """
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


def _record_lifecycle_event(event_type: str, details: dict) -> None:
    """Record a lifecycle event for evidence tracking."""
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": event_type,
        "details": details,
    }
    log_file = GENERATED_DIR / "mutation-lifecycle-events.jsonl"
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        pass  # Non-critical


def _config_hash() -> str:
    from runtime.foundation.verification.env import hash_file

    return hash_file(FULL_CONFIG)


def execute_mutation(
    *,
    mode: str,
    target: str | None = None,
    max_runtime: int | None = None,
    max_children: int = 0,
    no_cache: bool = False,
    restore_only: bool = False,
    allow_dirty: bool = False,
) -> MutationResult:
    """Core executor. Returns a MutationResult (no file I/O side effects on callers).

    Safety guarantees (R3a, R4):
    - Signal handlers (SIGTERM, SIGINT) + atexit restore config on any exit
    - Pre-run capture of backend/pyproject.toml + mutation scope hashes
    - Post-run verification of exact restoration
    - Dirty-worktree refusal (unless allow_dirty=True)
    """
    run_id = f"mut-{uuid.uuid4().hex[:12]}"
    sha = _git_sha()
    tree = _git_tree()
    env = resolve_environment(config_dir=BACKEND_DIR)
    config_hash = _config_hash()

    # Initialize safety context
    safety = _MutationSafety(mode=mode, allow_dirty=allow_dirty)
    installed_config_original: str | None = None
    safety_entered = False

    try:
        safety.enter()
        safety_entered = True

        if restore_only:
            scope = (
                "backend/src"
                if mode == "full"
                else str(SMOKE_DIR.relative_to(REPO_ROOT))
            )
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

        # ── C42.7: install canonical, explicit, engine-aware selection config ────
        # The [tool.mutmut] block is rendered ONLY from ENGINE_SELECTION (the single
        # source of truth in mutation_contract.py). This removes the fragile implicit
        # coverage-mapping fallback and guarantees the selected test scope is recorded.
        installed_config_original: str | None = None
        selected_test_scope = ""
        source_scope = ""
        selection_method = SELECTION_METHOD
        if mode in ("target", "full"):
            if mode == "target" and not is_valid_engine(target):
                return build_infrastructure_failure(
                    run_id=run_id,
                    repository_sha=sha,
                    tree_sha=tree,
                    python_version=env.python.version or "unknown",
                    pytest_version=env.pytest.version or "unknown",
                    mutmut_version=env.mutmut.version or "unknown",
                    config_hash=config_hash,
                    error=f"unknown mutation target engine: {target!r}",
                    mode=mode,
                    target=target,
                )
            try:
                installed_config_original = write_backend_mutmut_config(
                    target if mode == "target" else None, FULL_CONFIG
                )
            except Exception as exc:  # pragma: no cover - defensive
                return build_infrastructure_failure(
                    run_id=run_id,
                    repository_sha=sha,
                    tree_sha=tree,
                    python_version=env.python.version or "unknown",
                    pytest_version=env.pytest.version or "unknown",
                    mutmut_version=env.mutmut.version or "unknown",
                    config_hash=config_hash,
                    error=f"failed to render canonical mutmut config: {exc}",
                    mode=mode,
                    target=target,
                )
            # Recompute config hash to reflect the installed canonical config.
            config_hash = _config_hash()
            # Remove any stale mutants from a previous (different-scope) run so the
            # generated population matches the canonical source scope exactly.
            mutants_dir = BACKEND_DIR / "mutants"
            if mutants_dir.exists():
                shutil.rmtree(mutants_dir)
            # Also drop mutmut's own cache so a different-scope provenance can never
            # be reused (mutmut 3.7.0 keeps a .mutmut-cache that encodes source scope).
            cache_dir = BACKEND_DIR / ".mutmut-cache"
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
            if mode == "target":
                sel = ENGINE_SELECTION[target]
                selected_test_scope = " ".join(sel.test_selection)
                source_scope = " ".join(sel.source_paths)
            else:
                selected_test_scope = " ".join(
                    p for s in ENGINE_SELECTION.values() for p in s.test_selection
                )
                source_scope = "src/engines/"
        elif mode == "smoke":
            selected_test_scope = "test_probe.py"
            source_scope = "probe.py"
            selection_method = "explicit-pytest-path (smoke fixture)"

        if mode == "smoke":
            cwd = SMOKE_DIR
        else:
            cwd = BACKEND_DIR

        _validate_cache(cwd, no_cache=no_cache, config_hash=config_hash)

        mutmut = env.mutmut.path
        assert mutmut is not None

        # Build the mutmut invocation. mutmut 3.7.0: `mutmut run [MUTANT_NAMES]...`.
        # NOTE: Do NOT pass `target` as a positional argument — mutmut 3.7.0 treats
        # positional args as a mutant-name filter (fnmatch against cached names).
        # Passing e.g. "credit_card_engine" fails when no cache entry matches that
        # exact string, producing RC=1 and an infra-failure. Engine scoping is handled
        # entirely by the canonical `source_paths` block installed into pyproject.toml.
        cmd = [mutmut, "run"]
        if max_children and max_children > 0:
            cmd += ["--max-children", str(max_children)]

        timeout = max_runtime or DEFAULT_RUNTIME.get(mode, 5400)

        start = time.monotonic()
        rc: int | None = None
        infra_error: str | None = None
        log_tail = ""
        proc = None
        try:
            # F19: Run mutmut in its own process group so timeout kills entire tree
            # Mutmut changes cwd to `mutants/` before invoking pytest; set PYTHONPATH
            # so that test-fixture plugins (e.g. tests.fixtures.database) remain
            # importable from that working directory.
            _pytest_pythonpath = f"{REPO_ROOT / 'backend' / 'src'}:{REPO_ROOT / 'backend' / 'tests'}"
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                start_new_session=True,
                env={
                    **os.environ,
                    "PATH": f"{VENV_BIN}:{os.environ.get('PATH','')}",
                    "PYTHONPATH": _pytest_pythonpath,
                },
            )
            pgid = os.getpgid(proc.pid)

            try:
                stdout, stderr = proc.communicate(timeout=timeout)
                rc = proc.returncode
                log_tail = (stdout or "") + (stderr or "")
            except subprocess.TimeoutExpired:
                # F19: Kill entire process group on timeout
                try:
                    os.killpg(pgid, signal.SIGTERM)
                    time.sleep(0.5)
                    os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait(timeout=5)
                rc = None
                infra_error = f"mutation run exceeded max_runtime={timeout}s"
                log_tail = ""

            # ── R2 architectural fix ───────────────────────────────────────────
            # Evidence collection occurs HERE, inside the `try` body and BEFORE
            # the `finally:` block below. The `finally` restores the original
            # [tool.mutmut] config, so the target configuration is still active
            # while `mutmut results` evidence is gathered. This guarantees
            # evidence is collected with the correct engine selected
            # (requirement #3: evidence collection cannot silently resolve the
            # wrong engine) and Gate B stays fail-safe. The ordering is enforced
            # by Python's try/finally semantics, not a runtime flag.
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

        except Exception as exc:  # pragma: no cover - defensive
            rc = None
            infra_error = f"mutation subprocess error: {exc}"
            log_tail = ""

        finally:
            # Ensure process group is cleaned up on any exit
            if proc is not None:
                pgid = None
                try:
                    pgid = os.getpgid(proc.pid)
                    try:
                        os.killpg(pgid, signal.SIGTERM)
                        time.sleep(0.2)
                        os.killpg(pgid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                except Exception:
                    pass
                # Evidence: record process group termination
                _record_lifecycle_event(
                    "mutation_process_group_killed",
                    {"pgid": pgid, "signal": "SIGTERM+SIGKILL"},
                )
            # Restore source tree with CORRECT scope (backend/src for full/target)
            restore_scope = (
                "backend/src"
                if mode in ("full", "target")
                else str(SMOKE_DIR.relative_to(REPO_ROOT))
            )
            _restore_source_tree(cwd, restore_scope)
            # The [tool.mutmut] block is restored unconditionally here, AFTER
            # evidence has already been collected inside the `try` body (see R2
            # architectural fix below). This guarantees the target configuration
            # is still active while `mutmut results` evidence is gathered, so
            # evidence can never silently resolve the wrong engine.
            if installed_config_original is not None:
                FULL_CONFIG.write_text(installed_config_original)

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
            selected_test_scope=selected_test_scope,
            source_scope=source_scope,
            selection_method=selection_method,
        )
        _write_cache_provenance(cwd, config_hash=config_hash)

        # Verify safety context (restoration verification)
        safety.exit(installed_config_original)

        return result

    except Exception:
        # Ensure safety context cleanup on any exception
        if safety_entered:
            try:
                safety.exit(installed_config_original)
            except Exception:
                pass
        raise


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
    print(
        f"  Mode             : {result.mode}"
        + (f" (target={result.target})" if result.target else "")
    )
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
    parser.add_argument(
        "--target", default=None, help="incremental target (engine/module)"
    )
    parser.add_argument(
        "--max-runtime", type=int, default=None, help="hard subprocess timeout (s)"
    )
    parser.add_argument(
        "--max-children", type=int, default=0, help="mutmut parallelism"
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="discard mutation cache"
    )
    parser.add_argument(
        "--restore", action="store_true", help="restore mutated source and exit"
    )
    parser.add_argument("--json", action="store_true", help="emit summary path only")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="allow dirty worktree in mutation scope (D5 override)",
    )
    args = parser.parse_args(argv)

    mode = "smoke" if args.smoke else ("target" if args.target else "full")

    result = execute_mutation(
        mode=mode,
        target=args.target,
        max_runtime=args.max_runtime,
        max_children=args.max_children,
        no_cache=args.no_cache,
        restore_only=args.restore,
        allow_dirty=args.allow_dirty,
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
