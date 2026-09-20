"""F006 - Configuration divergence detection tests."""
import pytest


def test_configuration_divergence_consistent():
    """Test that consistent configuration is detected as CONSISTENT."""
    from runtime.foundation.verification.config_loader import (
        check_configuration_divergence,
        ConfigDivergenceState,
    )

    state, findings = check_configuration_divergence()
    assert state == ConfigDivergenceState.CONSISTENT
    assert len(findings) == 0


def test_configuration_divergence_out_of_range():
    """Test that out-of-range thresholds are detected as DIVERGED."""
    from runtime.foundation.verification.config_loader import (
        check_configuration_divergence,
        ConfigDivergenceState,
        _load_yaml,
        reload_config,
    )
    import yaml
    from pathlib import Path

    yaml_path = Path("runtime/foundation/verification/verification.yaml")
    original_content = yaml_path.read_text()

    try:
        # Inject an invalid coverage threshold
        data = yaml.safe_load(original_content)
        data["backend"]["coverage_threshold"] = 999
        yaml_path.write_text(yaml.dump(data))
        reload_config()

        state, findings = check_configuration_divergence()
        assert state == ConfigDivergenceState.DIVERGED
        assert any(f["check"] == "backend.coverage_threshold" for f in findings)
    finally:
        # Restore original configuration
        yaml_path.write_text(original_content)
        reload_config()


def test_configuration_divergence_regression_thresholds():
    """Test that inverted regression thresholds are detected."""
    from runtime.foundation.verification.config_loader import (
        check_configuration_divergence,
        ConfigDivergenceState,
        reload_config,
    )
    import yaml
    from pathlib import Path

    yaml_path = Path("runtime/foundation/verification/verification.yaml")
    original_content = yaml_path.read_text()

    try:
        # Inject inverted regression thresholds
        data = yaml.safe_load(original_content)
        if "regression_thresholds" not in data:
            data["regression_thresholds"] = {}
        data["regression_thresholds"]["coverage_drop_warning"] = 20
        data["regression_thresholds"]["coverage_drop_critical"] = 10
        yaml_path.write_text(yaml.dump(data))
        reload_config()

        state, findings = check_configuration_divergence()
        assert state == ConfigDivergenceState.DIVERGED
        assert any("coverage_drop" in f["check"] for f in findings)
    finally:
        # Restore original configuration
        yaml_path.write_text(original_content)
        reload_config()
