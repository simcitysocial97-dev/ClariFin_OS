#!/usr/bin/env python3
"""
Generate Capability Health Dashboard deterministically.

Counts tests per category per capability from the test directory tree.
Produces a deterministic JSON artifact with no timestamps.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent / "tests"


CAPABILITY_MAP = {
    "account_management": {
        "unit": ["unit/engines/account", "unit/engines/account_engine"],
        "property": ["properties/behaviour"],
        "contract": [
            "contract/generated/test_accounts.py",
            "contract/generated/test_analytics.py",
        ],
        "capability": ["capability/account_management"],
    },
    "credit_cards": {
        "unit": ["unit/engines/credit_card"],
        "property": ["properties/credit_card_engine", "properties/credit_cards"],
        "contract": [
            "contract/generated/test_cards.py",
            "contract/generated/test_credit_cards.py",
        ],
        "capability": ["capability/credit_cards"],
    },
    "debt_management": {
        "unit": ["unit/engines/loan"],
        "property": ["properties/loan_engine", "properties/lending"],
        "contract": ["contract/generated/test_loans.py"],
        "capability": ["capability/debt_management"],
    },
    "financial_events": {
        "unit": ["unit/engines/financial_events"],
        "property": ["properties/financial_events"],
        "contract": ["contract/generated/test_financial_events.py"],
        "capability": ["capability/financial_events"],
    },
    "financial_health": {
        "unit": ["unit/engines/behavior", "unit/engines/behaviour"],
        "property": ["properties/behaviour"],
        "contract": ["contract/generated/test_behaviour.py"],
        "capability": ["capability/financial_health"],
    },
    "forecasting": {
        "unit": ["unit/engines/financial_intelligence"],
        "property": ["properties/forecasting"],
        "contract": [
            "contract/generated/test_forecast.py",
            "contract/generated/test_financial_events.py",
        ],
        "capability": ["capability/forecasting"],
    },
    "household_cashflow": {
        "unit": ["unit/engines/cashflow"],
        "property": ["properties/cashflow"],
        "contract": ["contract/generated/test_cashflow.py"],
        "capability": ["capability/household_cashflow"],
    },
    "pattern_analysis": {
        "unit": ["unit/engines/insight"],
        "property": ["unit/repositories"],
        "contract": [
            "contract/generated/test_transactions.py",
            "contract/generated/test_categories.py",
        ],
        "capability": ["capability/pattern_analysis"],
    },
    "recommendations": {
        "unit": ["unit/engines/recommendation"],
        "property": [],
        "contract": [
            "contract/generated/test_recommendations.py",
            "contract/generated/test_optimization.py",
        ],
        "capability": ["capability/recommendations"],
    },
    "reconciliation": {
        "unit": ["unit/engines/reconciliation"],
        "property": ["properties/reconciliation"],
        "contract": [
            "contract/generated/test_reconciliation.py",
            "contract/generated/test_reconciliations.py",
        ],
        "capability": ["capability/reconciliation"],
    },
    "transaction_intelligence": {
        "unit": ["unit/engines/transaction_intelligence"],
        "property": ["properties/credit_cards", "properties/transaction_intelligence"],
        "contract": ["contract/generated/test_transactions.py"],
        "capability": ["capability/transaction_intelligence"],
    },
}


def count_tests_in_file(path: Path) -> int:
    """Count test functions/methods in a Python file."""
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8", errors="ignore")
    # Match def test_ or class Test with methods
    len(re.findall(r"\n\s*def\s+test_\w+", text))
    len(re.findall(r"\n\s+def\s+test_\w+", text))
    # Total is sum of top-level defs + indented defs
    total = len(re.findall(r"\bdef\s+test_\w+\s*\(", text))
    return max(total, 1) if total > 0 else 0


def files_for_category(base: Path, subpaths: list[str]) -> list[Path]:
    """Resolve all .py files under the given subpaths."""
    files = []
    for sub in subpaths:
        p = base / sub
        if p.is_dir():
            files.extend(sorted(p.rglob("test_*.py")))
        elif p.suffix == ".py" and p.exists():
            files.append(p)
    return files


def content_hash(paths: list[Path]) -> str:
    """Deterministic hash from sorted file content concatenation."""
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(str(p).encode("utf-8"))
        if p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()[:16]


def main() -> None:
    dashboard = {}
    for capability, categories in CAPABILITY_MAP.items():
        unit_files = files_for_category(BASE_DIR, categories["unit"])
        property_files = files_for_category(BASE_DIR, categories["property"])
        contract_files = files_for_category(BASE_DIR, categories["contract"])
        capability_files = files_for_category(BASE_DIR, categories["capability"])

        unit_tests = sum(count_tests_in_file(f) for f in unit_files)
        property_tests = sum(count_tests_in_file(f) for f in property_files)
        contract_tests = sum(count_tests_in_file(f) for f in contract_files)
        capability_tests = sum(count_tests_in_file(f) for f in capability_files)

        # Coverage: percentage of 7 categories with at least 1 test file
        category_files = [unit_files, property_files, contract_files, capability_files]
        covered_categories = sum(1 for files in category_files if len(files) > 0)
        coverage = int((covered_categories / 4) * 100)

        # Determinism: uniform 100 (verified in ENGINE_FAILURE_BASELINE_REPORT.md)

        # Isolation: uniform 100 (verified in ENGINE_IMPLEMENTATION_REPORT.md)

        # Health
        if (
            coverage == 100
            and (unit_tests + property_tests + contract_tests + capability_tests) > 0
        ):
            health = "green"
        elif coverage >= 50:
            health = "yellow"
        else:
            health = "red"

        # Risk
        risk = "medium" if capability in ("financial_events", "credit_cards") else "low"

        validation_id = content_hash(
            unit_files + property_files + contract_files + capability_files
        )

        dashboard[capability] = {
            "health": health,
            "coverage": coverage,
            "property_tests": property_tests,
            "contracts": contract_tests,
            "capability_tests": capability_tests,
            "risk": risk,
            "last_validation": validation_id,
        }

    out_path = Path(__file__).resolve().parent / "CAPABILITY_HEALTH_DASHBOARD.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"Generated {out_path}")


if __name__ == "__main__":
    main()
