"""F006 - Configuration divergence detection tests.

Hermeticity
-----------
The divergence checks read ``verification.yaml`` through
``config_loader._load_yaml()``, which resolves ``DEFAULT_YAML_PATH`` — the
repository's own tracked production config
(``config_loader.py:22-25``).

The two divergence tests below need an out-of-range value to be present in
that document. Writing the edit into the real file is what the suite used to
do, inside a ``try/finally``. A ``finally`` does not run when a process is
killed outright, so an interrupted run left ``coverage_threshold: 999``
committed to the production config; and because the window is
CWD-relative, the write only landed at all when pytest happened to start from
the repository root.

Both tests now copy the real config into ``tmp_path``, point the loader at
the copy with ``monkeypatch``, and edit the copy. ``reload_config`` clears the
loader cache and its own docstring names this exact use ("useful in tests
that patch the yaml file"), so the redirection is the intended mechanism. The
assertions are unchanged and the loader reads byte-identical content.
"""

from __future__ import annotations

import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
import yaml

CONFIG_PATH = "runtime/foundation/verification/verification.yaml"


@pytest.fixture
def mutable_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[Path, None, None]:
    """An isolated, writable copy of the production verification.yaml.

    ``monkeypatch`` restores ``config_loader.DEFAULT_YAML_PATH`` on teardown,
    including if the test body is interrupted.
    """
    from runtime.foundation.verification import config_loader

    repo_root = config_loader.REPO_ROOT
    real_config = repo_root / CONFIG_PATH
    isolated = tmp_path / "verification.yaml"
    shutil.copy2(real_config, isolated)

    monkeypatch.setattr(config_loader, "DEFAULT_YAML_PATH", isolated)
    config_loader.reload_config()
    yield isolated
    config_loader.reload_config()


def test_configuration_divergence_consistent() -> None:
    """Test that consistent configuration is detected as CONSISTENT."""
    from runtime.foundation.verification.config_loader import (
        ConfigDivergenceState,
        check_configuration_divergence,
    )

    state, findings = check_configuration_divergence()
    assert state == ConfigDivergenceState.CONSISTENT
    assert len(findings) == 0


def test_configuration_divergence_out_of_range(
    mutable_config: Path,
) -> None:
    """Test that out-of-range thresholds are detected as DIVERGED."""
    from runtime.foundation.verification.config_loader import (
        ConfigDivergenceState,
        check_configuration_divergence,
        reload_config,
    )

    # Inject an invalid coverage threshold
    data = yaml.safe_load(mutable_config.read_text())
    data["backend"]["coverage_threshold"] = 999
    mutable_config.write_text(yaml.dump(data))
    reload_config()

    state, findings = check_configuration_divergence()
    assert state == ConfigDivergenceState.DIVERGED
    assert any(f["check"] == "backend.coverage_threshold" for f in findings)


def test_configuration_divergence_regression_thresholds(
    mutable_config: Path,
) -> None:
    """Test that inverted regression thresholds are detected."""
    from runtime.foundation.verification.config_loader import (
        ConfigDivergenceState,
        check_configuration_divergence,
        reload_config,
    )

    # Inject inverted regression thresholds
    data = yaml.safe_load(mutable_config.read_text())
    if "regression_thresholds" not in data:
        data["regression_thresholds"] = {}
    data["regression_thresholds"]["coverage_drop_warning"] = 20
    data["regression_thresholds"]["coverage_drop_critical"] = 10
    mutable_config.write_text(yaml.dump(data))
    reload_config()

    state, findings = check_configuration_divergence()
    assert state == ConfigDivergenceState.DIVERGED
    assert any("coverage_drop" in f["check"] for f in findings)
