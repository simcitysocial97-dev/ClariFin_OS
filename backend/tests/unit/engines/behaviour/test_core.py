"""
Consolidated Behaviour Engine Core Tests
=========================================

Merges tests from:
- test_behaviour_engine_core.py  (utility functions, behavioral indices, profile, determinism, no-mutation, edge cases, India risk, insights, nudges)
- test_behaviour_engine_wellness.py  (wellness score, band classification, debt-dependent integration, edge cases, determinism)
- test_behaviour_engine_profile.py  (all 5 personality profiles, confidence, determinism, edge cases, priority)

All monetary values are integers in paise (₹1.00 = 100 paise).
"""

import hashlib
import json
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from engines.behaviour_engine import classify_financial_personality
from engines.behaviour_engine.core import (
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
    generate_behavioral_insights,
    generate_nudges,
    generate_summary_text,
    get_top_nudge,
)
from engines.behaviour_engine.wellness import (
    classify_wellness_band,
    compute_wellness_score,
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
# Utility Function Tests (from test_behaviour_engine_core.py)
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
# Behavioral Index Tests (from test_behaviour_engine_core.py)
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
# Main Profile Tests (from test_behaviour_engine_core.py)
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
# Determinism Tests (from test_behaviour_engine_core.py)
# ============================================================


class TestCoreDeterminism:
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
# No Mutation Tests (from test_behaviour_engine_core.py)
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
# Edge Case Tests (from test_behaviour_engine_core.py)
# ============================================================


class TestCoreEdgeCases:
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
# India-Specific Risk Tests (from test_behaviour_engine_core.py)
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
# Insight Generator Tests (from test_behaviour_engine_core.py)
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
# Nudge Engine Tests (from test_behaviour_engine_core.py)
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
# Wellness Score Calculation Tests (from test_behaviour_engine_wellness.py)
# ============================================================


class TestWellnessScoreCalculation:
    """Tests for compute_wellness_score function."""

    @pytest.fixture
    def perfect_scores(self) -> dict[str, Decimal | int]:
        """Fixture with perfect scores for all components."""
        return {
            "cashflow_stability": Decimal("1"),
            "debt_cycle_score": 0,  # Best possible debt score
            "savings_rate": Decimal("1"),  # 100% savings
            "resilience_index": Decimal("1"),
            "lifestyle_inflation": Decimal("-1"),  # Perfect lifestyle decrease
            "credit_revolver_ratio": Decimal("0"),  # No revolving credit
            "foir": Decimal("0"),  # No fixed obligations
        }

    @pytest.fixture
    def worst_scores(self) -> dict[str, Decimal | int]:
        """Fixture with worst scores for all components."""
        return {
            "cashflow_stability": Decimal("0"),
            "debt_cycle_score": 100,  # Worst possible debt score
            "savings_rate": Decimal("-1"),  # 100% overspending
            "resilience_index": Decimal("0"),
            "lifestyle_inflation": Decimal("2"),  # Extreme lifestyle inflation
            "credit_revolver_ratio": Decimal("1"),  # Always revolving
            "foir": Decimal("2"),  # Extreme fixed obligations
        }

    @pytest.fixture
    def average_scores(self) -> dict[str, Decimal | int]:
        """Fixture with average scores for all components."""
        return {
            "cashflow_stability": Decimal("0.5"),
            "debt_cycle_score": 50,
            "savings_rate": Decimal("0.2"),  # 20% savings
            "resilience_index": Decimal("0.5"),
            "lifestyle_inflation": Decimal("0.2"),  # 20% lifestyle inflation
            "credit_revolver_ratio": Decimal("0.3"),  # Some revolving
            "foir": Decimal("0.4"),  # Moderate fixed obligations
        }

    def test_perfect_wellness_score(self, perfect_scores):
        """Test perfect scores result in 100."""
        result = compute_wellness_score(**perfect_scores)
        assert result == Decimal("100")

    def test_worst_wellness_score(self, worst_scores):
        """Test worst scores result in 0."""
        result = compute_wellness_score(**worst_scores)
        assert result == Decimal("0")

    def test_average_wellness_score(self, average_scores):
        """Test average scores result in expected value."""
        result = compute_wellness_score(**average_scores)
        # Expected calculation:
        # Cashflow: 0.5 * 0.30 = 0.15
        # Debt: (1 - 0.5) * 0.20 = 0.10
        # Savings: 0.2 * 0.15 = 0.03
        # Resilience: 0.5 * 0.20 = 0.10
        # Lifestyle: (1 - 0.2) * 0.10 = 0.08
        # Credit: 0.5*(1-0.3) + 0.5*(1-0.4) = 0.35 + 0.3 = 0.65 * 0.05 = 0.0325
        # Total: 0.15 + 0.10 + 0.03 + 0.10 + 0.08 + 0.0325 = 0.4925
        expected = Decimal("0.4925") * Decimal("100")
        assert result == expected

    def test_negative_savings_rate(self):
        """Test negative savings rate is clamped to 0."""
        result = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=50,
            savings_rate=Decimal("-0.5"),  # Negative savings
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("0.2"),
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("0.4"),
        )
        # Should be same as if savings_rate=0
        expected = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=50,
            savings_rate=Decimal("0"),  # Clamped to 0
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("0.2"),
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("0.4"),
        )
        assert result == expected

    def test_high_lifestyle_inflation(self):
        """Test lifestyle inflation > 1 is capped at 1."""
        result = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=50,
            savings_rate=Decimal("0.2"),
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("2"),  # Extreme inflation
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("0.4"),
        )
        # Should be same as if lifestyle_inflation=1
        expected = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=50,
            savings_rate=Decimal("0.2"),
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("1"),  # Capped at 1
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("0.4"),
        )
        assert result == expected

    def test_high_foir(self):
        """Test FOIR > 1 is capped at 1."""
        result = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=50,
            savings_rate=Decimal("0.2"),
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("0.2"),
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("1.5"),  # Extreme FOIR
        )
        # Should be same as if foir=1
        expected = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=50,
            savings_rate=Decimal("0.2"),
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("0.2"),
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("1"),  # Capped at 1
        )
        assert result == expected

    def test_boundary_scores(self):
        """Test boundary score values."""
        # Test 0
        result = compute_wellness_score(
            cashflow_stability=Decimal("0"),
            debt_cycle_score=100,
            savings_rate=Decimal("-1"),
            resilience_index=Decimal("0"),
            lifestyle_inflation=Decimal("1"),
            credit_revolver_ratio=Decimal("1"),
            foir=Decimal("1"),
        )
        assert result == Decimal("0")

        # Test 100
        result = compute_wellness_score(
            cashflow_stability=Decimal("1"),
            debt_cycle_score=0,
            savings_rate=Decimal("1"),
            resilience_index=Decimal("1"),
            lifestyle_inflation=Decimal("-1"),
            credit_revolver_ratio=Decimal("0"),
            foir=Decimal("0"),
        )
        assert result == Decimal("100")

    def test_debt_health_inversion(self):
        """Test that lower debt cycle score results in higher wellness score."""
        # Low debt score (good)
        result_low_debt = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=20,  # Good debt score
            savings_rate=Decimal("0.2"),
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("0.2"),
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("0.4"),
        )

        # High debt score (bad)
        result_high_debt = compute_wellness_score(
            cashflow_stability=Decimal("0.5"),
            debt_cycle_score=80,  # Bad debt score
            savings_rate=Decimal("0.2"),
            resilience_index=Decimal("0.5"),
            lifestyle_inflation=Decimal("0.2"),
            credit_revolver_ratio=Decimal("0.3"),
            foir=Decimal("0.4"),
        )

        assert result_low_debt > result_high_debt

    def test_deterministic(self):
        """Test that same inputs produce same outputs."""
        inputs = {
            "cashflow_stability": Decimal("0.5"),
            "debt_cycle_score": 50,
            "savings_rate": Decimal("0.2"),
            "resilience_index": Decimal("0.5"),
            "lifestyle_inflation": Decimal("0.2"),
            "credit_revolver_ratio": Decimal("0.3"),
            "foir": Decimal("0.4"),
        }

        result1 = compute_wellness_score(**inputs)
        result2 = compute_wellness_score(**inputs)
        assert result1 == result2


# ============================================================
# Wellness Band Classification Tests (from test_behaviour_engine_wellness.py)
# ============================================================


class TestWellnessBandClassification:
    """Tests for classify_wellness_band function."""

    def test_excellent_band(self):
        """Test scores in excellent range (90-100)."""
        assert classify_wellness_band(Decimal("90")) == "Excellent"
        assert classify_wellness_band(Decimal("95")) == "Excellent"
        assert classify_wellness_band(Decimal("100")) == "Excellent"

    def test_healthy_band(self):
        """Test scores in healthy range (75-89)."""
        assert classify_wellness_band(Decimal("75")) == "Healthy"
        assert classify_wellness_band(Decimal("80")) == "Healthy"
        assert classify_wellness_band(Decimal("89.99")) == "Healthy"

    def test_developing_band(self):
        """Test scores in developing range (50-74)."""
        assert classify_wellness_band(Decimal("50")) == "Developing"
        assert classify_wellness_band(Decimal("60")) == "Developing"
        assert classify_wellness_band(Decimal("74.99")) == "Developing"

    def test_risk_band(self):
        """Test scores in risk range (25-49)."""
        assert classify_wellness_band(Decimal("25")) == "Risk"
        assert classify_wellness_band(Decimal("30")) == "Risk"
        assert classify_wellness_band(Decimal("49.99")) == "Risk"

    def test_critical_band(self):
        """Test scores in critical range (<25)."""
        assert classify_wellness_band(Decimal("0")) == "Critical"
        assert classify_wellness_band(Decimal("10")) == "Critical"
        assert classify_wellness_band(Decimal("24.99")) == "Critical"

    def test_boundary_values(self):
        """Test boundary values between bands."""
        assert classify_wellness_band(Decimal("89.999")) == "Healthy"
        assert classify_wellness_band(Decimal("90")) == "Excellent"

        assert classify_wellness_band(Decimal("74.999")) == "Developing"
        assert classify_wellness_band(Decimal("75")) == "Healthy"

        assert classify_wellness_band(Decimal("49.999")) == "Risk"
        assert classify_wellness_band(Decimal("50")) == "Developing"

        assert classify_wellness_band(Decimal("24.999")) == "Critical"
        assert classify_wellness_band(Decimal("25")) == "Risk"


# ============================================================
# Integration Tests with DEBT_DEPENDENT Profile (from test_behaviour_engine_wellness.py)
# ============================================================


class TestDebtDependentIntegration:
    """Test wellness score for DEBT_DEPENDENT profile characteristics."""

    def test_debt_dependent_profile(self):
        """Test wellness score for typical debt-dependent profile."""
        # Characteristics of DEBT_DEPENDENT:
        # - High credit revolver ratio
        # - High FOIR
        # - Low savings rate
        # - High debt cycle score
        result = compute_wellness_score(
            cashflow_stability=Decimal("0.3"),  # Unstable cashflow
            debt_cycle_score=80,  # High debt cycle score
            savings_rate=Decimal("-0.1"),  # Negative savings
            resilience_index=Decimal("0.2"),  # Low resilience
            lifestyle_inflation=Decimal("0.5"),  # High lifestyle inflation
            credit_revolver_ratio=Decimal("0.8"),  # High revolver ratio
            foir=Decimal("0.7"),  # High fixed obligations
        )

        # Should be in Risk or Critical band
        band = classify_wellness_band(result)
        assert band in ["Risk", "Critical"]
        assert result < Decimal("50")


# ============================================================
# Edge Cases and Boundary Conditions (from test_behaviour_engine_wellness.py)
# ============================================================


class TestWellnessEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_all_zero_inputs(self):
        """Test all zero inputs."""
        result = compute_wellness_score(
            cashflow_stability=Decimal("0"),
            debt_cycle_score=0,  # Best debt score
            savings_rate=Decimal("0"),
            resilience_index=Decimal("0"),
            lifestyle_inflation=Decimal("0"),
            credit_revolver_ratio=Decimal("0"),
            foir=Decimal("0"),
        )
        # Debug: print actual result
        print(f"Actual result: {result}")
        # Debt component: 20% of 1.0 = 0.20
        # Credit component: 0.5*(1-0) + 0.5*(1-0) = 1.0 * 0.05 = 0.05
        # Lifestyle component: (1 - 0) * 0.10 = 0.10
        # Total: 0.20 + 0.05 + 0.10 = 0.35 → 35
        expected = Decimal("35")
        assert result == expected

    def test_extreme_values(self):
        """Test with extreme values."""
        # Very high cashflow stability should not exceed 100
        result = compute_wellness_score(
            cashflow_stability=Decimal("1"),
            debt_cycle_score=0,
            savings_rate=Decimal("1"),
            resilience_index=Decimal("1"),
            lifestyle_inflation=Decimal("-1"),
            credit_revolver_ratio=Decimal("0"),
            foir=Decimal("0"),
        )
        assert result == Decimal("100")

        # Very low values should not go below 0
        result = compute_wellness_score(
            cashflow_stability=Decimal("0"),
            debt_cycle_score=100,
            savings_rate=Decimal("-1"),
            resilience_index=Decimal("0"),
            lifestyle_inflation=Decimal("2"),
            credit_revolver_ratio=Decimal("1"),
            foir=Decimal("2"),
        )
        assert result == Decimal("0")


# ============================================================
# Determinism Tests (from test_behaviour_engine_wellness.py)
# ============================================================


class TestWellnessDeterminism:
    """Verify all functions are deterministic."""

    def test_wellness_score_deterministic(self):
        """Test compute_wellness_score is deterministic."""
        inputs = {
            "cashflow_stability": Decimal("0.7"),
            "debt_cycle_score": 30,
            "savings_rate": Decimal("0.35"),
            "resilience_index": Decimal("0.6"),
            "lifestyle_inflation": Decimal("0.1"),
            "credit_revolver_ratio": Decimal("0.2"),
            "foir": Decimal("0.3"),
        }

        for _ in range(3):
            result1 = compute_wellness_score(**inputs)
            result2 = compute_wellness_score(**inputs)
            assert result1 == result2

    def test_classify_wellness_band_deterministic(self):
        """Test classify_wellness_band is deterministic."""
        score = Decimal("65.4321")
        for _ in range(3):
            result1 = classify_wellness_band(score)
            result2 = classify_wellness_band(score)
            assert result1 == result2


# ============================================================
# SAVER Tests (from test_behaviour_engine_profile.py)
# ============================================================


class TestSaverProfile:
    """Tests for SAVER personality classification."""

    def test_saver_high_savings_no_debt(self):
        """Test SAVER with high savings and no credit dependency."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.25'),  # 25% savings
            borrowed_lifestyle_ratio=Decimal('0.05'),  # 5% credit funded
            credit_revolver_ratio=Decimal('0.0'),  # No revolving debt
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.05'),
            transaction_count=150,
        )
        assert profile == "SAVER"
        assert 0 <= confidence <= 1
        assert "SAVER" in explanation
        assert "25%" in explanation or "savings rate" in explanation.lower()

    def test_saver_strong_savings(self):
        """Test SAVER with strong savings (>25%) gets higher confidence."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0.35'),  # 35% savings - strong
            borrowed_lifestyle_ratio=Decimal('0.0'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.10'),
            impulse_transaction_ratio=Decimal('0.05'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=200,
        )
        assert profile == "SAVER"
        # Strong savings should get confidence bonus
        assert confidence >= Decimal('0.6')

    def test_saver_threshold_boundary(self):
        """Test SAVER at just above 20% threshold."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0.21'),  # Just above 20%
            borrowed_lifestyle_ratio=Decimal('0.0'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.10'),
            impulse_transaction_ratio=Decimal('0.05'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=100,
        )
        assert profile == "SAVER"

    def test_saver_not_if_high_borrowed_ratio(self):
        """Test SAVER is not assigned when borrowed lifestyle ratio is high."""
        profile, _, _ = classify_financial_personality(
            savings_rate=Decimal('0.25'),
            borrowed_lifestyle_ratio=Decimal('0.30'),  # Too high
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.10'),
            impulse_transaction_ratio=Decimal('0.05'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=100,
        )
        assert profile == "DEBT_DEPENDENT"


# ============================================================
# DEBT_DEPENDENT Tests (from test_behaviour_engine_profile.py)
# ============================================================


class TestDebtDependentProfile:
    """Tests for DEBT_DEPENDENT personality classification."""

    def test_debt_dependent_high_borrowed_ratio(self):
        """Test DEBT_DEPENDENT with high borrowed lifestyle ratio."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.10'),
            borrowed_lifestyle_ratio=Decimal('0.25'),  # >20% threshold
            credit_revolver_ratio=Decimal('0.30'),
            discretionary_spending_ratio=Decimal('0.40'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.20'),
            transaction_count=100,
        )
        assert profile == "DEBT_DEPENDENT"
        assert "borrowed lifestyle" in explanation.lower() or "credit" in explanation.lower()

    def test_debt_dependent_recurring_extraction(self):
        """Test DEBT_DEPENDENT from high revolver + low savings."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.05'),  # Low savings
            borrowed_lifestyle_ratio=Decimal('0.10'),  # Below threshold
            credit_revolver_ratio=Decimal('0.60'),  # High revolver
            discretionary_spending_ratio=Decimal('0.30'),
            impulse_transaction_ratio=Decimal('0.20'),
            lifestyle_creep_index=Decimal('0.10'),
            transaction_count=100,
        )
        assert profile == "DEBT_DEPENDENT"

    def test_debt_dependent_high_confidence(self):
        """Test DEBT_DEPENDENT gets high confidence with clear signals."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0.0'),  # Negative/near-zero
            borrowed_lifestyle_ratio=Decimal('0.40'),  # Very high
            credit_revolver_ratio=Decimal('0.70'),
            discretionary_spending_ratio=Decimal('0.50'),
            impulse_transaction_ratio=Decimal('0.30'),
            lifestyle_creep_index=Decimal('0.30'),
            transaction_count=250,
        )
        assert profile == "DEBT_DEPENDENT"
        assert confidence >= Decimal('0.7')


# ============================================================
# DEBT_OPTIMIZER Tests (from test_behaviour_engine_profile.py)
# ============================================================


class TestDebtOptimizerProfile:
    """Tests for DEBT_OPTIMIZER personality classification."""

    def test_debt_optimizer_responsible_usage(self):
        """Test DEBT_OPTIMIZER with responsible credit usage."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.15'),
            borrowed_lifestyle_ratio=Decimal('0.10'),  # Low credit dependency
            credit_revolver_ratio=Decimal('0.10'),  # Low revolver, pays in full
            discretionary_spending_ratio=Decimal('0.25'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.05'),
            transaction_count=120,
        )
        assert profile == "DEBT_OPTIMIZER"
        assert "responsibly" in explanation.lower() or "credit" in explanation.lower()

    def test_debt_optimizer_confidence(self):
        """Test DEBT_OPTIMIZER gets moderate confidence."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0.12'),
            borrowed_lifestyle_ratio=Decimal('0.08'),
            credit_revolver_ratio=Decimal('0.05'),
            discretionary_spending_ratio=Decimal('0.30'),
            impulse_transaction_ratio=Decimal('0.05'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=100,
        )
        assert profile == "DEBT_OPTIMIZER"
        assert Decimal('0.5') <= confidence <= Decimal('0.7')

    def test_debt_optimizer_not_if_no_credit(self):
        """Test DEBT_OPTIMIZER requires some credit usage."""
        profile, _, _ = classify_financial_personality(
            savings_rate=Decimal('0.15'),
            borrowed_lifestyle_ratio=Decimal('0.0'),
            credit_revolver_ratio=Decimal('0.0'),  # No credit usage
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.05'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=100,
        )
        # Should be BALANCED since savings < 20% and no credit usage
        assert profile == "BALANCED"


# ============================================================
# SPENDER Tests (from test_behaviour_engine_profile.py)
# ============================================================


class TestSpenderProfile:
    """Tests for SPENDER personality classification."""

    def test_spender_high_discretionary(self):
        """Test SPENDER with high discretionary spending."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.05'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.0'),  # No credit usage to avoid DEBT_OPTIMIZER
            discretionary_spending_ratio=Decimal('0.50'),  # High discretionary
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.10'),
            transaction_count=100,
        )
        assert profile == "SPENDER"
        assert "SPENDER" in explanation

    def test_spender_high_impulse(self):
        """Test SPENDER with high impulse transaction ratio."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.05'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.0'),  # No credit usage to avoid DEBT_OPTIMIZER
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.40'),  # High impulse
            lifestyle_creep_index=Decimal('0.10'),
            transaction_count=100,
        )
        assert profile == "SPENDER"
        assert "impulse" in explanation.lower() or "discretionary" in explanation.lower()

    def test_spender_high_lifestyle_creep(self):
        """Test SPENDER with high lifestyle creep index."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.05'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.0'),  # No credit usage to avoid DEBT_OPTIMIZER
            discretionary_spending_ratio=Decimal('0.15'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.60'),  # High creep (>50%)
            transaction_count=100,
        )
        assert profile == "SPENDER"


# ============================================================
# BALANCED Tests (from test_behaviour_engine_profile.py)
# ============================================================


class TestBalancedProfile:
    """Tests for BALANCED personality classification."""

    def test_balanced_moderate_values(self):
        """Test BALANCED with moderate savings and low extremes."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.12'),  # Moderate savings
            borrowed_lifestyle_ratio=Decimal('0.10'),  # Low credit dependency
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.25'),  # Moderate discretionary
            impulse_transaction_ratio=Decimal('0.15'),
            lifestyle_creep_index=Decimal('0.10'),
            transaction_count=100,
        )
        assert profile == "BALANCED"
        assert "BALANCED" in explanation

    def test_balanced_default_fallback(self):
        """Test BALANCED is the default when no clear pattern."""
        profile, confidence, explanation = classify_financial_personality(
            savings_rate=Decimal('0.15'),
            borrowed_lifestyle_ratio=Decimal('0.05'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=50,
        )
        assert profile == "BALANCED"

    def test_balanced_explanation_content(self):
        """Test BALANCED explanation contains key metrics."""
        profile, _, explanation = classify_financial_personality(
            savings_rate=Decimal('0.15'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.0'),  # No credit usage
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=100,
        )
        assert "15.0" in explanation
        assert "10.0" in explanation


# ============================================================
# Confidence Tests (from test_behaviour_engine_profile.py)
# ============================================================


class TestConfidenceCalculation:
    """Tests for confidence score calculation."""

    def test_confidence_bounds(self):
        """Test confidence is always between 0 and 1."""
        for _ in range(10):
            profile, confidence, _ = classify_financial_personality(
                savings_rate=Decimal('0.15'),
                borrowed_lifestyle_ratio=Decimal('0.10'),
                credit_revolver_ratio=Decimal('0.10'),
                discretionary_spending_ratio=Decimal('0.20'),
                impulse_transaction_ratio=Decimal('0.10'),
                lifestyle_creep_index=Decimal('0.05'),
                transaction_count=100,
            )
            assert Decimal('0') <= confidence <= Decimal('1')

    def test_confidence_increases_with_volume(self):
        """Test confidence increases with more transactions."""
        profile1, confidence1, _ = classify_financial_personality(
            savings_rate=Decimal('0.10'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=50,
        )
        profile2, confidence2, _ = classify_financial_personality(
            savings_rate=Decimal('0.10'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=400,
        )
        assert confidence2 > confidence1

    def test_confidence_saver_strong(self):
        """Test SAVER gets confidence bonus for strong savings."""
        _, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0.30'),  # Strong
            borrowed_lifestyle_ratio=Decimal('0.0'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.10'),
            impulse_transaction_ratio=Decimal('0.0'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=100,
        )
        assert confidence >= Decimal('0.6')


# ============================================================
# Determinism Tests (from test_behaviour_engine_profile.py)
# ============================================================


class TestProfileDeterminism:
    """Tests for deterministic behavior."""

    def test_same_input_same_output(self):
        """Test that same inputs produce same outputs."""
        inputs = {
            "savings_rate": Decimal('0.25'),
            "borrowed_lifestyle_ratio": Decimal('0.05'),
            "credit_revolver_ratio": Decimal('0.0'),
            "discretionary_spending_ratio": Decimal('0.20'),
            "impulse_transaction_ratio": Decimal('0.10'),
            "lifestyle_creep_index": Decimal('0.05'),
            "transaction_count": 150,
        }

        result1 = classify_financial_personality(**inputs)
        result2 = classify_financial_personality(**inputs)

        assert result1 == result2
        assert result1[0] == result2[0]  # Profile
        assert result1[1] == result2[1]  # Confidence
        assert result1[2] == result2[2]  # Explanation

    def test_deterministic_all_profiles(self):
        """Test determinism across all profile types."""
        test_cases = [
            ("SAVER", Decimal('0.25'), Decimal('0.0'), Decimal('0.0')),
            ("DEBT_DEPENDENT", Decimal('0.10'), Decimal('0.30'), Decimal('0.60')),
            ("DEBT_OPTIMIZER", Decimal('0.12'), Decimal('0.08'), Decimal('0.10')),
            ("SPENDER", Decimal('0.05'), Decimal('0.10'), Decimal('0.0')),  # No credit for SPENDER
            ("BALANCED", Decimal('0.15'), Decimal('0.05'), Decimal('0.0')),
        ]

        for expected_profile, savings, borrowed, revolver in test_cases:
            # Use discretionary values that only trigger SPENDER for SPENDER case
            disc = Decimal('0.50') if expected_profile == "SPENDER" else Decimal('0.25')
            impulse = Decimal('0.40') if expected_profile == "SPENDER" else Decimal('0.10')
            creep = Decimal('0.60') if expected_profile == "SPENDER" else Decimal('0.10')

            result1 = classify_financial_personality(
                savings_rate=savings,
                borrowed_lifestyle_ratio=borrowed,
                credit_revolver_ratio=revolver,
                discretionary_spending_ratio=disc,
                impulse_transaction_ratio=impulse,
                lifestyle_creep_index=creep,
                transaction_count=100,
            )
            result2 = classify_financial_personality(
                savings_rate=savings,
                borrowed_lifestyle_ratio=borrowed,
                credit_revolver_ratio=revolver,
                discretionary_spending_ratio=disc,
                impulse_transaction_ratio=impulse,
                lifestyle_creep_index=creep,
                transaction_count=100,
            )
            assert result1[0] == expected_profile
            assert result1 == result2


# ============================================================
# Edge Cases Tests (from test_behaviour_engine_profile.py)
# ============================================================


class TestProfileEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_savings_rate(self):
        """Test with zero savings rate."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0'),
            borrowed_lifestyle_ratio=Decimal('0.0'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=50,
        )
        assert profile == "BALANCED"

    def test_zero_transaction_count(self):
        """Test with zero transactions."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0.15'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=0,
        )
        # Should still return a valid profile
        assert profile in ("BALANCED", "SAVER")

    def test_negative_savings_rate(self):
        """Test with negative savings rate (overspending)."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('-0.10'),
            borrowed_lifestyle_ratio=Decimal('0.10'),
            credit_revolver_ratio=Decimal('0.30'),
            discretionary_spending_ratio=Decimal('0.40'),
            impulse_transaction_ratio=Decimal('0.20'),
            lifestyle_creep_index=Decimal('0.10'),
            transaction_count=100,
        )
        # Should be SPENDER or DEBT_DEPENDENT
        assert profile in ("SPENDER", "DEBT_DEPENDENT")

    def test_very_high_values(self):
        """Test with very high metric values."""
        profile, confidence, _ = classify_financial_personality(
            savings_rate=Decimal('0.90'),
            borrowed_lifestyle_ratio=Decimal('0.0'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.0'),
            impulse_transaction_ratio=Decimal('0.0'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=500,
        )
        assert profile == "SAVER"
        assert confidence >= Decimal('0.8')


# ============================================================
# Priority Tests (from test_behaviour_engine_profile.py)
# ============================================================


class TestProfilePriority:
    """Tests to verify classification priority order."""

    def test_debt_dependent_takes_priority_over_saver(self):
        """DEBT_DEPENDENT should be detected before SAVER."""
        profile, _, _ = classify_financial_personality(
            savings_rate=Decimal('0.25'),  # Would qualify for SAVER
            borrowed_lifestyle_ratio=Decimal('0.25'),  # But DEBT_DEPENDENT takes priority
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.20'),
            impulse_transaction_ratio=Decimal('0.10'),
            lifestyle_creep_index=Decimal('0.0'),
            transaction_count=100,
        )
        assert profile == "DEBT_DEPENDENT"

    def test_saver_takes_priority_over_spender(self):
        """SAVER should be detected before SPENDER."""
        profile, _, _ = classify_financial_personality(
            savings_rate=Decimal('0.25'),  # SAVER qualifies
            borrowed_lifestyle_ratio=Decimal('0.05'),
            credit_revolver_ratio=Decimal('0.0'),
            discretionary_spending_ratio=Decimal('0.45'),  # SPENDER would also qualify
            impulse_transaction_ratio=Decimal('0.35'),
            lifestyle_creep_index=Decimal('0.60'),
            transaction_count=100,
        )
        assert profile == "SAVER"


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
