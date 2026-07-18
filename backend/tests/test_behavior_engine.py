"""
Test Suite for Behavior Engine
===============================

Validates:
- Deterministic outputs
- Scores always between 0 and 1
- Health score between 0 and 100
- No DB mutation
- Same dataset → same result

Phase 3: Advanced Behavioral Intelligence Layer
"""

import hashlib
import json
import os
import sqlite3

# Add parent directory to path
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.behavior_engine import (
    _coefficient_of_variation,
    _compute_financial_stress_index,
    _compute_habit_stability_score,
    _compute_impulsivity_score,
    _compute_loss_aversion_index,
    _compute_savings_discipline_score,
    _moving_average,
    _normalize_score,
    compute_behavior_profile,
    detect_india_risk_patterns,
)
from engines.insight_generator import (
    generate_behavioral_insights,
    generate_summary_text,
)
from engines.nudge_engine import (
    generate_nudges,
    get_top_nudge,
)

# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture
def temp_db():
    """Create a temporary database with test transactions (in paise)."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Create tables with canonical schema (amount_paise as INTEGER)
    cur.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            statement_id INTEGER,
            date TEXT,
            date_iso TEXT,
            description TEXT,
            amount_paise INTEGER,
            type TEXT,
            category TEXT,
            subcategory TEXT,
            member TEXT,
            account_id TEXT,
            debit INTEGER,
            credit INTEGER,
            balance INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Generate 90 days of test transactions
    base_date = datetime.now() - timedelta(days=90)

    transactions = []
    txn_id = 1

    for day in range(90):
        date = base_date + timedelta(days=day)
        date_iso = date.strftime("%Y-%m-%d")

        # Daily expenses (groceries, food) - values in paise
        if day % 2 == 0:
            transactions.append((
                txn_id, 1, date_iso, date_iso, "GROCERY STORE", 50000, "debit",
                "Groceries", None, "Self", "ACC001", 50000, None, None
            ))
            txn_id += 1

        if day % 3 == 0:
            transactions.append((
                txn_id, 1, date_iso, date_iso, "RESTAURANT", 80000, "debit",
                "Food & Dining", None, "Self", "ACC001", 80000, None, None
            ))
            txn_id += 1

        # Monthly salary (1st of each month) - in paise
        if date.day == 1:
            transactions.append((
                txn_id, 1, date_iso, date_iso, "SALARY CREDIT", 5000000, "credit",
                "Income", None, "Self", "ACC001", None, 5000000, None
            ))
            txn_id += 1

        # Monthly EMI (5th of each month) - in paise
        if date.day == 5:
            transactions.append((
                txn_id, 1, date_iso, date_iso, "EMI LOAN REPAYMENT", 1500000, "debit",
                "EMI", None, "Self", "ACC001", 1500000, None, None
            ))
            txn_id += 1

        # Micro transactions (UPI) - in paise
        if day % 1 == 0:
            transactions.append((
                txn_id, 1, date_iso, date_iso, "UPI-PAYMENT", 15000, "debit",
                "Food & Dining", None, "Self", "ACC001", 15000, None, None
            ))
            txn_id += 1

    cur.executemany("""
        INSERT INTO transactions (
            id, statement_id, date, date_iso, description, amount_paise, type,
            category, subcategory, member, account_id, debit, credit, balance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, transactions)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def minimal_db():
    """Create a minimal database with few transactions (in paise)."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            statement_id INTEGER,
            date TEXT,
            date_iso TEXT,
            description TEXT,
            amount_paise INTEGER,
            type TEXT,
            category TEXT,
            subcategory TEXT,
            member TEXT,
            account_id TEXT,
            debit INTEGER,
            credit INTEGER,
            balance INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Just 5 transactions (in paise)
    transactions = [
        (1, 1, "2025-01-01", "2025-01-01", "TEST DEBIT", 10000, "debit", "Test", None, "Self", "ACC001", 10000, None, None),
        (2, 1, "2025-01-02", "2025-01-02", "TEST DEBIT", 20000, "debit", "Test", None, "Self", "ACC001", 20000, None, None),
        (3, 1, "2025-01-03", "2025-01-03", "TEST CREDIT", 100000, "credit", "Income", None, "Self", "ACC001", None, 100000, None),
        (4, 1, "2025-01-04", "2025-01-04", "TEST DEBIT", 15000, "debit", "Test", None, "Self", "ACC001", 15000, None, None),
        (5, 1, "2025-01-05", "2025-01-05", "TEST DEBIT", 30000, "debit", "Test", None, "Self", "ACC001", 30000, None, None),
    ]

    cur.executemany("""
        INSERT INTO transactions (
            id, statement_id, date, date_iso, description, amount_paise, type,
            category, subcategory, member, account_id, debit, credit, balance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, transactions)

    conn.commit()
    conn.close()

    yield db_path

    os.unlink(db_path)


# ============================================================
# Utility Function Tests
# ============================================================

class TestUtilityFunctions:
    """Test utility functions."""

    def test_normalize_score_within_range(self):
        """Test that normalize_score always returns 0-1."""
        assert 0 <= _normalize_score(0.5, 0, 1) <= 1
        assert 0 <= _normalize_score(0.5, 0, 2) <= 1
        assert 0 <= _normalize_score(1.5, 0, 1) <= 1

    def test_normalize_score_clamping(self):
        """Test that values are clamped to 0-1."""
        assert _normalize_score(-1, 0, 1) == 0.0
        assert _normalize_score(2, 0, 1) == 1.0

    def test_normalize_score_edge_cases(self):
        """Test edge cases."""
        assert _normalize_score(5, 5, 5) == 0.5

    def test_coefficient_of_variation_empty(self):
        """Test CV with empty list."""
        assert _coefficient_of_variation([]) == 0.0
        assert _coefficient_of_variation([1]) == 0.0

    def test_coefficient_of_variation_normal(self):
        """Test CV with normal data."""
        assert _coefficient_of_variation([5, 5, 5, 5]) == 0.0
        cv = _coefficient_of_variation([1, 2, 3, 4, 5])
        assert cv > 0

    def test_moving_average(self):
        """Test moving average calculation."""
        values = [1, 2, 3, 4, 5]
        ma = _moving_average(values, 3)
        assert len(ma) == len(values)
        assert ma[0] == 1.0
        assert ma[2] == 2.0

    def test_moving_average_empty(self):
        """Test moving average with empty list."""
        assert _moving_average([], 3) == []


# ============================================================
# Behavioral Index Tests
# ============================================================

class TestBehavioralIndices:
    """Test individual behavioral index calculations."""

    def test_loss_aversion_index_bounds(self):
        """Test that loss aversion score is between 0 and 1."""
        transactions = [
            {"type": "credit", "amount": 10000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount": 500, "date_iso": "2025-01-02"},
        ]
        result = _compute_loss_aversion_index(transactions)
        assert 0 <= result["score"] <= 1

    def test_impulsivity_score_bounds(self):
        """Test that impulsivity score is between 0 and 1."""
        transactions = [
            {"type": "debit", "amount": 100, "date_iso": "2025-01-01", "category": "Food"},
            {"type": "debit", "amount": 200, "date_iso": "2025-01-02", "category": "Shopping"},
        ]
        result = _compute_impulsivity_score(transactions)
        assert 0 <= result["score"] <= 1

    def test_habit_stability_score_bounds(self):
        """Test that habit stability score is between 0 and 1."""
        transactions = [
            {"type": "debit", "amount": 500, "date_iso": "2025-01-01", "category": "Groceries"},
            {"type": "debit", "amount": 500, "date_iso": "2025-02-01", "category": "Groceries"},
        ]
        result = _compute_habit_stability_score(transactions)
        assert 0 <= result["score"] <= 1

    def test_financial_stress_index_bounds(self):
        """Test that financial stress score is between 0 and 1."""
        transactions = [
            {"type": "credit", "amount": 10000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount": 5000, "date_iso": "2025-01-02"},
        ]
        result = _compute_financial_stress_index(transactions)
        assert 0 <= result["score"] <= 1

    def test_savings_discipline_score_bounds(self):
        """Test that savings discipline score is between 0 and 1."""
        transactions = [
            {"type": "credit", "amount": 10000, "date_iso": "2025-01-01"},
            {"type": "debit", "amount": 8000, "date_iso": "2025-01-02"},
        ]
        result = _compute_savings_discipline_score(transactions)
        assert 0 <= result["score"] <= 1


# ============================================================
# Main Profile Tests
# ============================================================

class TestBehaviorProfile:
    """Test main behavior profile computation."""

    def test_profile_structure(self, temp_db):
        """Test that profile has correct structure."""
        profile = compute_behavior_profile(temp_db)
        assert "temporal_patterns" in profile
        assert "behavioral_indices" in profile
        assert "risk_signals" in profile
        assert "confidence" in profile
        assert "financial_health_score" in profile

    def test_health_score_bounds(self, temp_db):
        """Test that health score is between 0 and 100."""
        profile = compute_behavior_profile(temp_db)
        assert 0 <= profile["financial_health_score"] <= 100

    def test_confidence_bounds(self, temp_db):
        """Test that confidence is between 0 and 1."""
        profile = compute_behavior_profile(temp_db)
        assert 0 <= profile["confidence"] <= 1

    def test_all_indices_present(self, temp_db):
        """Test that all behavioral indices are present."""
        profile = compute_behavior_profile(temp_db)
        indices = profile["behavioral_indices"]
        assert "loss_aversion" in indices
        assert "impulsivity" in indices
        assert "habit_stability" in indices
        assert "financial_stress" in indices
        assert "savings_discipline" in indices

    def test_all_indices_have_scores(self, temp_db):
        """Test that all indices have score field."""
        profile = compute_behavior_profile(temp_db)
        indices = profile["behavioral_indices"]
        for name, index in indices.items():
            assert "score" in index, f"{name} missing score"
            assert 0 <= index["score"] <= 1, f"{name} score out of bounds"


# ============================================================
# Determinism Tests
# ============================================================

class TestDeterminism:
    """Test that outputs are deterministic."""

    def test_same_input_same_output(self, temp_db):
        """Test that same input produces same output."""
        profile1 = compute_behavior_profile(temp_db)
        profile2 = compute_behavior_profile(temp_db)
        assert json.dumps(profile1, sort_keys=True) == json.dumps(profile2, sort_keys=True)

    def test_determinism_hash(self, temp_db):
        """Test determinism using hash comparison."""
        profile1 = compute_behavior_profile(temp_db)
        profile2 = compute_behavior_profile(temp_db)
        hash1 = hashlib.md5(json.dumps(profile1, sort_keys=True).encode()).hexdigest()
        hash2 = hashlib.md5(json.dumps(profile2, sort_keys=True).encode()).hexdigest()
        assert hash1 == hash2

    def test_insights_determinism(self, temp_db):
        """Test that insights are deterministic."""
        profile = compute_behavior_profile(temp_db)
        insights1 = generate_behavioral_insights(profile)
        insights2 = generate_behavioral_insights(profile)
        assert insights1 == insights2

    def test_nudges_determinism(self, temp_db):
        """Test that nudges are deterministic."""
        profile = compute_behavior_profile(temp_db)
        nudges1 = generate_nudges(profile)
        nudges2 = generate_nudges(profile)
        assert nudges1 == nudges2


# ============================================================
# No Mutation Tests
# ============================================================

class TestNoMutation:
    """Test that behavior engine doesn't mutate database."""

    def test_no_new_tables(self, temp_db):
        """Test that no new tables are created."""
        conn = sqlite3.connect(temp_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables_before = {row[0] for row in cur.fetchall()}
        conn.close()
        compute_behavior_profile(temp_db)
        conn = sqlite3.connect(temp_db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables_after = {row[0] for row in cur.fetchall()}
        conn.close()
        assert tables_before == tables_after

    def test_no_new_rows(self, temp_db):
        """Test that no new rows are added."""
        conn = sqlite3.connect(temp_db)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM transactions")
        count_before = cur.fetchone()[0]
        conn.close()
        compute_behavior_profile(temp_db)
        conn = sqlite3.connect(temp_db)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM transactions")
        count_after = cur.fetchone()[0]
        conn.close()
        assert count_before == count_after


# ============================================================
# Edge Case Tests
# ============================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_database(self):
        """Test with empty database (in paise)."""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                date TEXT,
                date_iso TEXT,
                description TEXT,
                amount_paise INTEGER,
                type TEXT,
                category TEXT,
                debit INTEGER DEFAULT 0,
                credit INTEGER DEFAULT 0,
                account_id TEXT
            )
        """)
        conn.commit()
        conn.close()
        try:
            profile = compute_behavior_profile(db_path)
            assert "financial_health_score" in profile
            assert 0 <= profile["financial_health_score"] <= 100
            assert profile["confidence"] >= 0
        finally:
            os.unlink(db_path)

    def test_minimal_data(self, minimal_db):
        """Test with minimal transaction data."""
        profile = compute_behavior_profile(minimal_db)
        assert "financial_health_score" in profile
        assert 0 <= profile["financial_health_score"] <= 100

    def test_all_credits(self):
        """Test with only credit transactions (in paise)."""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                date TEXT,
                date_iso TEXT,
                description TEXT,
                amount_paise INTEGER,
                type TEXT,
                category TEXT,
                debit INTEGER DEFAULT 0,
                credit INTEGER DEFAULT 0,
                account_id TEXT
            )
        """)
        cur.execute("""
            INSERT INTO transactions (date, date_iso, description, amount_paise, type, category, debit, credit, account_id)
            VALUES ('2025-01-01', '2025-01-01', 'INCOME', 1000000, 'credit', 'Income', 0, 1000000, 'ACC001')
        """)
        conn.commit()
        conn.close()
        try:
            profile = compute_behavior_profile(db_path)
            assert 0 <= profile["financial_health_score"] <= 100
        finally:
            os.unlink(db_path)

    def test_all_debits(self):
        """Test with only debit transactions (in paise)."""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                date TEXT,
                date_iso TEXT,
                description TEXT,
                amount_paise INTEGER,
                type TEXT,
                category TEXT,
                debit INTEGER DEFAULT 0,
                credit INTEGER DEFAULT 0,
                account_id TEXT
            )
        """)
        for i in range(10):
            cur.execute("""
                INSERT INTO transactions (date, date_iso, description, amount_paise, type, category, debit, credit, account_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"2025-01-{i+1:02d}", f"2025-01-{i+1:02d}", "EXPENSE", 100000, "debit", "Test", 100000, 0, "ACC001"))
        conn.commit()
        conn.close()
        try:
            profile = compute_behavior_profile(db_path)
            assert 0 <= profile["financial_health_score"] <= 100
        finally:
            os.unlink(db_path)


# ============================================================
# India-Specific Risk Tests
# ============================================================

class TestIndiaRiskPatterns:
    """Test India-specific risk detection."""

    def test_gambling_detection(self):
        """Test gambling transaction detection."""
        transactions = [
            {"type": "debit", "description": "DREAM11 CRICKET", "amount": 500, "date_iso": "2025-01-01"},
            {"type": "debit", "description": "MPL GAMING", "amount": 300, "date_iso": "2025-01-02"},
        ]
        result = detect_india_risk_patterns(transactions)
        assert result["gambling_flag"]
        assert result["gambling_transaction_count"] == 2

    def test_upi_micro_spend_detection(self):
        """Test UPI micro-spend clustering detection."""
        transactions = [{"type": "debit", "description": "UPI PAYMENT", "amount": 100, "date_iso": "2025-01-01"} for i in range(15)]
        result = detect_india_risk_patterns(transactions)
        assert result["upi_micro_spend_flag"]

    def test_loan_app_detection(self):
        """Test loan app pattern detection."""
        transactions = [
            {"type": "credit", "description": "LOAN CREDIT NBFC", "amount": 5000, "date_iso": "2025-01-01"},
            {"type": "credit", "description": "INSTANT LOAN", "amount": 3000, "date_iso": "2025-01-05"},
        ]
        result = detect_india_risk_patterns(transactions)
        assert result["loan_app_pattern_flag"]

    def test_emi_ratio_calculation(self):
        """Test EMI ratio calculation."""
        transactions = [
            {"type": "credit", "description": "SALARY", "amount": 50000, "date_iso": "2025-01-01"},
            {"type": "debit", "description": "EMI LOAN", "amount": 15000, "date_iso": "2025-01-05"},
        ]
        result = detect_india_risk_patterns(transactions)
        assert 0 <= result["emi_ratio"] <= 1


# ============================================================
# Insight Generator Tests
# ============================================================

class TestInsightGenerator:
    """Test insight generation."""

    def test_insights_structure(self, temp_db):
        """Test that insights have correct structure."""
        profile = compute_behavior_profile(temp_db)
        insights = generate_behavioral_insights(profile)
        for insight in insights:
            assert "type" in insight
            assert "title" in insight
            assert "message" in insight
            assert insight["type"] in ["warning", "positive", "info"]

    def test_summary_text(self, temp_db):
        """Test summary text generation."""
        profile = compute_behavior_profile(temp_db)
        summary = generate_summary_text(profile)
        assert isinstance(summary, str)
        assert len(summary) > 0


# ============================================================
# Nudge Engine Tests
# ============================================================

class TestNudgeEngine:
    """Test nudge generation."""

    def test_nudges_structure(self, temp_db):
        """Test that nudges have correct structure."""
        profile = compute_behavior_profile(temp_db)
        nudges = generate_nudges(profile)
        for nudge in nudges:
            assert "type" in nudge
            assert "priority" in nudge
            assert "title" in nudge
            assert "message" in nudge
            assert nudge["type"] in ["habit", "friction", "goal", "awareness"]
            assert 1 <= nudge["priority"] <= 3

    def test_nudges_sorted_by_priority(self, temp_db):
        """Test that nudges are sorted by priority."""
        profile = compute_behavior_profile(temp_db)
        nudges = generate_nudges(profile)
        priorities = [n["priority"] for n in nudges]
        assert priorities == sorted(priorities)

    def test_top_nudge(self, temp_db):
        """Test getting top nudge."""
        profile = compute_behavior_profile(temp_db)
        top = get_top_nudge(profile)
        assert "title" in top
        assert "message" in top


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
