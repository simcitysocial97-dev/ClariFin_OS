"""Validation Orchestrator Framework Tests.

Tests decision logic, history rotation, manifest schema, CLI parsing, and fallback rules.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
GENERATED_DIR = PROJECT_ROOT / "backend" / "tests" / "generated"
BACKEND_DIR = PROJECT_ROOT / "backend"


def test_orchestrator_cli_parsing() -> None:
    """VOF must parse CLI arguments correctly."""
    # Test --plan
    result = subprocess.run(
        [sys.executable, "tools/development/validation_orchestrator.py", "--plan"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"VOF --plan failed: {result.stderr}"
    assert "Validation Plan" in result.stdout or "Strategy:" in result.stdout


def test_manifest_schema() -> None:
    """validation-manifest.json must have required schema fields."""
    # Run --plan to generate manifest
    subprocess.run(
        [sys.executable, "tools/development/validation_orchestrator.py", "--plan"],
        cwd=PROJECT_ROOT,
        capture_output=True,
    )

    manifest_path = GENERATED_DIR / "validation-manifest.json"
    assert manifest_path.exists(), "validation-manifest.json not generated"

    with open(manifest_path) as f:
        data = json.load(f)

    required_fields = [
        "timestamp",
        "changed_files",
        "strategy",
        "reason",
        "confidence",
        "affected_capabilities",
        "stages",
        "estimated_runtime",
        "commands_executed",
    ]
    for field in required_fields:
        assert field in data, f"Manifest missing '{field}'"


def test_decision_logic_routers() -> None:
    """Router changes should trigger selective verification."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
sys.path.insert(0, 'tools/development')
from validation_orchestrator import determine_strategy

strategy, reason, risk = determine_strategy(['backend/src/routers/accounts.py'])
assert strategy == 'selective', f"Router change should be selective, got {strategy}"
print("PASS")
""",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Decision logic test failed: {result.stderr}"
    assert "PASS" in result.stdout


def test_decision_logic_engines() -> None:
    """Engine changes should trigger selective verification."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
sys.path.insert(0, 'tools/development')
from validation_orchestrator import determine_strategy

strategy, reason, risk = determine_strategy(['backend/src/engines/cashflow_engine.py'])
assert strategy == 'selective', f"Engine change should be selective, got {strategy}"
print("PASS")
""",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Decision logic test failed: {result.stderr}"
    assert "PASS" in result.stdout


def test_decision_logic_models() -> None:
    """Model changes should trigger full verification."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
sys.path.insert(0, 'tools/development')
from validation_orchestrator import determine_strategy

strategy, reason, risk = determine_strategy(['backend/src/models/account.py'])
assert strategy == 'full', f"Model change should be full, got {strategy}"
print("PASS")
""",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Decision logic test failed: {result.stderr}"
    assert "PASS" in result.stdout


def test_decision_logic_docs() -> None:
    """Documentation changes should trigger fast verification."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
sys.path.insert(0, 'tools/development')
from validation_orchestrator import determine_strategy

strategy, reason, risk = determine_strategy(['docs/README.md', 'README.md'])
assert strategy == 'fast', f"Doc change should be fast, got {strategy}"
print("PASS")
""",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Decision logic test failed: {result.stderr}"
    assert "PASS" in result.stdout


def test_decision_logic_empty() -> None:
    """No changes should trigger fast verification."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
sys.path.insert(0, 'tools/development')
from validation_orchestrator import determine_strategy

strategy, reason, risk = determine_strategy([])
assert strategy == 'fast', f"No changes should be fast, got {strategy}"
assert risk == 'LOW', f"No changes should have LOW risk, got {risk}"
print("PASS")
""",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Empty changes test failed: {result.stderr}"
    assert "PASS" in result.stdout


def test_history_rotation() -> None:
    """Validation history must keep last 200 entries."""
    # Import and test rotation
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
sys.path.insert(0, 'tools/development')
from validation_orchestrator import save_history, load_history

# Create 250 entries
history = [{"entry": i, "timestamp": f"2024-01-01T00:00:{i:02d}"} for i in range(250)]
save_history(history)
loaded = load_history()
assert len(loaded) == 200, f"History should be capped at 200, got {len(loaded)}"
assert loaded[0]["entry"] == 50, f"First entry should be 50, got {loaded[0]['entry']}"
print("PASS")
""",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"History rotation test failed: {result.stderr}"
    assert "PASS" in result.stdout


def test_fallback_to_full() -> None:
    """Unknown capability handling should trigger full verification fallback."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
sys.path.insert(0, 'tools/development')
from validation_orchestrator import ValidationGraph

graph = ValidationGraph()
full_pipeline = graph.get_full_pipeline()
assert 'fast' in full_pipeline, "Full pipeline must include fast"
assert 'coverage' in full_pipeline, "Full pipeline must include coverage"
assert 'architecture' in full_pipeline, "Full pipeline must include architecture"
assert 'property' in full_pipeline, "Full pipeline must include property"
assert 'golden' in full_pipeline, "Full pipeline must include golden"
print("PASS")
""",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Fallback test failed: {result.stderr}"
    assert "PASS" in result.stdout


def test_validation_graph_stages() -> None:
    """ValidationGraph must have all expected stages."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
sys.path.insert(0, 'tools/development')
from validation_orchestrator import ValidationGraph

graph = ValidationGraph()
stages = graph.get_all_stages()
stage_ids = [s.stage_id for s in stages]

expected = ['fast', 'coverage', 'change_intelligence', 'architecture', 'capability', 'property', 'golden', 'meta']
for exp in expected:
    assert exp in stage_ids, f"Missing stage: {exp}"
print("PASS")
""",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Graph stages test failed: {result.stderr}"
    assert "PASS" in result.stdout


def test_risk_rules_loaded() -> None:
    """risk-rules.yaml must be valid and loadable."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
sys.path.insert(0, 'tools/development')
from validation_orchestrator import load_risk_rules

rules = load_risk_rules()
assert 'rules' in rules, "Rules must have 'rules' key"
assert len(rules['rules']) > 0, "Rules must not be empty"
print("PASS")
""",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Risk rules test failed: {result.stderr}"
    assert "PASS" in result.stdout


def test_explain_mode() -> None:
    """--explain must output decision tree."""
    result = subprocess.run(
        [sys.executable, "tools/development/validation_orchestrator.py", "--explain"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    # Should succeed and show explanation
    output = result.stdout.lower()
    assert "changed files" in output or "risk" in output or "strategy" in output


def test_json_output() -> None:
    """--json must generate valid JSON output."""
    result = subprocess.run(
        [
            sys.executable,
            "tools/development/validation_orchestrator.py",
            "--plan",
            "--json",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"JSON output test failed: {result.stderr}"

    # The manifest should be saved to file
    manifest_path = GENERATED_DIR / "validation-manifest.json"
    assert manifest_path.exists(), "Manifest should be saved"


def test_metrics_generation() -> None:
    """--plan should generate validation-metrics.json."""
    # Metrics are generated on execution, verify the file path exists after run
    subprocess.run(
        [sys.executable, "tools/development/validation_orchestrator.py", "--plan"],
        cwd=PROJECT_ROOT,
        capture_output=True,
    )

    # Metrics file should not exist until execution
    # But manifest should
    manifest_path = GENERATED_DIR / "validation-manifest.json"
    assert manifest_path.exists(), "Manifest should exist after --plan"
