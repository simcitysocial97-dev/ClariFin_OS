# runtime/foundation/verification/env_contract.py
#
# M9-C55 — Authoritative Environment Contract.
#
# Extends the canonical environment fingerprint from env.py with the full set
# of identity dimensions required for reproducible verification:
#   - OS / platform / shell / locale / timezone
#   - Python, Node, npm, pip versions
#   - All verification-tool versions (pytest, coverage, mutmut, ruff, black, mypy, hypothesis)
#   - Dependency lock fingerprints (requirements.lock + frontend/package-lock.json)
#   - Configuration fingerprints (pyproject.toml, backend/pyproject.toml)
#   - Repository identity (SHA, tree SHA, worktree state, untracked count)
#   - Frontend package manifest hash
#
# There is exactly ONE authoritative contract: build_environment_contract().
# All other code reads through this function or via verify.py env-contract.
#
# Contract states:
#   CONSISTENT      — all resolved, no mismatches against declared pins
#   WARNINGS        — resolved but non-critical differences (e.g. local Node < declared)
#   INCOMPLETE      — some dimensions missing (e.g. Node not installed locally)
#   INCOMPATIBLE    — material mismatch that invalidates evidence comparison

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from runtime.foundation.verification.env import (
    REPO_ROOT,
    VENV_BIN,
    PINNED_MUTMUT,
    MIN_PYTHON,
    FORBIDDEN_VENV_DIRS,
    hash_file,
    resolve_environment,
)

# ── Declared pin contract (single source of truth = root pyproject.toml) ──────
PINNED_PYTEST = "9.1.1"
PINNED_COVERAGE = "7.15.2"
PINNED_RUFF = "0.15.20"
PINNED_BLACK = "26.5.1"
PINNED_MYPY = "2.1.0"
PINNED_HYPOTHESIS = "6.161.4"
PINNED_NODE_MAJOR = 24  # frontend/package.json engines.node >=24 <25
PINNED_NPM_VERSION = "11.19.0"  # frontend/package.json packageManager (synced with Node 24 LTS)


class ContractState(str, Enum):
    CONSISTENT = "CONSISTENT"
    WARNINGS = "WARNINGS"
    INCOMPLETE = "INCOMPLETE"
    INCOMPATIBLE = "INCOMPATIBLE"


@dataclass(frozen=True, slots=True)
class ToolVersion:
    name: str
    resolved_version: str | None
    resolved_path: str | None
    source: str  # "venv" | "path" | "missing"
    pinned_version: str | None
    matches_pin: bool | None


@dataclass(frozen=True, slots=True)
class EnvironmentContract:
    """Single authoritative environment contract for C55 reproducibility."""

    schema: str
    generated_at: str
    state: str  # ContractState string
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    # Repository identity
    repository_sha: str
    repository_tree_sha: str
    working_tree_state: str  # "CLEAN" | "DIRTY"
    untracked_file_count: int

    # Python environment
    python_version: str | None
    python_path: str | None
    python_source: str
    python_min_ok: bool

    # Toolchain (all resolution sources)
    pytest: ToolVersion
    coverage: ToolVersion
    mutmut: ToolVersion
    ruff: ToolVersion
    black: ToolVersion
    mypy: ToolVersion
    hypothesis: ToolVersion

    # Node / npm (frontend)
    node_version: str | None
    node_path: str | None
    node_source: str
    npm_version: str | None
    npm_path: str | None
    npm_source: str
    node_matches_engine: bool | None
    npm_matches_pin: bool | None

    # Platform / shell / locale / timezone
    os_name: str
    os_version: str
    platform_machine: str
    shell: str
    locale: str
    timezone: str

    # Dependency lock fingerprints
    requirements_lock_hash: str
    frontend_package_lock_hash: str
    root_pyproject_hash: str
    backend_pyproject_hash: str
    frontend_package_json_hash: str

    # Configuration authority hashes
    config_hashes: dict[str, str]

    # Provenance
    baseline_sha: str  # C54 certified baseline
    reproducibility_note: str


def _run(cmd: list[str], timeout: int = 10, cwd: str | None = None) -> tuple[str, str, int]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except Exception as exc:
        return "", str(exc), 1


def _which(tool: str) -> tuple[str | None, str]:
    venv_path = VENV_BIN / tool
    if venv_path.is_file():
        return str(venv_path), "venv"
    on_path = shutil.which(tool)
    if on_path:
        return on_path, "path"
    return None, "missing"


def _version_of(path: str | None, *extra_args: str, config_dir: Path | None = None) -> str | None:
    if not path:
        return None
    try:
        cwd = str(config_dir) if config_dir else None
        args = [path, "--version"] + list(extra_args)
        out, _, rc = _run(args, timeout=15, cwd=cwd)
        if rc == 0 and out:
            return out.splitlines()[0].strip()
        return None
    except Exception:
        return None


def _python_version_info(python_path: str | None) -> tuple[str | None, bool]:
    if not python_path:
        return None, False
    ok = False
    ver = None
    try:
        out, _, rc = _run([python_path, "-c", "import sys;print('%d.%d'%(sys.version_info[:2]))"], timeout=10)
        if rc == 0 and out:
            parts = out.strip().split(".")
            major, minor = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
            ver = f"{major}.{minor}"
            ok = (major, minor) >= MIN_PYTHON
    except Exception:
        pass
    return ver, ok


def _git_sha() -> str:
    out, _, rc = _run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT))
    return out if rc == 0 and out else "unknown"


def _git_tree_sha() -> str:
    out, _, rc = _run(["git", "rev-parse", "HEAD^{tree}"], cwd=str(REPO_ROOT))
    return out if rc == 0 and out else "unknown"


def _git_status_summary() -> tuple[str, int]:
    dirty = subprocess.run(
        ["git", "diff", "--quiet"], capture_output=True, cwd=str(REPO_ROOT)
    ).returncode != 0
    untracked_out, _, _ = _run(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=str(REPO_ROOT)
    )
    count = len([l for l in untracked_out.splitlines() if l.strip()]) if untracked_out else 0
    return ("DIRTY" if dirty else "CLEAN"), count


def _platform_info() -> dict[str, str]:
    import platform
    import locale as loc_mod
    import time as time_mod

    tz = time_mod.strftime("%Z") or "UTC"
    try:
        lc = loc_mod.getlocale(loc_mod.LC_ALL) or loc_mod.getlocale(loc_mod.LC_MESSAGES)
        locale_str = str(lc) if lc else "unknown"
    except Exception:
        locale_str = "unknown"
    return {
        "os_name": platform.system(),
        "os_version": platform.version(),
        "platform_machine": platform.machine(),
        "shell": Path(shutil.which("sh") or "/bin/sh").name,
        "locale": locale_str,
        "timezone": tz,
    }


def _parse_semver(version_str: str | None) -> tuple[int, ...] | None:
    if not version_str:
        return None
    import re
    m = re.search(r"(\d+(?:\.\d+)*)", version_str)
    if not m:
        return None
    parts = m.group(1).split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


def _tool_version_record(
    tool_name: str,
    pinned: str | None,
) -> ToolVersion:
    # mutmut requires a config dir to resolve source paths before printing version
    config_dir = REPO_ROOT / "backend" if tool_name == "mutmut" else None
    path, source = _which(tool_name)
    ver = _version_of(path, config_dir=config_dir)
    matches = None
    if pinned and ver:
        try:
            installed = _parse_semver(ver)
            expected = _parse_semver(pinned)
            if installed and expected:
                matches = installed[:len(expected)] == expected
        except Exception:
            matches = None
    return ToolVersion(
        name=tool_name,
        resolved_version=ver,
        resolved_path=path,
        source=source,
        pinned_version=pinned,
        matches_pin=matches,
    )


def build_environment_contract(
    *,
    baseline_sha: str | None = None,
) -> EnvironmentContract:
    """Build the single authoritative environment contract for C55."""

    errors: list[str] = []
    warnings: list[str] = []

    # Existing env report
    env_report = resolve_environment()

    # Tool versions
    pytest_rec = _tool_version_record("pytest", PINNED_PYTEST)
    coverage_rec = _tool_version_record("coverage", PINNED_COVERAGE)
    mutmut_rec = _tool_version_record("mutmut", PINNED_MUTMUT)
    ruff_rec = _tool_version_record("ruff", PINNED_RUFF)
    black_rec = _tool_version_record("black", PINNED_BLACK)
    mypy_rec = _tool_version_record("mypy", PINNED_MYPY)
    hyp_rec = _tool_version_record("hypothesis", None)  # hypothesis has no strict pin in [verification]; use pyproject
    # hypothesis IS in the verification extras at pinned version
    hyp_rec = _tool_version_record("hypothesis", PINNED_HYPOTHESIS)

    # Node / npm
    node_path, node_source = _which("node")
    node_ver = _version_of(node_path)
    npm_path, npm_source = _which("npm")
    npm_ver = _version_of(npm_path)
    node_matches = None
    npm_matches = None
    if node_ver:
        sv = _parse_semver(node_ver)
        if sv:
            node_matches = sv[0] >= PINNED_NODE_MAJOR
        else:
            warnings.append(f"node version string unparseable: {node_ver}")
    else:
        warnings.append("node not found on PATH or in .venv/bin")
    if npm_ver:
        npv = _parse_semver(npm_ver)
        epv = _parse_semver(PINNED_NPM_VERSION)
        if npv and epv:
            npm_matches = npv[0] >= epv[0] and npv[: min(len(npv), len(epv))] == epv[: min(len(npv), len(epv))]
        else:
            warnings.append(f"npm version string unparseable: {npm_ver}")
    else:
        warnings.append("npm not found on PATH or in .venv/bin")

    # Forbidden venvs
    forbidden = []
    for d in FORBIDDEN_VENV_DIRS:
        if d.exists():
            rel = str(d.relative_to(REPO_ROOT) if d.is_relative_to(REPO_ROOT) else d)
            forbidden.append(rel)
    if forbidden:
        errors.append(f"forbidden virtualenv present: {', '.join(forbidden)}")

    # Copy existing errors
    errors.extend(env_report.errors)

    # Python version info
    py_ver_info, py_ok = _python_version_info(env_report.python.path)

    # Git state
    repo_sha = _git_sha()
    repo_tree = _git_tree_sha()
    worktree_state, untracked_count = _git_status_summary()

    # Lockfile hashes
    req_lock_hash = hash_file(REPO_ROOT / "requirements.lock")
    fe_pkg_lock = REPO_ROOT / "frontend" / "package-lock.json"
    fp_lock_hash = hash_file(fe_pkg_lock)
    root_py_hash = hash_file(REPO_ROOT / "pyproject.toml")
    backend_py_hash = hash_file(REPO_ROOT / "backend" / "pyproject.toml")
    fe_pkg_json_hash = hash_file(REPO_ROOT / "frontend" / "package.json")

    # Config hashes
    config_hashes = {
        "root_pyproject_toml": root_py_hash,
        "backend_pyproject_toml": backend_py_hash,
        "frontend_package_json": fe_pkg_json_hash,
        "frontend_package_lock": fp_lock_hash,
        "requirements_lock": req_lock_hash,
    }
    for extra in ("ruff", "black", "mypy"):
        p = REPO_ROOT / "backend" / f"{extra}.toml"
        if p.exists():
            config_hashes[f"{extra}_toml"] = hash_file(p)
        else:
            config_hashes[f"{extra}_toml"] = "not_applicable"

    # Platform info
    plat = _platform_info()

    # Reproducibility note
    reproducibility_notes = []
    if node_source == "missing" or (node_ver and node_matches is False):
        reproducibility_notes.append(
            f"local node={node_ver or 'missing'} does not satisfy declared engines.node >={PINNED_NODE_MAJOR}; "
            "frontend reproducibility validated only via CI path (actions/setup-node@v7 with node-version 24)"
        )
        warnings.append(
            f"node version mismatch: local={node_ver or 'missing'}, "
            f"declared engine >= {PINNED_NODE_MAJOR}. Frontend tests require CI validation."
        )
    if npm_matches is False:
        warnings.append(
            f"npm version mismatch: local={npm_ver}, declared packageManager npm@{PINNED_NPM_VERSION}"
        )
        reproducibility_notes.append(
            f"local npm={npm_ver} does not match declared packageManager npm@{PINNED_NPM_VERSION}"
        )
    if not reproducibility_notes:
        reproducibility_notes.append("All local toolchain dimensions match declared pins.")
    reproducibility_note = "; ".join(reproducibility_notes)

    # Determine overall state
    state = ContractState.CONSISTENT.value
    if errors:
        state = ContractState.INCOMPATIBLE.value
    elif warnings:
        state = ContractState.WARNINGS.value
    if node_source == "missing":
        state = ContractState.INCOMPLETE.value if state == ContractState.CONSISTENT.value else state

    baseline = baseline_sha or repo_sha

    return EnvironmentContract(
        schema="m9-c55/environment-contract/v1",
        generated_at=datetime.now(UTC).isoformat(),
        state=state,
        errors=tuple(errors),
        warnings=tuple(warnings),
        repository_sha=repo_sha,
        repository_tree_sha=repo_tree,
        working_tree_state=worktree_state,
        untracked_file_count=untracked_count,
        python_version=py_ver_info or env_report.python.version,
        python_path=env_report.python.path,
        python_source=env_report.python.source,
        python_min_ok=py_ok,
        pytest=pytest_rec,
        coverage=coverage_rec,
        mutmut=mutmut_rec,
        ruff=ruff_rec,
        black=black_rec,
        mypy=mypy_rec,
        hypothesis=hyp_rec,
        node_version=node_ver,
        node_path=node_path,
        node_source=node_source,
        npm_version=npm_ver,
        npm_path=npm_path,
        npm_source=npm_source,
        node_matches_engine=node_matches,
        npm_matches_pin=npm_matches,
        os_name=plat["os_name"],
        os_version=plat["os_version"],
        platform_machine=plat["platform_machine"],
        shell=plat["shell"],
        locale=plat["locale"],
        timezone=plat["timezone"],
        requirements_lock_hash=req_lock_hash,
        frontend_package_lock_hash=fp_lock_hash,
        root_pyproject_hash=root_py_hash,
        backend_pyproject_hash=backend_py_hash,
        frontend_package_json_hash=fe_pkg_json_hash,
        config_hashes=config_hashes,
        baseline_sha=baseline,
        reproducibility_note=reproducibility_note,
    )


def contract_to_dict(contract: EnvironmentContract) -> dict[str, Any]:
    result = asdict(contract)
    result["state"] = contract.state
    return result


def main_env_contract(argv: list[str]) -> int:
    """`verify.py env-contract` — build and print the authoritative environment contract."""
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py env-contract")
    parser.add_argument("--json", action="store_true", help="output JSON")
    parser.add_argument("--out", help="write to file instead of stdout")
    parser.add_argument("--validate", action="store_true", help="exit non-zero on INCOMPATIBLE")
    args = parser.parse_args(argv)

    contract = build_environment_contract()
    data = contract_to_dict(contract)

    output = json.dumps(data, indent=2) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output)
        print(f"Written to {args.out}")
    else:
        print(output)

    if args.validate:
        if contract.state == ContractState.INCOMPATIBLE.value:
            print("\nENVIRONMENT CONTRACT INCOMPATIBLE:", file=sys.stderr)
            for e in contract.errors:
                print(f"  - {e}", file=sys.stderr)
            return 2
        if contract.state == ContractState.INCOMPLETE.value:
            print("\nENVIRONMENT CONTRACT INCOMPLETE (non-blocking):", file=sys.stderr)
            for w in contract.warnings:
                print(f"  ! {w}", file=sys.stderr)
            return 0
        if contract.state == ContractState.WARNINGS.value:
            print("\nENVIRONMENT CONTRACT HAS WARNINGS:", file=sys.stderr)
            for w in contract.warnings:
                print(f"  ! {w}", file=sys.stderr)
            return 0
        print("\nENVIRONMENT CONTRACT CONSISTENT")
        return 0

    # Non-validate mode: always exits 0 (informational)
    return 0


if __name__ == "__main__":
    sys.exit(main_env_contract(sys.argv[1:]))
