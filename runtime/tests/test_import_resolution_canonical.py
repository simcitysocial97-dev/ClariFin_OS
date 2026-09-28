"""M9-C57 — Import-resolution regression test.

Proves that under canonical module execution (`python -m runtime.verify` from
the repository root), stdlib imports resolve correctly and are NOT shadowed by
internal packages:

  * `import platform` → stdlib
  * `platform.system()` works
  * `import uuid` works
  * `runtime.platform` is accessible via its explicit package path

This pins down the fix for the known failure class where direct script
execution (`python runtime/verify.py`) placed `runtime/` at sys.path[0],
causing `runtime.platform` to shadow the stdlib `platform`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class TestImportResolutionCanonical:
    """Verify stdlib/platform/uuid resolution under canonical model."""

    def test_platform_resolves_to_stdlib(self) -> None:
        """stdlib `platform` must NOT be shadowed by `runtime.platform`."""
        import platform

        # stdlib platform lives outside the repo; runtime.platform would
        # be inside <repo>/runtime/platform/__init__.py if shadowed.
        assert "/usr/" in platform.__file__ or platform.__file__.startswith(
            sys.base_prefix
        ), f"stdlib platform shadowed by runtime.platform: {platform.__file__}"

    def test_platform_system_works(self) -> None:
        """`platform.system()` must return a valid OS string."""
        import platform

        result = platform.system()
        assert (
            isinstance(result, str) and len(result) > 0
        ), f"platform.system() returned invalid value: {result!r}"

    def test_uuid_importable(self) -> None:
        """stdlib `uuid` must be importable without side effects."""
        import uuid

        assert hasattr(uuid, "UUID"), "stdlib uuid.UUID missing"

    def test_runtime_platform_accessible(self) -> None:
        """`runtime.platform` must be reachable via explicit package path."""
        import runtime.platform as rp

        assert rp.__file__.endswith(
            "runtime/platform/__init__.py"
        ), f"runtime.platform unresolved: {rp.__file__}"

    def test_canonical_module_execution_from_repo_root(self) -> None:
        """Run `python -m runtime.verify status` from repo root.

        This is the strongest end-to-end proof: the subprocess inherits
        cwd=repo root, so sys.path[0]=repo root, which means stdlib
        `platform` cannot be shadowed.
        """
        repo_root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, "-m", "runtime.verify", "status"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Status (now routed to doctor) should succeed with exit 0.
        assert (
            result.returncode == 0
        ), f"canonical execution failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        # Stdout must contain the health report header (proves the runtime started).
        assert (
            "Engineering Health Report" in result.stdout
            or "verification_record" in result.stdout.lower()
        ), f"unexpected output from canonical execution:\n{result.stdout[:500]}"

    def test_no_stdlib_shadowing_in_subprocess(self) -> None:
        """Explicitly prove no shadowing in a fresh subprocess from repo root."""
        repo_root = Path(__file__).resolve().parents[2]
        probe = """
import platform, uuid, sys
# stdlib platform lives outside the repo (e.g. /usr/lib/pythonX.Y/platform.py);
# runtime.platform would be at <repo>/runtime/platform/__init__.py if shadowed.
assert "/usr/" in platform.__file__ or platform.__file__.startswith(sys.base_prefix), \\
    f"shadowed: {{platform.__file__}}"
assert hasattr(uuid, "UUID"), "uuid missing"
print("OK")
"""
        result = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert (
            result.returncode == 0
        ), f"shadowing detected in subprocess:\nstderr={result.stderr}"
        assert "OK" in result.stdout
