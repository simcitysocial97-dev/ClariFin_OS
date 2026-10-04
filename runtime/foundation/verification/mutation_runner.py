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
import contextlib
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import replace
import uuid
from datetime import UTC, datetime
from pathlib import Path

from runtime.foundation.verification.env import (
    PINNED_MUTMUT,
    REPO_ROOT,
    VENV_BIN,
    resolve_environment,
)
from runtime.foundation.verification.measurement_truth import (
    EvidenceClassification,
    FailureClassification,
    MeasurementCompletionStatus,
    MeasurementKind,
    MeasurementTruthRecord,
    PopulationAccounting,
    assert_authoritative_classification,
    classify_completion,
    set_evidence_fingerprint,
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
from runtime.foundation.verification.mutmut_contract import (
    MutmutContractError,
    MutmutTrampolineContract,
    ensure_mutmut_contract,
    write_mutmut_contract_evidence,
)
from runtime.foundation.verification.survivor_catalog import run_catalog_cli
from runtime.foundation.verification.survivor_intel import (
    DEFAULT_INTEL_PATH,
    build_survivor_intel,
    write_survivor_intel,
)

BACKEND_DIR = REPO_ROOT / "backend"
SMOKE_DIR = BACKEND_DIR / "tests" / "mutation_infra"
FULL_CONFIG = BACKEND_DIR / "pyproject.toml"
SMOKE_CONFIG = SMOKE_DIR / "pyproject.toml"
#: Durable, pre-write backup of ``FULL_CONFIG`` (M10-R3 C2).
#:
#: Kept as a *sibling* of the config rather than under ``runtime/generated/`` because
#: it has to survive exactly the event it exists for: the process being SIGKILLed
#: mid-campaign. A backup written somewhere the campaign also rewrites would not be
#: trustworthy. It is git-ignored via the ``.m10r3-`` prefix and consumed (applied and
#: deleted) by ``_MutationSafety.recover_stale_backup`` on the next run.
CONFIG_BACKUP = BACKEND_DIR / ".pyproject.toml.m10r3-backup"
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
        # True when this run repaired a backup left by a previously killed run.
        self.recovered_stale_backup = False

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
        import re

        if not path.exists():
            return ""
        # Exclude generated bytecode caches and dot/hidden directories: they
        # are artifacts, not source — regenerated `.pyc` during mutation must
        # not be treated as an unexpected source modification.
        pattern = re.compile(r"(^|/)(__pycache__|\.\w+)(/|$)")
        hashes = []
        for f in sorted(path.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(path).as_posix()
            if pattern.search(rel):
                continue
            if any(part.startswith(".") for part in f.parts):
                continue
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
        """Check for unexpected tracked modifications in the protected scope.

        The scope is the mutation *target* — the source mutation must never
        modify — and is deliberately the same for every mode. It is NOT the
        smoke sandbox: `_capture_hashes` already documents that smoke runs in
        `mutation_infra/`, which is expected to change (mutants, cache), and an
        earlier version of this guard aborted whenever that sandbox showed a
        tracked diff. Those two halves of one safety guard contradicted each
        other, so smoke protected the directory it was about to modify while
        leaving the source it must not touch unchecked. Checking the protected
        scope for every mode is both consistent and strictly wider than what
        smoke previously verified.
        """
        scope = "backend/src"

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
        """Restore ``backend/pyproject.toml`` atomically, from the durable backup.

        M10-R3 (C2). Three defects in one method, all reproduced or provable:

        **1. SIGKILL bypasses every restoration path.** Restoration was reachable
        only from ``atexit`` and from the SIGTERM/SIGINT handlers. SIGKILL cannot be
        caught, so a hard kill mid-campaign left ``backend/pyproject.toml`` rewritten
        to the campaign's target scope. This was observed live during M10-R3
        Checkpoint A: a reconcile shard leg killed mid-mutation left
        ``source_paths = ["src/engines/reconciliation_engine.py"]`` in the file.

        **2. The consequence was misattributed.** ``backend/pyproject.toml`` is one of
        the two files in the repository fingerprint's ``config_hash``, so the *next*
        run's capture mismatched and the orchestrator reported
        ``VALIDATION_BLOCKED`` — "scope or fingerprint mismatch detected". The real
        fault was a killed mutation task that did not restore its toolchain config.
        A green suite was blocked by a phantom integrity failure.

        **3. A partial write could corrupt the file.** ``write_text`` truncates then
        writes, so a kill between the two left a truncated TOML that fails to parse
        for every subsequent command — a total, not a partial, loss.

        The fix is a **durable backup plus an atomic replace**, so restoration no
        longer depends on catching anything:

        * :meth:`_write_backup` stores the original text *beside* the config before
          anything is rewritten, so it survives process death;
        * :meth:`_atomic_write` writes to a sibling temp file and ``os.replace``s it,
          which is atomic on POSIX — a crash leaves either the old content or the new
          content, never a truncated file;
        * :meth:`recover_stale_backup` restores a backup left by a *previous* crashed
          run, so the repair happens on the next invocation rather than depending on
          a signal that never arrives.

        SIGKILL still cannot be caught, but it is no longer *fatal to integrity*.
        """
        if self.config_restored:
            return
        text = self.original_config_text
        if text is None:
            text = self._read_backup()
        if text is not None:
            with contextlib.suppress(Exception):
                self._atomic_write(FULL_CONFIG, text)
            with contextlib.suppress(Exception):
                CONFIG_BACKUP.unlink(missing_ok=True)
        self.config_restored = True

    @staticmethod
    def _read_backup() -> str | None:
        try:
            return CONFIG_BACKUP.read_text(encoding="utf-8")
        except OSError:
            return None

    @classmethod
    def _write_backup(cls, text: str) -> None:
        """Persist the original config before it is rewritten.

        A classmethod, not an instance method: the backup must be writable from a
        context where no safety instance exists yet, and it touches no instance state.
        Written with the same atomic discipline as the restore, because the window that
        matters is precisely the one in which the process can be killed.
        """
        cls._atomic_write(CONFIG_BACKUP, text)

    @staticmethod
    def _atomic_write(path: Path, text: str) -> None:
        """Replace *path* with *text* atomically.

        ``os.replace`` on the same filesystem is atomic, so a reader either sees the
        complete old file or the complete new one. ``Path.write_text`` gives no such
        guarantee: it truncates first, so an interrupted write is corruption.
        """
        tmp = path.with_name(f".{path.name}.m10r3-tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)

    @classmethod
    def recover_stale_backup(
        cls,
        full_config: Path | None = None,
        config_backup: Path | None = None,
    ) -> bool:
        """Restore a backup left behind by a previously killed run.

        Called at the very start of a mutation run. This is what turns an
        unrecoverable SIGKILL into a self-healing condition: the damage is repaired
        on the next invocation instead of persisting until a human notices.

        *full_config* / *config_backup* default to the module-level paths but are
        overridable so the repair can be exercised against arbitrary files — the
        restoration path is the one piece of this subsystem that must be provable
        without mutating the real ``backend/pyproject.toml``.

        Returns ``True`` when a stale backup was found and applied.
        """
        target = full_config if full_config is not None else FULL_CONFIG
        source = config_backup if config_backup is not None else CONFIG_BACKUP
        if not Path(source).is_file():
            return False
        try:
            text = Path(source).read_text(encoding="utf-8")
        except OSError:
            with contextlib.suppress(Exception):
                Path(source).unlink(missing_ok=True)
            return False
        cls._atomic_write(Path(target), text)
        with contextlib.suppress(Exception):
            Path(source).unlink(missing_ok=True)
        return True

    def restore_to(self, text: str | None) -> None:
        """Restore the config to *text* atomically and consume the backup.

        The single restoration entry point. ``backend/pyproject.toml`` has two writers
        — the pre-run installer and this post-run restore — and when they used
        different mechanisms the file could be left non-atomically written or with a
        stale sidecar, which made the next run's ``recover_stale_backup`` fire against
        a backup nobody expected. One method, one discipline.
        """
        if text is None:
            return
        self.original_config_text = text
        self.config_restored = False  # force the write even if already marked restored
        self._restore_config()

    def enter(self) -> None:
        """Enter the safety context."""
        # Repair any damage a previously killed run left behind, *before* the
        # dirty-worktree check. Otherwise the check below reports the stale
        # mutation edit as an unrelated dirty file and refuses to run, and the
        # operator is sent to look at a change they did not make.
        self.recovered_stale_backup = self.recover_stale_backup()

        # Check dirty worktree BEFORE capturing hashes (to avoid false positives)
        if not self.allow_dirty:
            dirty = self._check_dirty_worktree()
            if dirty:
                raise RuntimeError(
                    f"Dirty worktree detected in mutation scope. "
                    f"Unexpected tracked changes: {dirty}. "
                    f"Use --allow-dirty to override."
                )

        # The backup must exist before anything is rewritten, not merely before
        # the exit handlers are installed.
        with contextlib.suppress(OSError):
            self._write_backup(FULL_CONFIG.read_text(encoding="utf-8"))

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
        with contextlib.suppress(Exception):
            atexit.unregister(self._restore_config)


# Default bounded runtimes (seconds). The CI shard job window is 90 min, so the
# per-shard subprocess timeout sits well inside it: a shard that exhausts its
# budget is reported as an explicit infrastructure failure (with the mutmut
# transcript attached) rather than being killed by the job runner with no
# evidence at all. The full campaign is intentionally CI-only and expensive.
DEFAULT_RUNTIME = {
    "smoke": 600,
    "target": 4200,
    "full": 5400,
    "incremental": 4200,
}


#: The budget a mutation revalidation task declares in the execution plan.
#:
#: Duplicated as a named constant rather than derived, because the declaration lives
#: as a literal at the two revalidation construction sites in
#: ``execution_orchestrator`` and re-deriving it here would require instantiating a
#: planner's private API — trading a real, greppable constant for an indirection.
#: ``test_mutation_budget_and_toolchain.py`` asserts both sites still agree with this
#: value, so the duplication cannot rot silently.
DECLARED_MUTATION_TIMEOUT_SECONDS = 1200


def _declared_mutation_timeout(mode: str, target: str | None) -> int:
    """What the *plan* believes this mutation obligation's budget to be.

    Returns 0 for a mode the planner never emits a revalidation task for, so "no
    declared budget" is distinguishable from "a budget of zero".
    """
    if mode == "smoke":
        return 0
    return DECLARED_MUTATION_TIMEOUT_SECONDS


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


def _get_git_status(cwd: Path, scope: str) -> dict[str, str]:
    """Return {path: status} for tracked files in scope. Status like ' M', 'M ', 'MM'."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", scope],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        ).stdout
    except Exception:
        return {}
    status = {}
    for line in out.splitlines():
        if line[:2] in (" M", "M ", "MM", "??", "!!", "A ", " D", "D "):
            path = line[3:].strip()
            status[path] = line[:2]
    return status


def _restore_source_tree(
    cwd: Path, scope: str, pre_status: dict[str, str] | None = None
) -> list[str]:
    """Restore mutated tracked source via git.

    If `pre_status` is provided, only restore files that were clean (not modified)
    before mutation but are modified now — i.e., files mutmut actually mutated.
    This preserves legitimate user edits made before the mutation run.
    If `pre_status` is None (e.g., restore_only mode), restore all modified tracked
    files as before (intended to clean up after an aborted run).
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
        if line[:2] not in (" M", "M ", "MM"):
            continue
        path = line[3:].strip()
        # Only restore if file was clean before mutation (not in pre_status,
        # or was untracked/ignored). Legitimate pre-existing edits are preserved.
        if pre_status is not None:
            prior = pre_status.get(path)
            # If file had any tracked modification before, skip (user edit).
            if prior and prior in (" M", "M ", "MM", "A ", " D", "D "):
                continue
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


def _read_log_tail(path: Path, limit: int = 200_000) -> str:
    """Read at most *limit* trailing characters of a captured execution log.

    mutmut's transcript is the only witness to how each mutant was dispatched
    (killed / survived / no tests / not checked). C71 persists the full
    transcript; this bounded tail is only used for infra-failure detection so a
    large log can never be pulled into memory wholesale.
    """
    try:
        size = path.stat().st_size
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            if size > limit:
                handle.seek(size - limit)
            return handle.read()
    except OSError:
        return ""


def execute_mutation(
    *,
    mode: str,
    target: str | None = None,
    shard: str | None = None,
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

    *shard* selects one bounded unit of the sharded campaign
    (see `mutation_shards.py`); it implies ``mode="target"`` and its component
    becomes the reported target so per-component reporting stays intact.
    """
    if shard:
        from runtime.foundation.verification.mutation_shards import (
            MutmutShardError,
            shard_by_id,
        )

        try:
            resolved = shard_by_id(shard)
        except MutmutShardError as exc:
            raise MutmutShardError(str(exc)) from exc
        if resolved is None:
            raise MutmutShardError(
                f"unknown mutation shard {shard!r}; run "
                "`verify.py mutation-plan` to list the certified shards"
            )
        shard = resolved.shard_id
        target = resolved.component
        mode = "target"

    run_id = f"mut-{uuid.uuid4().hex[:12]}"
    sha = _git_sha()
    tree = _git_tree()
    env = resolve_environment(config_dir=BACKEND_DIR)
    config_hash = _config_hash()
    # Assigned before the subprocess starts; the result records it so a shard's
    # independent execution evidence can always be joined to its verdict.
    sentinel_sink: Path | None = None

    # Initialize safety context
    safety = _MutationSafety(mode=mode, allow_dirty=allow_dirty)
    installed_config_original: str | None = None
    safety_entered = False

    # M10-R3 (B2). Mutation is the sixth and last topology to join the shared
    # certification authority. It is the one that *deliberately* rewrites repository
    # files, so it is the clearest proof that the bracket is the right abstraction:
    # a naive "did the tree change" check would always report drift here, whereas the
    # bracket plus an explicit `toolchain_restored` distinguishes "mutated and
    # restored exactly" (certifiable) from "mutated and abandoned" (not).
    from runtime.foundation.verification.execution_orchestrator import (
        CertificationRun,
        CompletionState,
    )

    certification = CertificationRun(plan_id=f"mutation:{mode}:{run_id}")
    certification.__enter__()

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

        # ── C71: enforce the mutation toolchain contract BEFORE executing ──────
        # mutmut 3.7.0 strips a leading "src." from path-derived mutant module
        # names, but this repository imports production code as "src.<package>".
        # With a pristine install every mutant is therefore dispatched to the
        # ORIGINAL function, the test suite exercises unmutated code, and the
        # campaign reports a structurally impossible 0.0% score with every mutant
        # "survived". The contract makes the declared dependency install and the
        # working toolchain the same thing, locally and in CI. If it cannot be
        # satisfied we fail as an INFRASTRUCTURE failure — never as a 0% quality
        # result, and never by mutating the threshold.
        toolchain: MutmutTrampolineContract | None = None
        try:
            toolchain = ensure_mutmut_contract(env.mutmut.version or "")
            write_mutmut_contract_evidence(toolchain)
        except MutmutContractError as exc:
            return build_infrastructure_failure(
                run_id=run_id,
                repository_sha=sha,
                tree_sha=tree,
                python_version=env.python.version or "unknown",
                pytest_version=env.pytest.version or "unknown",
                mutmut_version=env.mutmut.version or "unknown",
                config_hash=config_hash,
                error=f"mutation toolchain contract violated: {exc}",
                mode=mode,
                target=target,
            )

        # ── C42.7: install canonical, explicit, engine-aware selection config ────
        # The [tool.mutmut] block is rendered ONLY from ENGINE_SELECTION (the single
        # source of truth in mutation_contract.py). This removes the fragile implicit
        # coverage-mapping fallback and guarantees the selected test scope is recorded.
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
                if shard:
                    from runtime.foundation.verification.mutation_contract import (
                        install_mutmut_config_block,
                        render_shard_mutmut_config_block,
                    )
                    from runtime.foundation.verification.mutation_shards import (
                        shard_by_id,
                    )

                    resolved = shard_by_id(shard)
                    if resolved is None:  # pragma: no cover - validated above
                        raise RuntimeError(f"unknown mutation shard: {shard!r}")
                    installed_config_original = install_mutmut_config_block(
                        render_shard_mutmut_config_block(resolved), FULL_CONFIG
                    )
                    selected_test_scope = ",".join(resolved.test_selection)
                    source_scope = ",".join(resolved.files)
                    selection_method = f"{SELECTION_METHOD} + sharded campaign unit {resolved.shard_id}"
                else:
                    installed_config_original = write_backend_mutmut_config(
                        target if mode == "target" else None, FULL_CONFIG
                    )
                    selected_test_scope = (
                        ",".join(ENGINE_SELECTION[target].test_selection)
                        if mode == "target"
                        else ""
                    )
                    source_scope = (
                        ",".join(ENGINE_SELECTION[target].source_paths)
                        if mode == "target"
                        else ""
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
            if mode == "target" and not shard:
                assert (
                    target is not None
                )  # guaranteed by the is_valid_engine gate above
                sel = ENGINE_SELECTION[target]
                selected_test_scope = " ".join(sel.test_selection)
                source_scope = " ".join(sel.source_paths)
            elif mode == "target":
                # Shard scope was resolved from the certified shard plan above;
                # it must not be widened back to the whole component.
                assert shard is not None
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

        # Capture pre-mutation git status so we only restore mutmut's changes,
        # not legitimate user edits made before the run (permanent fix for
        # source-reversion bug).
        restore_scope = (
            "backend/src"
            if mode in ("full", "target")
            else str(SMOKE_DIR.relative_to(REPO_ROOT))
        )
        pre_status = _get_git_status(cwd, restore_scope)

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

        # M10-R3 (C) — reconcile the *declared* budget with the *enforced* one.
        #
        # `ExecutionOrchestrator._timeout_for` derives a task's `timeout_seconds` from
        # its estimated duration (`max(60, 2 * estimated)`, else 900), so a mutation
        # revalidation task declares 1200s. What is enforced here is
        # `DEFAULT_RUNTIME[mode]` — 4200s for a target campaign. The declared budget was
        # 3.5x smaller than the real one and nothing recorded either value, so:
        #
        # * a campaign killed by its own timeout and a campaign killed by the CI job
        #   were indistinguishable;
        # * a workflow sizing `timeout-minutes` from the declared value was sizing it
        #   from a number that does not exist.
        #
        # The divergence is now *recorded* on every result rather than silently
        # tolerated. Collapsing the two into one authority is Checkpoint D's transport
        # work; what matters here is that the two numbers are visible together so the
        # discrepancy cannot hide.
        declared_timeout = _declared_mutation_timeout(mode, target)

        start = time.monotonic()
        rc: int | None = None
        infra_error: str | None = None
        log_tail = ""
        proc = None
        log_handle = None
        log_rel = ""
        try:
            # F19: Run mutmut in its own process group so timeout kills entire tree
            # Mutmut changes cwd to `mutants/` before invoking pytest; set PYTHONPATH
            # so that test-fixture plugins (e.g. tests.fixtures.database) remain
            # importable from that working directory.
            _pytest_pythonpath = (
                f"{REPO_ROOT / 'backend' / 'src'}:{REPO_ROOT / 'backend' / 'tests'}"
            )
            log_path = GENERATED_DIR / "mutation-logs" / f"{run_id}.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_handle = log_path.open("w", encoding="utf-8")
            log_handle.write(
                f"# mutmut invocation\n# cwd={cwd}\n# command={' '.join(cmd)}\n"
                f"# toolchain_contract={toolchain.contract_id if toolchain else ''}"
                f":{toolchain.status if toolchain else ''}\n"
                f"# mutmut_version={env.mutmut.version}\n"
                f"# started_at={datetime.now(UTC).isoformat()}\n\n"
            )
            log_handle.flush()
            # ── C71: independent execution evidence ──────────────────────────────
            # mutmut's verdict is derived from a test process's exit code, which
            # answers "did any test fail?" but not "did the mutated code run?".
            # The sentinel sink lets the mutation trust analysis prove the
            # latter independently. It is passed to the mutmut process so every
            # forked mutant test process inherits it; the sentinel itself is a
            # no-op unless a test opts in by calling `arm()`.
            sentinel_sink = GENERATED_DIR / f"mutation-sentinel-{run_id}.jsonl"
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                start_new_session=True,
                env={
                    **os.environ,
                    "PATH": f"{VENV_BIN}:{os.environ.get('PATH', '')}",
                    "PYTHONPATH": _pytest_pythonpath,
                    "C71_MUTATION_SENTINEL_SINK": str(sentinel_sink),
                },
            )
            log_rel = str(log_path.relative_to(REPO_ROOT))
            pgid: int | None = os.getpgid(proc.pid)

            try:
                proc.wait(timeout=timeout)
                rc = proc.returncode
                # C71: mutmut's own output is the only witness to how mutants
                # were dispatched. Read the tail back for infra-failure
                # detection; the full transcript stays on disk as evidence.
                log_tail = _read_log_tail(log_path, limit=200_000)
            except subprocess.TimeoutExpired:
                # F19: Kill entire process group on timeout
                assert pgid is not None  # assigned before wait() above
                try:
                    os.killpg(pgid, signal.SIGTERM)
                    time.sleep(0.5)
                    os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait(timeout=5)
                rc = None
                infra_error = f"mutation run exceeded max_runtime={timeout}s"
                log_tail = _read_log_tail(log_path, limit=200_000)

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
                    if (
                        "missing argument" in low
                        or "error:" in low
                        or "traceback" in low
                    ):
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
            # Restore only mutmut's mutations, preserving legitimate pre-existing edits
            _restore_source_tree(cwd, restore_scope, pre_status)
            # The [tool.mutmut] block is restored unconditionally here, AFTER
            # evidence has already been collected inside the `try` body (see R2
            # architectural fix below). This guarantees the target configuration
            # is still active while `mutmut results` evidence is gathered, so
            # evidence can never silently resolve the wrong engine.
            if installed_config_original is not None:
                # M10-R3 (C2). Routed through the safety object rather than written
                # directly. This used to be a bare `FULL_CONFIG.write_text(...)`, which
                # is the exact two defects the crash-safety work removed:
                # non-atomic (truncate-then-write, so an interruption corrupts the
                # file) and unaware of the durable backup (so it left the sidecar
                # behind, causing the next run's `recover_stale_backup` to fire
                # spuriously). Both writers of this file now go through one method.
                safety.restore_to(installed_config_original)
            if log_handle is not None:
                with contextlib.suppress(Exception):
                    log_handle.flush()
                    log_handle.close()

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
            execution_path="VERIFICATION_CONTROL_PLANE",
            shard_id=shard or "",
            toolchain_contract=(
                f"{toolchain.contract_id}:{toolchain.status}" if toolchain else ""
            ),
            execution_log_path=log_rel,
            execution_sentinel_path=(
                str(sentinel_sink.relative_to(REPO_ROOT)) if sentinel_sink else ""
            ),
            # M10-R3 C: the budget that was actually enforced, and the one the plan
            # declared. Recorded on both so a future divergence is visible in the
            # evidence instead of being inferred from two modules.
            enforced_timeout_seconds=timeout,
            declared_timeout_seconds=declared_timeout,
        )
        _write_cache_provenance(cwd, config_hash=config_hash)

        # Verify safety context (restoration verification)
        safety.exit(installed_config_original)

        # Frozen dataclass: the verdict is attached by replacement, not assignment.
        result = _finalise_mutation_certification(
            certification,
            safety,
            result,
            timeout=timeout,
        )
        assert result is not None

        return result

    except Exception:
        # Ensure safety context cleanup on any exception
        if safety_entered:
            with contextlib.suppress(Exception):
                safety.exit(installed_config_original)
        # Close the bracket on the failure path too. An unclosed bracket cannot assert
        # stability, and a campaign that blew up is exactly the case where the
        # repository state afterwards is the question an operator is asking. The
        # verdict is discarded here because the exception is what the caller sees;
        # what matters is that the state is captured and the config is repaired.
        with contextlib.suppress(Exception):
            _finalise_mutation_certification(
                certification,
                safety,
                None,
                timeout=locals().get("timeout", 0),
            )
        raise


def _finalise_mutation_certification(
    certification: "CertificationRun",
    safety: _MutationSafety,
    result: "MutationResult | None",
    *,
    timeout: int,
) -> "MutationResult | None":
    """Close the bracket and record mutation's verdict in the shared authority.

    Returns the result carrying the new provenance, because ``MutationResult`` is a
    **frozen** dataclass. It cannot be enriched in place — an earlier version of this
    function assigned to its fields, raised ``FrozenInstanceError``, and the enclosing
    ``contextlib.suppress`` swallowed it, so the verdict was silently never applied.
    That is the exact failure mode this milestone exists to remove, reproduced in the
    code that removes it; hence the explicit return value and no broad suppression
    around the assignments.

    The bracket is deliberately closed *after* ``safety.exit``, so the "after" capture
    reflects the restored tree. If it were captured before restoration, every healthy
    campaign would report drift — which is the precise reason a naive per-obligation
    fingerprint check is wrong for mutation, and the reason the bracket, not a
    per-obligation hash, is the model.
    """
    from runtime.foundation.verification.execution_orchestrator import CompletionState

    certification.__exit__(None, None, None)
    restored = bool(safety.config_restored)
    if not restored:
        # Drift that restoration could not repair is a hard block, and the reason
        # must survive into the document rather than being inferred from a next-run
        # fingerprint mismatch.
        certification.record(
            "mutation-toolchain",
            CompletionState.SCOPE,
            detail=(
                "the mutation toolchain config (backend/pyproject.toml) was not "
                "restored; the next fingerprint capture will mismatch and report "
                "VALIDATION_BLOCKED for the wrong reason"
            ),
        )
    state = (
        CompletionState.PASS
        if (result is not None and result.execution_status == "PASS")
        else CompletionState.INFRASTRUCTURE
    )
    certification.record(
        (result.run_id if result else "mutation"),
        state,
        detail=(result.error if result and result.error else ""),
    )
    outcome = certification.to_dict()
    if result is None:
        return None
    return replace(
        result,
        fingerprint_before=outcome["fingerprint_before"],
        fingerprint_after=outcome["fingerprint_after"],
        fingerprint_stable=bool(outcome["fingerprint_stable"]),
        toolchain_restored=restored,
        recovered_stale_backup=bool(safety.recovered_stale_backup),
        certification_decision=outcome["decision"],
        declared_timeout_seconds=result.declared_timeout_seconds
        or _declared_mutation_timeout(result.mode, result.target),
        enforced_timeout_seconds=timeout,
    )


def _write_summary(
    result: MutationResult, mode: str, target: str | None = None
) -> Path:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    if mode == "smoke":
        out = GENERATED_DIR / "local-smoke" / "mutation-summary.json"
    elif target:
        out = GENERATED_DIR / f"mutation-summary-{target}.json"
    else:
        out = GENERATED_DIR / "mutation-summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = result.to_dict()

    # M9-C72: stamp the shard's fingerprint so an incremental run can later
    # PROVE a cached verdict still describes the same source, tests and
    # toolchain. Without it, reuse is a matter of trust, and a trust-based
    # cache is indistinguishable from a measurement that silently stopped
    # running.
    if target:
        import contextlib

        from runtime.foundation.verification.mutation_shards import (
            record_evidence_fingerprint,
        )

        # A summary that cannot be fingerprinted is still valid evidence for
        # this run; it just cannot be reused later. Never let this change the
        # campaign's outcome.
        with contextlib.suppress(Exception):
            payload = record_evidence_fingerprint(payload)

    out.write_text(json.dumps(payload, indent=2) + "\n")
    return out


def _write_measurement_truth(
    result: MutationResult,
    summary_path: Path,
    mode: str,
    target: str | None = None,
) -> Path:
    """M9-C47: persist the canonical measurement-truth record for a mutation run.

    Derives a single authoritative completion classification from the actual
    run state (including partial/timeout/infra/evidence/scope/derived states),
    fingerprints the durable record, and writes it alongside the summary JSON.
    This is the ONE observable, durable truth path for mutation evidence.
    """
    try:
        env = resolve_environment(config_dir=BACKEND_DIR)
        fp = env.fingerprint if env else {}
    except Exception:  # pragma: no cover - defensive
        fp = {}

    def _fp_value(*keys: str) -> str:
        for k in keys:
            v = fp.get(k)
            if v:
                return str(v)
        return ""

    if mode == "smoke":
        out = GENERATED_DIR / "local-smoke" / "measurement-truth.json"
    elif target:
        out = GENERATED_DIR / f"measurement-truth-{target}.json"
    else:
        out = GENERATED_DIR / "measurement-truth.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    requested_scope = result.source_scope or (
        f"target={target}" if target else "full (all engines)"
    )
    actual_scope = requested_scope

    population = PopulationAccounting(
        requested_generated=result.mutants_generated,
        generated=result.mutants_generated,
        killed=result.killed,
        survived=result.survived,
        timeout=result.timeout,
        no_tests=result.no_tests,
        suspicious=result.suspicious,
        not_checked=result.not_checked,
    )

    failure = FailureClassification.NONE.value
    if result.execution_status != "PASS":
        failure = FailureClassification.INFRASTRUCTURE.value
        if result.error and "exceeded max_runtime" in result.error:
            failure = FailureClassification.TIMEOUT.value

    record = MeasurementTruthRecord(
        run_id=result.run_id,
        measurement_kind=MeasurementKind.MUTATION.value,
        repository_sha=result.repository_sha,
        tree_sha=result.tree_sha,
        working_tree_fingerprint=_fp_value("tree_sha", "git_sha"),
        configuration_fingerprint=result.config_hash or _fp_value("config_hash"),
        toolchain_fingerprint=_fp_value("toolchain", "fingerprint"),
        environment_fingerprint=str(fp) if fp else "",
        command=f"verify.py mutation{(' --target ' + target) if target else ''}",
        requested_scope=requested_scope,
        actual_scope=actual_scope,
        population=population,
        mutation_score=result.mutation_score,
        execution_status=result.execution_status,
        completion_status=MeasurementCompletionStatus.UNKNOWN.value,
        failure_classification=failure,
        duration_seconds=float(result.duration_seconds),
        toolchain_versions={
            "python": result.python_version,
            "pytest": result.pytest_version,
            "mutmut": result.mutmut_version,
        },
        artifact_paths=[str(summary_path)],
        evidence_classification=EvidenceClassification.AUTHORITATIVE.value,
        mode=mode,
        target=target,
        error=result.error,
        note="; ".join(
            part
            for part in (
                result.note,
                (
                    f"toolchain_contract={result.toolchain_contract}"
                    if result.toolchain_contract
                    else ""
                ),
                (
                    f"execution_log={result.execution_log_path}"
                    if result.execution_log_path
                    else ""
                ),
            )
            if part
        ),
        durable_survivor_evidence=(
            [
                str(DEFAULT_INTEL_PATH),
                str(GENERATED_DIR / "mutation-survivors.json"),
            ]
            if result.survived > 0 and mode in ("full", "target")
            else []
        ),
    )

    # Order matters: `classify_completion` rejects a record whose
    # `evidence_fingerprint` is empty while it has processed a non-empty
    # population (EVIDENCE_FAILURE), so durability must be stamped *before*
    # classification. Classifying first stamped EVIDENCE_FAILURE, which then
    # downgraded `evidence_classification` to DERIVED, and the subsequent
    # `assert_authoritative_classification` recomputed DERIVED_ONLY — so a
    # complete, clean, freshly measured campaign was written to disk as derived
    # evidence and certification refused to consume it. The order here is now
    # stamp -> classify -> settle label, which is the same sequence the
    # execution orchestrator's measurement path uses.
    set_evidence_fingerprint(record)
    completion = classify_completion(record=record)
    record.completion_status = completion
    # Authoritative only when the full scope completed cleanly (never for
    # partial/timeout/infra/evidence/scope/derived). Reuse the C42 invalidation
    # contract: only a freshly-measured complete run is authoritative.
    record.evidence_classification = (
        EvidenceClassification.AUTHORITATIVE.value
        if completion == MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value
        else EvidenceClassification.DERIVED.value
    )
    assert_authoritative_classification(record)
    out.write_text(json.dumps(record.to_dict(), indent=2) + "\n")
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
    print(f"  Toolchain        : {result.toolchain_contract or 'n/a'}")
    if result.execution_log_path:
        print(f"  Execution log    : {result.execution_log_path}")
    print("-" * 72)
    print(f"  Gate A (Execution Integrity) : {'PASS' if gate_a else 'FAIL'}")
    print(f"  Gate B (Evidence Integrity)  : {'PASS' if gate_b else 'FAIL'}")
    print(f"  Gate C (Quality Threshold)   : {gate_c_display}")
    print("=" * 72)
    if result.execution_status != "PASS":
        print(f"  INFRASTRUCTURE FAILURE: {result.error}")
        print("  Mutation score was NOT evaluated (no fake 0% emitted).")


def get_affected_engines_from_files(changed_files: list[Path]) -> set[str]:
    """Map changed files to engine names for incremental mutation.

    Uses ENGINE_SELECTION source_paths to determine which engine(s) each
    changed file belongs to. Files outside known engine paths are ignored.
    """
    affected: set[str] = set()
    for file_path in changed_files:
        path_str = str(file_path)
        # Normalize to relative backend path
        rel_path = path_str
        if rel_path.startswith(str(REPO_ROOT)):
            rel_path = rel_path[len(str(REPO_ROOT)) :]
        if rel_path.startswith("/"):
            rel_path = rel_path[1:]

        # Match against each engine's source_paths
        for engine_name, selection in ENGINE_SELECTION.items():
            for source_path in selection.source_paths:
                # Direct file match
                if rel_path == source_path or rel_path.endswith(f"/{source_path}"):
                    affected.add(engine_name)
                    break
                # Directory match (file is inside the engine directory)
                if source_path.endswith("/") and rel_path.startswith(source_path):
                    affected.add(engine_name)
                    break
                # Partial match for nested files
                if source_path not in ("/", "") and f"/{source_path}" in rel_path:
                    affected.add(engine_name)
                    break

    return affected


def _collect_changed_files(base: str = "HEAD~1", head: str = "HEAD") -> list[Path]:
    """Collect changed Python files between two git refs."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base, head],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        return [
            REPO_ROOT / f.strip()
            for f in result.stdout.splitlines()
            if f.strip().endswith(".py")
        ]
    except Exception:
        return []


def run_mutation_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="verify.py mutation")
    parser.add_argument("--smoke", action="store_true", help="bounded infra smoke test")
    parser.add_argument(
        "--target", default=None, help="incremental target (engine/module)"
    )
    parser.add_argument(
        "--shard",
        default=None,
        help="run one bounded unit of the sharded campaign "
        "(see `verify.py mutation-plan`); implies --target <component>",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="run mutation only on changed engines",
    )
    parser.add_argument(
        "--changed-files",
        nargs="*",
        default=[],
        help="list of changed files (for incremental mode)",
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
        "--catalog",
        action="store_true",
        help="emit a structured, categorized per-function survivor breakdown "
        "(mutation-survivors.json + console report)",
    )
    parser.add_argument(
        "--intel-enrich",
        type=int,
        default=0,
        help="at-most N survivors to enrich with mutmut tests-for-mutant "
        "covering-test surfaces when persisting the durable survivor-intel "
        "record (<=0 enriches all; conservative default 0 runs all)",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="allow dirty worktree in mutation scope (D5 override)",
    )
    args = parser.parse_args(argv)

    # Determine mode
    if args.shard:
        mode = "target"
    elif args.incremental:
        mode = "incremental"
    elif args.smoke:
        mode = "smoke"
    elif args.target:
        mode = "target"
    else:
        mode = "full"

    # Handle incremental mode: run mutation for each affected engine
    if mode == "incremental":
        # Collect changed files
        if args.changed_files:
            changed_files = [Path(f) for f in args.changed_files]
        else:
            changed_files = _collect_changed_files()

        if not changed_files:
            print("No changed Python files detected, skipping incremental mutation")
            return 0

        affected_engines = get_affected_engines_from_files(changed_files)

        if not affected_engines:
            print("No engines affected by changes, skipping mutation")
            return 0

        print(f"\n{'=' * 72}")
        print("  🎯 INCREMENTAL MUTATION MODE")
        print(f"{'=' * 72}")
        print(f"  Changed files    : {len(changed_files)}")
        print(f"  Affected engines : {', '.join(sorted(affected_engines))}")
        print(f"{'=' * 72}\n")

        # Run mutation for each affected engine
        all_results = []
        for engine in sorted(affected_engines):
            print(f"  Running mutation on: {engine}")
            result = execute_mutation(
                mode="target",
                target=engine,
                max_runtime=args.max_runtime,
                max_children=args.max_children,
                no_cache=args.no_cache,
                restore_only=args.restore,
                allow_dirty=args.allow_dirty,
            )
            all_results.append(result)

        # Aggregate results
        total_killed = sum(r.killed for r in all_results)
        total_survived = sum(r.survived for r in all_results)
        total_no_tests = sum(r.no_tests for r in all_results)
        total_timeout = sum(r.timeout for r in all_results)
        total_suspicious = sum(r.suspicious for r in all_results)
        total_not_checked = sum(r.not_checked for r in all_results)

        aggregated = MutationResult(
            run_id=f"mut-incr-{uuid.uuid4().hex[:12]}",
            repository_sha=all_results[0].repository_sha if all_results else "unknown",
            tree_sha=all_results[0].tree_sha if all_results else "unknown",
            python_version=all_results[0].python_version if all_results else "unknown",
            pytest_version=all_results[0].pytest_version if all_results else "unknown",
            mutmut_version=all_results[0].mutmut_version if all_results else "unknown",
            config_hash=all_results[0].config_hash if all_results else "unknown",
            killed=total_killed,
            survived=total_survived,
            no_tests=total_no_tests,
            timeout=total_timeout,
            suspicious=total_suspicious,
            not_checked=total_not_checked,
            execution_status=(
                "PASS"
                if all(r.execution_status == "PASS" for r in all_results)
                else "FAIL"
            ),
            classification_status=(
                "PASS"
                if all(r.classification_status == "PASS" for r in all_results)
                else "FAIL"
            ),
            evidence_complete=all(r.evidence_complete for r in all_results),
            mode="incremental",
            target=None,
            affected_engines=sorted(affected_engines),
            note=f"Aggregated from {len(all_results)} engine(s)",
            threshold_percent=80,
            source_scope=",".join(
                ENGINE_SELECTION[e].source_paths[0] for e in affected_engines
            ),
            selected_test_scope=" ".join(
                p for e in affected_engines for p in ENGINE_SELECTION[e].test_selection
            ),
            selection_method=SELECTION_METHOD,
            error=None,
        )

        if not args.json:
            _print_report(aggregated)

        out_path = GENERATED_DIR / "mutation-summary-incremental.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(aggregated.to_dict(), indent=2) + "\n")

        if args.json:
            print(str(out_path))

        # Gate logic: incremental runs validate infrastructure, quality gate applies only for full
        gate_a, gate_b, gate_c, verdict = classify_gates(aggregated)
        if not gate_a or not gate_b:
            return 1
        return 0

    # Existing mode handling
    from runtime.foundation.verification.mutation_shards import MutmutShardError

    try:
        result = execute_mutation(
            mode=mode,
            target=args.target,
            shard=args.shard,
            max_runtime=args.max_runtime,
            max_children=args.max_children,
            no_cache=args.no_cache,
            restore_only=args.restore,
            allow_dirty=args.allow_dirty,
        )
    except MutmutShardError as exc:
        print(f"  [shard] {exc}", file=sys.stderr)
        return 1

    # Evidence is keyed by the shard when the sharded campaign produced it, so
    # the aggregate gate can reconcile every shard independently.
    label = result.shard_id or args.target

    if not args.json:
        _print_report(result)

    out_path = _write_summary(result, mode, target=label)
    if args.json:
        print(str(out_path))

    # M9-C47: persist the canonical measurement-truth record for this run so
    # local and CI can reconcile through one observable, durable truth path.
    truth_path = _write_measurement_truth(result, out_path, mode, target=label)
    if not args.json:
        print(
            f"  [truth] measurement-truth persisted: "
            f"{truth_path.relative_to(REPO_ROOT)}"
        )

    # Structured, categorized per-function survivor breakdown (C43.7).
    # Reconstructs surviving mutants from the generated mutant population via
    # mutmut's own libcst reconstruction — no post-hoc file searching required.
    # Runs automatically for full/target campaigns that have survivors; or on
    # demand with --catalog. Skipped for smoke (a surviving mutant is intended
    # there) and for restore-only invocations.
    if (
        not args.restore
        and (args.catalog or mode in ("full", "target"))
        and result.survived > 0
    ):
        try:
            catalog_path = (
                GENERATED_DIR / f"mutation-survivors-{label}.json"
                if label
                else GENERATED_DIR / "mutation-survivors.json"
            )
            run_catalog_cli(BACKEND_DIR / "mutants", BACKEND_DIR, out_path=catalog_path)
        except Exception as exc:  # pragma: no cover - defensive reporting
            print(f"  [catalog] survivor breakdown unavailable: {exc}")

    # M9-C45.2: persist a durable per-mutant survivor-intel record while the
    # .meta cache + mutants/ tree are still alive, so the intelligence (what
    # mutated -> covering tests -> classification -> capability -> fingerprint ->
    # recommendation) survives the workspace lifecycle. Runs unconditionally for
    # full/target campaigns with survivors, or on demand with the catalog flag.
    if (
        not args.restore
        and (args.catalog or mode in ("full", "target"))
        and result.survived > 0
    ):
        try:
            intel = build_survivor_intel(
                BACKEND_DIR / "mutants",
                BACKEND_DIR,
                enrich_tests=True,
                max_enrich=args.intel_enrich,
            )
            intel_path = (
                GENERATED_DIR / f"mutation-survivor-intel-{label}.json"
                if label
                else DEFAULT_INTEL_PATH
            )
            write_survivor_intel(intel, out_path=intel_path)
            print(
                f"  [intel] durable survivor-intel persisted ({intel['total_survivors']} "
                f"survivors; {intel['tests_enriched_count']} tests-enriched): "
                f"{intel_path.relative_to(REPO_ROOT)}"
            )
        except Exception as exc:  # pragma: no cover - defensive reporting
            print(f"  [intel] durable survivor record unavailable: {exc}")

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
