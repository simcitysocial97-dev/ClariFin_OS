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

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
import hashlib
import json

# Add parent directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import FinanceDB
from engines.behavior_engine import (
    compute_behavior_profile,
    detect_india_risk_patterns,
    _normalize_score,
    _coefficient_of_variation,
    _moving_average,
    _compute_temporal_patterns,
    _compute_loss_aversion_index,
    _compute_impulsivity_score,
    _compute_habit_stability_score,
    _compute_financial_stress_index,
    _compute_savings_discipline_score,
)
from engines.insight_generator import (
    generate_behavioral_insights,
    generate_summary_text,
)
from engines.nudge_engine import (
    generate_nudges,
    get_top_nudge,
    get_nudge_summary,
)


# ============================================================
# Test Fixtures
# ============================================================

@pytest.fixture
def temp_db():
    """Create a temporary database with test transactions."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Create FinanceDB instance (tables are created automatically)
    db = FinanceDB(db_path)
    
    # Create a statement record
    with db.transaction() as conn:
        cur = conn.execute(
            "INSERT INTO statements (bank, file_name) VALUES (?, ?)",
            ("TestBank", "test_statement.pdf")
        )
        statement_id = cur.lastrowid
    
    # Generate 90 days of test transactions
    base_date = datetime.now() - timedelta(days=90)
    
    transactions = []
    txn_id = 1
    
    for day in range(90):
        date = base_date + timedelta(days=day)
        date_iso = date.strftime("%Y-%m-%d")
        
        # Daily expenses (groceries, food)
        if day % 2 == 0:
            transactions.append({
                "date": date_iso,
                "description": "GROCERY STORE",
                "amount": 500.0,
                "type": "debit",
                "category": "Groceries",
            })
            txn_id += 1
        
        if day % 3 == 0:
            transactions.append({
                "date": date_iso,
                "description": "RESTAURANT",
                "amount": 800.0,
                "type": "debit",
                "category": "Food & Dining",
            })
            txn_id += 1
        
        # Monthly salary (1st of each month)
        if date.day == 1:
            transactions.append({
                "date": date_iso,
                "description": "SALARY CREDIT",
                "amount": 50000.0,
                "type": "credit",
                "category": "Income",
            })
            txn_id += 1
        
        # Monthly EMI (5th of each month)
        if date.day == 5:
            transactions.append({
                "date": date_iso,
                "description": "EMI LOAN REPAYMENT",
                "amount": 15000.0,
                "type": "debit",
                "category": "EMI",
            })
            txn_id += 1
        
        # Micro transactions (UPI)
        if day % 1 == 0:
            transactions.append({
                "date": date_iso,
                "description": "UPI-PAYMENT",
                "amount": 150.0,
                "type": "debit",
                "category": "Food & Dining",
            })
            txn_id += 1
    
    # Insert transactions using FinanceDB
    db.insert_transactions(statement_id, transactions)
    
    yield db
    
    # Cleanup
    db.close()
    os.unlink(db_path)


@pytest.fixture
def minimal_db():
    """Create a minimal database with few transactions."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Create FinanceDB instance (tables are created automatically)
    db = FinanceDB(db_path)
    
    # Create a statement record
    with db.transaction() as conn:
        cur = conn.execute(
            "INSERT INTO statements (bank, file_name) VALUES (?, ?)",
            ("TestBank", "minimal_statement.pdf")
        )
        statement_id = cur.lastrowid
    
    # Just 5 transactions
    transactions = [
        {"date": "2025-01-01", "description": "TEST DEBIT", "amount": 100.0, "type": "debit", "category": "Test"},
        {"date": "2025-01-02", "description": "TEST DEBIT", "amount": 200.0, "type": "debit", "category": "Test"},
        {"date": "2025-01-03", "description": "TEST CREDIT", "amount": 1000.0, "type": "credit", "category": "Income"},
        {"date": "2025-01-04", "description": "TEST DEBIT", "amount": 150.0, "type": "debit", "category": "Test"},
        {"date": "2025-01-05", "description": "TEST DEBIT", "amount": 300.0, "type": "debit", "category": "Test"},
    ]
    
    # Insert transactions using FinanceDB
    db.insert_transactions(statement_id, transactions)
    
    yield db
    
    # Cleanup
    db.close()
    os.unlink(db_path)


# ============================================================
# Utility Function Tests
# ============================================================

class TestUtilityFunctions:
    """Test utility functions."""

    def test_normalize_score_within_range(self):
        """Test that normalize_score always returns 0-1."""
        # Normal cases
        assert 0 <= _normalize_score(0.5, 0, 1) <= 1
        assert 0 <= _normalize_score(0.5, 0, 2) <= 1
        assert 0 <= _normalize_score(1.5, 0, 1) <= 1  # Above max
        
    def test_normalize_score_clamping(self):
        """Test that values are clamped to 0-1."""
        assert _normalize_score(-1, 0, 1) == 0.0
        assert _normalize_score(2, 0, 1) == 1.0
        
    def test_normalize_score_edge_cases(self):
        """Test edge cases."""
        # Equal min and max
        assert _normalize_score(5, 5, 5) == 0.5
        
    def test_coefficient_of_variation_empty(self):
        """Test CV with empty list."""
        assert _coefficient_of_variation([]) == 0.0
        assert _coefficient_of_variation([1]) == 0.0
        
    def test_coefficient_of_variation_normal(self):
        """Test CV with normal data."""
        # Zero variance
        assert _coefficient_of_variation([5, 5, 5, 5]) == 0.0
        
        # Some variance
        cv = _coefficient_of_variation([1, 2, 3, 4, 5])
        assert cv > 0
        
    def test_moving_average(self):
        """Test moving average calculation."""
        values = [1, 2, 3, 4, 5]
        ma = _moving_average(values, 3)
        
        assert len(ma) == len(values)
        assert ma[0] == 1.0  # First value
        assert ma[2] == 2.0  # (1+2+3)/3
        
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
        
        # Compare as JSON strings to handle floating point
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
        with temp_db.connection() as conn:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables_before = set(row[0] for row in cur.fetchall())
        
        # Run profile
        compute_behavior_profile(temp_db)
        
        # Get tables after
        with temp_db.connection() as conn:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables_after = set(row[0] for row in cur.fetchall())
        
        assert tables_before == tables_after
        
    def test_no_new_rows(self, temp_db):
        """Test that no new rows are added."""
        with temp_db.connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM transactions")
            count_before = cur.fetchone()[0]
        
        # Run profile
        compute_behavior_profile(temp_db)
        
        # Get count after
        with temp_db.connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM transactions")
            count_after = cur.fetchone()[0]
        
        assert count_before == count_after


# ============================================================
# Edge Case Tests
# ============================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_database(self):
        """Test with empty database."""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        # Use FinanceDB - tables are created automatically
        db = FinanceDB(db_path)
        
        # Database is empty (no transactions)
        try:
            profile = compute_behavior_profile(db)
            
            # Should return valid structure with defaults
            assert "financial_health_score" in profile
            assert 0 <= profile["financial_health_score"] <= 100
            assert profile["confidence"] >= 0
        finally:
            db.close()
            os.unlink(db_path)
            
    def test_minimal_data(self, minimal_db):
        """Test with minimal transaction data."""
        profile = compute_behavior_profile(minimal_db)
        
        # Should still produce valid output
        assert "financial_health_score" in profile
        assert 0 <= profile["financial_health_score"] <= 100
        
    def test_all_credits(self):
        """Test with only credit transactions."""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        # Use FinanceDB - tables are created automatically
        db = FinanceDB(db_path)
        
        # Create a statement record
        with db.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO statements (bank, file_name) VALUES (?, ?)",
                ("TestBank", "all_credits.pdf")
            )
            statement_id = cur.lastrowid
        
        # Only credits
        transactions = [
            {"date": "2025-01-01", "description": "INCOME", "amount": 10000, "type": "credit", "category": "Income"},
        ]
        
        db.insert_transactions(statement_id, transactions)
        
        try:
            profile = compute_behavior_profile(db)
            assert 0 <= profile["financial_health_score"] <= 100
        finally:
            db.close()
            os.unlink(db_path)
            
    def test_all_debits(self):
        """Test with only debit transactions."""
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        # Use FinanceDB - tables are created automatically
        db = FinanceDB(db_path)
        
        # Create a statement record
        with db.transaction() as conn:
            cur = conn.execute(
                "INSERT INTO statements (bank, file_name) VALUES (?, ?)",
                ("TestBank", "all_debits.pdf")
            )
            statement_id = cur.lastrowid
        
        # Only debits
        transactions = []
        for i in range(10):
            date = f"2025-01-{i+1:02d}"
            transactions.append({
                "date": date,
                "description": "EXPENSE",
                "amount": 1000,
                "type": "debit",
                "category": "Test"
            })
        
        db.insert_transactions(statement_id, transactions)
        
        try:
            profile = compute_behavior_profile(db)
            assert 0 <= profile["financial_health_score"] <= 100
        finally:
            db.close()
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
        
        assert result["gambling_flag"] == True
        assert result["gambling_transaction_count"] == 2
        
    def test_upi_micro_spend_detection(self):
        """Test UPI micro-spend clustering detection."""
        transactions = []
        
        # Create 15 micro transactions on same day
        for i in range(15):
            transactions.append({
                "type": "debit",
                "description": "UPI PAYMENT",
                "amount": 100,
                "date_iso": "2025-01-01"
            })
        
        result = detect_india_risk_patterns(transactions)
        
        assert result["upi_micro_spend_flag"] == True
        
    def test_loan_app_detection(self):
        """Test loan app pattern detection."""
        transactions = [
            {"type": "credit", "description": "LOAN CREDIT NBFC", "amount": 5000, "date_iso": "2025-01-01"},
            {"type": "credit", "description": "INSTANT LOAN", "amount": 3000, "date_iso": "2025-01-05"},
        ]
        
        result = detect_india_risk_patterns(transactions)
        
        assert result["loan_app_pattern_flag"] == True
        
    def test_emi_ratio_calculation(self):
        """Test EMI ratio calculation."""
        transactions = [
            {"type": "credit", "description": "SALARY", "amount": 50000, "date_iso": "2025-01-01"},
            {"type": "debit", "description": "EMI LOAN", "amount": 15000, "date_iso": "2025-01-05"},
        ]
        
        result = detect_india_risk_patterns(transactions)
        
        # EMI ratio should be 15000/50000 = 0.3
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
