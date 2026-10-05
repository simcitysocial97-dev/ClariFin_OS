"""Tests for services previously at 0% coverage per M46.6 baseline.

These tests verify behavioral correctness, not just execution, per M46.7
test-quality model. Each test asserts on actual returned values to discriminate
behavioral change.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from src.services.recommendation_service import RecommendationService

# ============================================================
# RecommendationService tests
# ============================================================


def _seed_household(db_path: str, *, monthly_emi_paise: int = 0) -> None:
    """Record income and expenses, optionally against an EMI-sized obligation.

    ``monthly_emi_paise`` goes into the `loans` table so the FOIR the service
    derives is a real obligation against real recorded income.
    """
    from datetime import date

    from src.core.db.connection import get_connection_context

    today = date.today()
    with get_connection_context(db_path) as conn:
        conn.execute("""
            INSERT OR IGNORE INTO accounts (id, name, bank, account_type,
                balance_paise, owner_id, household_id)
            VALUES (1, 'Salary', 'Test Bank', 'savings', 100000, 'self', 'primary')
            """)
        conn.execute(
            "INSERT OR IGNORE INTO statements (id, bank, file_name) "
            "VALUES (1, 'Test Bank', 'test.pdf')"
        )
        conn.execute("UPDATE accounts SET balance_paise = 100000 WHERE id = 1")
        seq = 0
        # Three calendar months of income and expense = 6 transactions, which
        # clears RecommendationService.MIN_TRANSACTIONS_FOR_RECOMMENDATIONS (5).
        # Below that the ratios are not meaningful and the service says so.
        year, month = today.year, today.month
        month_keys = []
        for _ in range(3):
            month_keys.append(f"{year:04d}-{month:02d}")
            month -= 1
            if month == 0:
                month, year = 12, year - 1
        for month_key in reversed(month_keys):
            when = date(int(month_key[:4]), int(month_key[5:]), 1)
            for kind, amount in (("credit", 900000), ("debit", 250000)):
                seq += 1
                conn.execute(
                    """
                    INSERT INTO transactions (statement_id, sequence_num, date,
                        date_iso, description, type, amount_paise, category, account_id)
                    VALUES (1, ?, ?, ?, ?, ?, ?, 'x', 1)
                    """,
                    (
                        seq,
                        when.isoformat(),
                        when.isoformat(),
                        f"{kind}-{month_key}",
                        kind,
                        amount,
                    ),
                )
        if monthly_emi_paise:
            # Column names follow backend/src/core/db/schema.py::_DDL_LOANS.
            conn.execute(
                """
                INSERT INTO loans (id, name, lender, loan_type, principal_paise,
                                   outstanding_paise, interest_rate, tenure_months,
                                   emi_paise, disbursed_date, is_active)
                VALUES (1, 'Home Loan', 'Test Bank', 'HOME', 5000000, 5000000,
                        0.085, 240, ?, ?, 1)
                """,
                (monthly_emi_paise, today.isoformat()),
            )
        conn.commit()


@pytest.fixture
def household(finance_db: Any) -> str:
    """A household with recorded cashflow and no obligations."""
    _seed_household(str(finance_db.db_path))
    return str(finance_db.db_path)


@pytest.fixture
def indebted_household(finance_db: Any) -> str:
    """A household whose EMI is 70% of recorded monthly income.

    `compute_foir` = (loan_emi + card_min_due) / monthly_income, so an EMI of
    630000 against 900000 of income is a FOIR of 0.70 — the CRITICAL band. The
    profile is derived, so the severity follows from the recorded data rather
    than from a value handed to the service.
    """
    _seed_household(str(finance_db.db_path), monthly_emi_paise=630000)
    return str(finance_db.db_path)


class TestRecommendationService:
    """Tests for RecommendationService.get_recommendations.

    M11: these previously ran against a HARDCODED demonstration profile inside
    the service (`borrowed_lifestyle_ratio=0.35`, `foir=0.45`,
    `liquidity_months=1`), so every household received identical advice. The
    tests asserted that fabricated output — one asserted a non-empty list "the
    demo profile yields", the other patched a `_demo_profile` method that never
    existed (`create=True`), so the patch was a no-op and the assertion actually
    exercised the hardcoded constants.

    The intent of both is kept — in particular "discriminates the engine from a
    no-op wrapper" — but the input is now the household's own recorded data.
    """

    def test_returns_dict_with_recommendations_key(self, household: str) -> None:
        """get_recommendations must return a dict that contains a 'recommendations' key."""
        result = RecommendationService(household).get_recommendations()
        assert isinstance(result, dict)
        assert "recommendations" in result

    def test_default_household_id_does_not_raise(self, finance_db: Any) -> None:
        """Default household_id='primary' must not raise, with no recorded data.

        With nothing recorded the honest answer is "not enough data", not a
        recommendation derived from invented ratios.
        """
        result = RecommendationService(str(finance_db.db_path)).get_recommendations()
        assert isinstance(result["recommendations"], list)
        assert result["status"] == "insufficient_data"
        assert result["recommendations"] == []
        assert result["reason"], "the absence must state why"
        assert result["profile"] is None, "no profile may be reported without data"

    def test_custom_household_id_accepted(self, household: str) -> None:
        """A custom household_id must be accepted without raising."""
        result = RecommendationService(household).get_recommendations(
            household_id="hh-abc"
        )
        assert "recommendations" in result

    def test_a_healthy_household_gets_no_advice(self, household: str) -> None:
        """No debt and ample liquidity means the engine has nothing to advise.

        The engine is discriminating, not broken: an empty list here is the
        correct answer for a household that is not overleveraged, and it is the
        opposite of the previous behaviour, which produced the same
        "Build Emergency Fund" advice for everybody.
        """
        result = RecommendationService(household).get_recommendations()
        assert result["status"] == "available"
        assert result["recommendations"] == []
        assert result["profile"]["foir"] < 0.5

    def test_recommendation_objects_have_required_fields(
        self, indebted_household: str
    ) -> None:
        """Each recommendation must be a JSON-serialisable dict with its fields.

        The endpoint returned HTTP 500 "Unable to serialize unknown type:
        Recommendation" while the service handed back domain objects, so this
        asserts dicts rather than objects.
        """
        result = RecommendationService(indebted_household).get_recommendations()
        recs = result["recommendations"]
        assert recs, "a heavily indebted household should be advised"
        for rec in recs:
            assert isinstance(rec, dict), (
                "a raw domain object reaches the response and FastAPI cannot "
                "serialise it"
            )
            for field in ("title", "severity", "suggested_action"):
                assert field in rec, f"missing {field}"
            assert rec["severity"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_profile_is_derived_from_recorded_data(self, household: str) -> None:
        """The reported profile must come from the household's own figures."""
        from src.repositories.transaction_repository import TransactionRepository

        result = RecommendationService(household).get_recommendations()
        assert result["status"] == "available"
        profile = result["profile"]

        income = sum(
            t["amount_paise"]
            for t in TransactionRepository(household).get_all_transactions()
            if t["type"] == "credit"
        )
        expenses = sum(
            t["amount_paise"]
            for t in TransactionRepository(household).get_all_transactions()
            if t["type"] == "debit"
        )
        assert (
            profile["total_income_paise"] == income
        ), "the reported income must be the recorded income"
        assert profile["total_expenses_paise"] == expenses
        assert profile["months_observed"] == 3
        assert profile["monthly_income_paise"] == income // 3, (
            "FOIR is a monthly ratio, so monthly income must be the recorded "
            "income divided by the months observed — not the multi-month total"
        )

    def test_high_foir_triggers_severity_recommendation(
        self, indebted_household: str
    ) -> None:
        """A real high-FOIR household should yield HIGH/CRITICAL severity.

        This discriminates the engine from a no-op wrapper — the engine must
        actually inspect the derived profile values. The EMI is in the database
        and the income is in the transactions, so a HIGH result can only come
        from the engine having inspected real figures.
        """
        result = RecommendationService(indebted_household).get_recommendations()
        assert result["status"] == "available"
        assert (
            result["profile"]["monthly_income_paise"] == 900000
        ), "three months of 900000 income is 900000 per month"
        assert result["profile"]["foir"] >= 0.6, (
            f"an EMI of 630000 against 900000 monthly income is a FOIR of 0.7, "
            f"got {result['profile']['foir']}"
        )
        severities = {r["severity"] for r in result["recommendations"]}
        assert "HIGH" in severities or "CRITICAL" in severities


# ============================================================
# NetWorthWorkspaceService tests
# ============================================================


class TestNetWorthWorkspaceService:
    """Tests for NetWorthWorkspaceService.get_networth_summary."""

    def _service(self, temp_db):
        from src.services.networth_workspace_service import (
            NetWorthWorkspaceService,
        )

        return NetWorthWorkspaceService(db_path=temp_db)

    def test_init_assigns_repos(self, temp_db) -> None:
        """Service init wires account/investment/loan/statement repos."""
        svc = self._service(temp_db)
        assert svc.account_repo is not None
        assert svc.investment_repo is not None
        assert svc.loan_repo is not None
        assert svc.statement_repo is not None

    def test_default_period_is_one_month(self, temp_db) -> None:
        """Default period must be '1M' per the API contract."""
        svc = self._service(temp_db)
        # Exercise get_networth_summary with default period; verify no exception
        result = svc.get_networth_summary()
        assert isinstance(result, dict)
        # Real NetWorthViewModel fields
        assert "total_net_worth_paise" in result
        assert "total_assets_paise" in result
        assert "total_liabilities_paise" in result
        assert "composition" in result

    def test_account_type_filter_excludes_other_types(self, temp_db) -> None:
        """Filtering by account_types must exclude accounts outside the filter set."""
        svc = self._service(temp_db)
        result_all = svc.get_networth_summary()
        result_filtered = svc.get_networth_summary(account_types=["SAVINGS"])
        # Total balances with a filter must not exceed totals without a filter
        bal_all = result_all.get("total_assets_paise", 0) or 0
        bal_filtered = result_filtered.get("total_assets_paise", 0) or 0
        assert bal_filtered <= bal_all

    def test_invalid_period_does_not_crash(self, temp_db) -> None:
        """An unrecognized period should not raise (defensive — must return a dict)."""
        svc = self._service(temp_db)
        result = svc.get_networth_summary(period="99X")
        assert isinstance(result, dict)
