# runtime/foundation/verification/env.py
#
# M9-C42.5 — Canonical environment resolver & consistency guard.
#
# THE canonical Python environment for ClariFin_OS is the REPOSITORY-ROOT
# `.venv` (created by scripts/bootstrap.sh and consumed by scripts/verify.sh).
# CI installs the SAME dependency contract (`pip install -e ".[all]"`) and
# exposes the same tools on PATH, so resolving via `.venv` first then PATH
# yields identical tooling locally and in CI.
#
# This module is the SINGLE place that:
#   * resolves mutmut / pytest / python binaries,
#   * pins and validates the mutmut + pytest + python contract,
#   * detects stray/duplicate virtualenvs (e.g. backend/venv),
#   * emits a machine-readable environment fingerprint for drift visibility.
#
# It never raises on detection — it returns a structured report so callers
# (the mutation runner, `verify.py env-check`, CI steps) decide whether to
# fail. This prevents silent path/environment inconsistencies from recurring.

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
VENV_BIN = REPO_ROOT / ".venv" / "bin"

# Pinned contract (single source of truth = root pyproject.toml).
PINNED_MUTMUT = "3.7.0"
MIN_PYTHON = (3, 12)

# Virtualenv locations that must NEVER exist. The only allowed env is
# REPO_ROOT/.venv. backend/venv historically shadowed it and produced a
# different mutmut/pytest toolchain — the root cause of M9-C42.5.
FORBIDDEN_VENV_DIRS = [
    REPO_ROOT / "backend" / "venv",
    REPO_ROOT / "backend" / ".venv",
]


@dataclass(frozen=True, slots=True)
class Tool:
    name: str
    path: str | None
    version: str | None
    source: str  # "venv" | "path" | "missing"


@dataclass(frozen=True, slots=True)
class EnvironmentReport:
    python: Tool
    pytest: Tool
    mutmut: Tool
    forbidden_venvs: tuple[str, ...]
    fingerprint: dict
    consistent: bool
    errors: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "python": asdict(self.python),
            "pytest": asdict(self.pytest),
            "mutmut": asdict(self.mutmut),
            "forbidden_venvs": list(self.forbidden_venvs),
            "fingerprint": self.fingerprint,
            "consistent": self.consistent,
            "errors": list(self.errors),
        }


def _resolve(tool: str) -> tuple[str | None, str]:
    """Return (resolved_path, source). Prefer REPO_ROOT/.venv/bin, then PATH."""
    venv_path = VENV_BIN / tool
    if venv_path.is_file():
        return str(venv_path), "venv"
    on_path = shutil.which(tool)
    if on_path:
        return on_path, "path"
    return None, "missing"


def _version(path: str | None, *, config_dir: Path | None = None) -> str | None:
    """Get a tool version. mutmut auto-loads config at import, so run it from a
    directory that has a [tool.mutmut] section when possible."""
    if not path:
        return None
    cwd = str(config_dir) if config_dir else None
    try:
        out = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
        line = (out.stdout or out.stderr).strip().splitlines()
        return line[0] if line else None
    except Exception:
        return None


def _resolve_tool(name: str, *, config_dir: Path | None = None) -> Tool:
    path, source = _resolve(name)
    ver = _version(path, config_dir=config_dir)
    return Tool(name=name, path=path, version=ver, source=source)


def resolve_environment(
    *,
    config_dir: Path | None = None,
    profile: str | None = None,
    capability_selection: list[str] | None = None,
) -> EnvironmentReport:
    """Resolve and validate the canonical mutation environment."""
    errors: list[str] = []

    py = _resolve_tool("python3")
    pytest = _resolve_tool("pytest")
    mutmut = _resolve_tool("mutmut", config_dir=config_dir or (REPO_ROOT / "backend"))

    # Python version check.
    py_ok = False
    if py.path:
        try:
            out = subprocess.run(
                [py.path, "-c", "import sys;print('%d.%d'%sys.version_info[:2])"],
                capture_output=True,
                text=True,
                timeout=30,
            ).stdout.strip()
            major, minor = (int(x) for x in out.split("."))
            py_ok = (major, minor) >= MIN_PYTHON
            py_version: str | None = out
        except Exception:
            py_version = py.version
    else:
        py_version = None
    if not py_ok:
        errors.append(
            f"python >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]} required "
            f"(resolved: {py_version or 'missing'})"
        )

    if pytest.path is None:
        errors.append("pytest not found on PATH or in .venv")

    if mutmut.path is None:
        errors.append("mutmut not found on PATH or in .venv")
    elif mutmut.version is None or PINNED_MUTMUT not in (mutmut.version or ""):
        errors.append(
            f"mutmut=={PINNED_MUTMUT} required (resolved: {mutmut.version or 'unknown'})"
        )

    # Forbidden venv detection.
    forbidden: list[str] = []
    for d in FORBIDDEN_VENV_DIRS:
        if d.exists():
            rel = d.relative_to(REPO_ROOT) if d.is_relative_to(REPO_ROOT) else d
            forbidden.append(str(rel))
    if forbidden:
        errors.append(
            "forbidden virtualenv present (must use repo-root .venv only): "
            + ", ".join(forbidden)
        )

    fingerprint = build_fingerprint(
        py,
        pytest,
        mutmut,
        forbidden,
        profile=profile,
        capability_selection=capability_selection,
    )

    return EnvironmentReport(
        python=py,
        pytest=pytest,
        mutmut=mutmut,
        forbidden_venvs=tuple(forbidden),
        fingerprint=fingerprint,
        consistent=not errors,
        errors=tuple(errors),
    )


def build_fingerprint(
    py: Tool,
    pytest: Tool,
    mutmut: Tool,
    forbidden: list[str],
    *,
    profile: str | None = None,
    capability_selection: list[str] | None = None,
) -> dict:
    """Machine-readable environment fingerprint for drift visibility.

    Extended fingerprint includes:
    - Tool versions (python, pytest, ruff, black, mypy, coverage, mutmut)
    - Config hashes (pyproject.toml, ruff config, black config, mypy config)
    - Dependency lock fingerprint
    - Verification profile
    - Capability selection
    - Repository revision
    """
    repo_root = REPO_ROOT

    # Core tool versions
    ruff_tool = _resolve_tool("ruff")
    black_tool = _resolve_tool("black")
    mypy_tool = _resolve_tool("mypy")
    coverage_tool = _resolve_tool("coverage")

    # Config hashes
    pyproject_hash = hash_file(repo_root / "pyproject.toml")
    ruff_config_hash = (
        hash_file(repo_root / "backend" / "ruff.toml")
        if (repo_root / "backend" / "ruff.toml").exists()
        else "missing"
    )
    black_config_hash = "embedded_in_pyproject"  # black config is in pyproject.toml
    mypy_config_hash = hash_file(repo_root / "backend" / "pyproject.toml")

    # Dependency lock fingerprint
    lock_hash = hash_file(repo_root / "requirements.lock")

    # Repository revision
    repo_sha = "unknown"
    try:
        repo_sha = (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
            or "unknown"
        )
    except Exception:
        pass

    return {
        # Core tools
        "python_version": py.version,
        "python_source": py.source,
        "python_path": py.path,
        "pytest_version": pytest.version,
        "pytest_source": pytest.source,
        "mutmut_version": mutmut.version,
        "mutmut_source": mutmut.source,
        "pinned_mutmut": PINNED_MUTMUT,
        "forbidden_venvs": forbidden,
        "venv_bin": str(VENV_BIN),
        # Extended toolchain
        "ruff_version": ruff_tool.version,
        "ruff_source": ruff_tool.source,
        "black_version": black_tool.version,
        "black_source": black_tool.source,
        "mypy_version": mypy_tool.version,
        "mypy_source": mypy_tool.source,
        "coverage_version": coverage_tool.version,
        "coverage_source": coverage_tool.source,
        # Config hashes
        "config_hashes": {
            "pyproject_toml": pyproject_hash,
            "ruff_toml": ruff_config_hash,
            "black": black_config_hash,
            "mypy": mypy_config_hash,
        },
        # Dependency lock
        "requirements_lock_hash": lock_hash,
        # Repository state
        "repository_sha": repo_sha,
        # Profile & capability
        "verification_profile": profile,
        "capability_selection": capability_selection or [],
        # Fingerprint version for future compatibility
        "fingerprint_version": "1.0",
    }


def _build_minimal_fingerprint(
    py: Tool, pytest: Tool, mutmut: Tool, forbidden: list[str]
) -> dict:
    """Minimal fingerprint for env-check (backward compatible)."""
    return {
        "python_version": py.version,
        "python_source": py.source,
        "pytest_version": pytest.version,
        "pytest_source": pytest.source,
        "mutmut_version": mutmut.version,
        "mutmut_source": mutmut.source,
        "pinned_mutmut": PINNED_MUTMUT,
        "forbidden_venvs": forbidden,
        "venv_bin": str(VENV_BIN),
    }


def hash_file(path: Path) -> str:

    if not path.is_file():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def main_env_check(argv: list[str]) -> int:
    """`verify.py env-check` — print fingerprint, exit non-zero if inconsistent.

    Flags:
        --full    Include extended fingerprint (tool versions, config hashes, lock hash, repo SHA)
    """
    full = "--full" in argv
    report = resolve_environment()

    if full:
        # Print extended fingerprint
        print(json.dumps(report.fingerprint, indent=2))
    else:
        # Print minimal fingerprint (backward compatible)
        print(
            json.dumps(
                {
                    "python": asdict(report.python),
                    "pytest": asdict(report.pytest),
                    "mutmut": asdict(report.mutmut),
                    "forbidden_venvs": list(report.forbidden_venvs),
                    "fingerprint": _build_minimal_fingerprint(
                        report.python,
                        report.pytest,
                        report.mutmut,
                        list(report.forbidden_venvs),
                    ),
                    "consistent": report.consistent,
                    "errors": list(report.errors),
                },
                indent=2,
            )
        )

    if report.consistent:
        print("\nENVIRONMENT CONSISTENT — canonical .venv is the only environment.")
        return 0
    print(
        "\nENVIRONMENT INCONSISTENT — resolve before running mutation:",
        file=sys.stderr,
    )
    for e in report.errors:
        print(f"  - {e}", file=sys.stderr)
    return 1
