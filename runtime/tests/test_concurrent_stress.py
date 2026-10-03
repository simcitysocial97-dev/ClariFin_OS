import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

# Canonical interpreter for every subprocess in this module.
#
# These tests used to spawn bare `"python"`, which resolves through PATH and
# on this host is `/usr/bin/python` — the SYSTEM interpreter, not the
# repository-root `.venv` that AGENTS.md makes the single sanctioned
# environment. `runtime/foundation/verification/env.py` resolves `.venv/bin`
# before PATH, but a raw `subprocess.run(["python", ...])` bypasses that
# resolver entirely, so the tests were exercising the CLI outside its
# contracted environment.
#
# Measured cost of that, same command, same repo state:
#     /usr/bin/python  -m runtime.verify plan --scope backend -> 23.41 s
#     .venv/bin/python -m runtime.verify plan --scope backend ->  7.73 s
# A 3.0x difference, paid by all 15 invocations below. It is also the direct
# cause of the observed flake: `test_concurrent_plan_commands` runs five of
# these concurrently under a `timeout=60` per command, and under host
# contention the slower interpreter pushed it to exactly 60.07 s and it
# failed. `sys.executable` is the pytest interpreter, i.e. the venv.
PYTHON = sys.executable


def test_concurrent_plan_commands():
    """Multiple verify plan commands must not corrupt shared state."""

    commands = [
        [PYTHON, "-m", "runtime.verify", "plan", "--scope", "backend"],
        [PYTHON, "-m", "runtime.verify", "plan", "--scope", "frontend"],
        [PYTHON, "-m", "runtime.verify", "plan", "--scope", "runtime"],
        [PYTHON, "-m", "runtime.verify", "plan", "--scope", "backend"],
        [PYTHON, "-m", "runtime.verify", "plan", "--scope", "frontend"],
    ]

    def run_command(cmd):
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_command, cmd) for cmd in commands]
        results = [f.result() for f in as_completed(futures)]

    failures = [r for r in results if r.returncode != 0]
    assert len(failures) == 0, f"{len(failures)} commands failed in parallel execution"

    cache_file = Path("runtime/generated/verification-cache.json")
    if cache_file.exists():
        import json

        try:
            cache_data = json.loads(cache_file.read_text())
            assert isinstance(cache_data, dict), "Cache corrupted (not a dict)"
        except json.JSONDecodeError as e:
            pytest.fail(f"Cache file corrupted: {e}")


def test_concurrent_inspect_commands():
    """Inspect commands must be read-only and safe to run concurrently."""

    commands = [
        [PYTHON, "-m", "runtime.verify", "inspect", "health"],
        [PYTHON, "-m", "runtime.verify", "inspect", "capabilities"],
        [PYTHON, "-m", "runtime.verify", "inspect", "health"],
        [PYTHON, "-m", "runtime.verify", "inspect", "capabilities"],
        [PYTHON, "-m", "runtime.verify", "inspect", "health"],
    ]

    def run_command(cmd):
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_command, cmd) for cmd in commands]
        results = [f.result() for f in as_completed(futures)]

    failures = [r for r in results if r.returncode != 0]
    assert len(failures) == 0, f"{len(failures)} inspect commands failed"


def test_concurrent_mutation_incremental():
    """Multiple incremental mutation runs must not interfere."""

    commands = [
        [
            PYTHON,
            "-m",
            "runtime.verify",
            "strengthen",
            "--target",
            "backend/src/engines/loan_engine/emi.py",
            "--smoke",
        ],
        [
            PYTHON,
            "-m",
            "runtime.verify",
            "strengthen",
            "--target",
            "backend/src/engines/balance_engine/balance.py",
            "--smoke",
        ],
    ]

    def run_command(cmd):
        return subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_command, cmd) for cmd in commands]
        results = [f.result() for f in as_completed(futures)]

    for result in results:
        assert result.returncode in [
            0,
            1,
            2,
        ], f"Mutation crashed: {result.stderr[-500:]}"


def test_evidence_directory_under_concurrent_load():
    """Evidence directory must handle concurrent writes without corruption."""

    commands = [
        [PYTHON, "-m", "runtime.verify", "plan", "--scope", "backend"],
        [PYTHON, "-m", "runtime.verify", "plan", "--scope", "frontend"],
        [PYTHON, "-m", "runtime.verify", "plan", "--scope", "runtime"],
    ]

    generated_dir = Path("runtime/generated")
    before_files = (
        set(generated_dir.rglob("*.json")) if generated_dir.exists() else set()
    )

    def run_command(cmd):
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_command, cmd) for cmd in commands]
        [f.result() for f in as_completed(futures)]

    after_files = (
        set(generated_dir.rglob("*.json")) if generated_dir.exists() else set()
    )
    new_files = after_files - before_files

    corrupted = []
    for file in new_files:
        try:
            import json

            json.loads(file.read_text())
        except json.JSONDecodeError:
            corrupted.append(file)

    assert len(corrupted) == 0, f"Concurrent writes corrupted {len(corrupted)} files"
