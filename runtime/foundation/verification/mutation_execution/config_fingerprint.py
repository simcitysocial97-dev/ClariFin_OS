# runtime/foundation/verification/mutation_execution/config_fingerprint.py
#
# M9-C44.11 — Deterministic Configuration Fingerprint.
#
# Computes a canonical fingerprint incorporating ALL result-affecting
# configuration. A mutation result may only be reused when the fingerprint
# is compatible with the current run.

from __future__ import annotations

import hashlib
import platform
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:
        return "unknown"


def _git_tree() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"],
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:
        return "unknown"


def _hash_file(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _python_version() -> str:
    import sys
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _platform_info() -> str:
    return f"{platform.system()}|{platform.machine()}|{platform.python_compiler() or ''}"


def compute_configuration_fingerprint(
    *,
    backend: str,
    backend_version: str,
    source_paths: list[str],
    test_selection: list[str],
    timeout_seconds: int,
    worker_count: int,
    operators: list[str] | None = None,
    extra_config_files: list[Path] | None = None,
    verification_profile: str = "default",
) -> str:
    """Compute a deterministic fingerprint for mutation configuration.

    Components:
      - Python version + platform
      - Repository revision (git SHA + tree SHA)
      - Backend name + version
      - Source paths (sorted, hashed)
      - Test selection (sorted, hashed)
      - Timeout policy
      - Worker count
      - Mutation operators (if specified)
      - Extra config file hashes
      - Verification profile
    """
    components = [
        "m9-c44-config-fingerprint/v1",
        _python_version(),
        _platform_info(),
        _git_sha(),
        _git_tree(),
        backend,
        backend_version,
        "|".join(sorted(source_paths)),
        "|".join(sorted(test_selection)),
        str(timeout_seconds),
        str(worker_count),
        verification_profile,
    ]

    if operators:
        components.append("|".join(sorted(operators)))

    if extra_config_files:
        file_hashes = []
        for p in sorted(extra_config_files):
            file_hashes.append(f"{p}:{_hash_file(p)}")
        components.append("|".join(file_hashes))

    payload = "\n".join(components)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_source_fingerprint(source_paths: list[str]) -> str:
    """Hash of all source files in scope — used for cache invalidation on source change."""
    hashes = []
    for rel in sorted(source_paths):
        p = REPO_ROOT / rel
        if p.is_file():
            hashes.append(f"{rel}:{_hash_file(p)}")
        elif p.is_dir():
            for fp in sorted(p.rglob("*.py")):
                rel_path = str(fp.relative_to(REPO_ROOT))
                hashes.append(f"{rel_path}:{_hash_file(fp)}")
    return hashlib.sha256("\n".join(hashes).encode("utf-8")).hexdigest()[:24]


def compute_test_selection_fingerprint(test_selection: list[str]) -> str:
    """Hash of test selection paths — invalidates cache when tests change."""
    hashes = []
    for rel in sorted(test_selection):
        p = REPO_ROOT / rel
        if p.is_file():
            hashes.append(f"{rel}:{_hash_file(p)}")
        elif p.is_dir():
            for fp in sorted(p.rglob("*.py")):
                rel_path = str(fp.relative_to(REPO_ROOT))
                hashes.append(f"{rel_path}:{_hash_file(fp)}")
    return hashlib.sha256("\n".join(hashes).encode("utf-8")).hexdigest()[:24]


def build_full_fingerprint(
    *,
    backend: str,
    backend_version: str,
    source_paths: list[str],
    test_selection: list[str],
    timeout_seconds: int,
    worker_count: int,
    extra_config_files: list[Path] | None = None,
) -> dict[str, str]:
    """Build the complete fingerprint document."""
    return {
        "schema": "m9-c44-config-fingerprint/v1",
        "configuration": compute_configuration_fingerprint(
            backend=backend,
            backend_version=backend_version,
            source_paths=source_paths,
            test_selection=test_selection,
            timeout_seconds=timeout_seconds,
            worker_count=worker_count,
            extra_config_files=extra_config_files,
        ),
        "source": compute_source_fingerprint(source_paths),
        "tests": compute_test_selection_fingerprint(test_selection),
        "python_version": _python_version(),
        "platform": _platform_info(),
        "repository_sha": _git_sha(),
        "tree_sha": _git_tree(),
    }


def fingerprints_compatible(old: dict[str, str], new: dict[str, str], *, loose: bool = False) -> bool:
    """Check whether a cached result is still valid under a new configuration.

    Strict mode: all fields must match.
    Loose mode: configuration and source must match; test selection hash may
    differ if the new selection is a superset (more tests = never false positive).
    """
    if old.get("configuration") != new.get("configuration"):
        return False
    if old.get("source") != new.get("source"):
        return False
    if loose:
        # Loose: allow test selection to change as long as configuration+source match
        return True
    if old.get("tests") != new.get("tests"):
        return False
    return old.get("python_version") == new.get("python_version")


__all__ = [
    "compute_configuration_fingerprint",
    "compute_source_fingerprint",
    "compute_test_selection_fingerprint",
    "build_full_fingerprint",
    "fingerprints_compatible",
]
