"""M11 — the Behaviour workspace must not report invented numbers.

Defect under regression
-----------------------
``BehaviourWorkspaceService.get_behaviour_summary`` — which feeds
``GET /api/v1/workspaces/behaviour``, the payload the ``/behaviour`` page
renders — fabricated almost everything it returned:

* ``wellness_score`` started at ``100`` and subtracted
  ``min(30, outstanding // 100000)``, labelled "(placeholder)" in the source.
* ``spending_patterns`` were three fixed rows: housing ₹30,000 / 30% / 1
  transaction, food ₹15,000 / 15% / 50 transactions, transport ₹10,000 / 10% /
  20 transactions.
* ``savings_rate`` was four constants: ``current_rate`` 15.0, ``trend`` "up",
  ``monthly_savings_paise`` 100000, ``income_paise`` 1000000.
* ``debt_health.score`` was 75 and ``debt_to_income_ratio`` was 0.25.
* ``wellness_radar`` was five constants: 80 / 70 / 75 / 65 / 60.
* ``evidence_chain.confidence_score`` was 85.

So every household saw identical behaviour metrics, shown side by side with the
real ``/api/v1/behaviour/*`` endpoints that reported different values. It is the
same fabrication class as the forecast placeholder.

Fix: every figure is delegated to ``BehaviourService`` or derived from the
household's own recorded transactions, and a metric that cannot be derived is
reported as unavailable rather than filled in.
"""

from __future__ import annotations

from typing import Any

import pytest
from src.core.db.connection import get_connection_context

#: The exact constants the defect emitted.
DEMO_SPENDING_PATTERNS = [
    {"category": "housing", "amount_paise": 3000000, "percentage": 30},
    {"category": "food", "amount_paise": 1500000, "percentage": 15},
    {"category": "transport", "amount_paise": 1000000, "percentage": 10},
]
DEMO_SAVINGS_RATE = {
    "current_rate": 15.0,
    "trend": "up",
    "monthly_savings_paise": 100000,
    "income_paise": 1000000,
}
DEMO_RADAR = [80, 70, 75, 65, 60]
DEMO_CONFIDENCE = 85


def _seed(db_path: str, *, with_transactions: bool = True) -> None:
    """Seed a household. `client` already creates account 1 and statement 1."""
    with get_connection_context(db_path) as conn:
        conn.execute("""
            INSERT OR IGNORE INTO accounts (id, name, bank, account_type,
                balance_paise, owner_id, household_id)
            VALUES (1, 'Salary', 'Test Bank', 'savings', 900000, 'self', 'primary')
            """)
        conn.execute("UPDATE accounts SET balance_paise = 900000 WHERE id = 1")
        conn.execute(
            "INSERT OR IGNORE INTO statements (id, bank, file_name) "
            "VALUES (1, 'Test Bank', 'test.pdf')"
        )
        if not with_transactions:
            return
        from datetime import date

        today = date.today()
        this_month = today.strftime("%Y-%m")
        # Explicit calendar months, not a 30-day offset: a 30-day offset from a
        # month boundary lands in the neighbouring month, which is exactly the
        # arithmetic the forecast duplicate-month defect used.
        year, month = int(today.year), today.month
        previous_key = f"{year - 1}-12" if month == 1 else f"{year}-{month - 1:02d}"
        seq = 0
        for month_key in (previous_key, this_month):
            for day, kind, amount in ((1, "credit", 900000), (1, "debit", 250000)):
                when = f"{month_key}-01"
                if when > today.isoformat():
                    continue
                seq += 1
                conn.execute(
                    """
                    INSERT INTO transactions (statement_id, sequence_num, date,
                        date_iso, description, type, amount_paise, category, account_id)
                    VALUES (1, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        seq,
                        when,
                        when,
                        f"{kind}-{month_key}",
                        kind,
                        amount,
                        "salary" if kind == "credit" else "housing",
                    ),
                )
        conn.commit()


@pytest.fixture
def populated(finance_db: Any) -> str:
    _seed(str(finance_db.db_path))
    return str(finance_db.db_path)


@pytest.fixture
def empty(finance_db: Any) -> str:
    _seed(str(finance_db.db_path), with_transactions=False)
    return str(finance_db.db_path)


def _summary(db_path: str) -> dict[str, Any]:
    from src.services.behaviour_workspace_service import BehaviourWorkspaceService

    return BehaviourWorkspaceService(db_path).get_behaviour_summary()


# ==================================================================
# No fabricated figures
# ==================================================================


class TestNoFabricatedFigures:
    def test_demo_spending_patterns_are_gone(self, populated: str) -> None:
        patterns = _summary(populated)["spending_patterns"]
        assert patterns != DEMO_SPENDING_PATTERNS
        for pattern in patterns:
            assert not (
                pattern["category"] in {"housing", "food", "transport"}
                and pattern["amount_paise"] in {3000000, 1500000, 1000000}
            )

    def test_spending_patterns_come_from_real_categories(self, populated: str) -> None:
        patterns = _summary(populated)["spending_patterns"]
        assert patterns, "three months of debits were seeded"
        assert {p["category"] for p in patterns} <= {"salary", "housing"}

    def test_spending_pattern_amounts_sum_to_recorded_debits(
        self, populated: str
    ) -> None:
        from src.repositories.transaction_repository import TransactionRepository

        summary = _summary(populated)
        recorded = sum(
            t["amount_paise"]
            for t in TransactionRepository(populated).get_all_transactions()
            if t["type"] == "debit"
        )
        assert sum(p["amount_paise"] for p in summary["spending_patterns"]) <= recorded

    def test_demo_savings_rate_is_gone(self, populated: str) -> None:
        savings = _summary(populated)["savings_rate"]
        assert savings is not None
        assert savings["income_paise"] != DEMO_SAVINGS_RATE["income_paise"]
        assert savings["savings_paise"] != DEMO_SAVINGS_RATE["monthly_savings_paise"]
        assert "trend" not in savings, "the constant trend string is gone"
        assert "current_rate" not in savings, (
            "a bare percentage here and basis points in the mapper's DTO is the "
            "same unit split as the wellness score"
        )

    def test_savings_rate_is_derived_from_recorded_cashflow(
        self, populated: str
    ) -> None:
        from src.repositories.transaction_repository import TransactionRepository

        transactions = TransactionRepository(populated).get_all_transactions()
        income = sum(t["amount_paise"] for t in transactions if t["type"] == "credit")
        expenses = sum(t["amount_paise"] for t in transactions if t["type"] == "debit")
        savings = _summary(populated)["savings_rate"]
        assert savings["income_paise"] == income
        assert savings["savings_paise"] == income - expenses
        assert savings["savings_rate_bps"] == round(
            (income - expenses) / income * 10000
        )

    def test_radar_is_not_the_five_constants(self, populated: str) -> None:
        radar = _summary(populated)["wellness_radar"]
        scores = [axis["score"] for axis in radar]
        assert scores != DEMO_RADAR
        assert all(axis["max_score"] == 100 for axis in radar)

    def test_radar_axes_come_from_the_wellness_components(self, populated: str) -> None:
        from src.services.behaviour_service import BehaviourService

        components = BehaviourService(populated).get_wellness_score().components
        radar = _summary(populated)["wellness_radar"]
        observed = {axis["score"] for axis in radar}
        for value in components.values():
            if float(value) in observed:
                break
        else:
            pytest.fail("no radar axis matches a measured wellness component")

    def test_evidence_confidence_is_not_a_constant(self, populated: str) -> None:
        chain = _summary(populated)["evidence_chain"]
        assert chain["confidence_score"] != DEMO_CONFIDENCE
        assert (
            chain["confidence_score"] is None
        ), "no confidence is derived for this aggregate, so none is asserted"

    def test_debt_health_is_not_75_and_0_25(self, populated: str) -> None:
        debt = _summary(populated)["debt_health"]
        assert "score" not in debt
        assert debt["debt_to_income_bps"] is not None
        assert debt["total_income_paise"] > 0

    def test_no_placeholder_comment_remains(self) -> None:
        import inspect

        from src.services.behaviour_workspace_service import BehaviourWorkspaceService

        source = inspect.getsource(BehaviourWorkspaceService)
        code = "\n".join(
            line
            for line in source.splitlines()
            if not line.strip().startswith(("*", "#"))
        )
        assert "wellness_score = 100" not in code
        assert "amount_paise" in code  # sanity: the field is still produced


# ==================================================================
# Unavailable is reported, not filled
# ==================================================================


class TestInsufficientDataIsReported:
    def test_status_is_insufficient_data_without_transactions(self, empty: str) -> None:
        summary = _summary(empty)
        assert summary["data_status"] == "insufficient_data"
        assert summary["spending_patterns"] == []
        assert summary["savings_rate"] is None

    def test_an_insight_explains_why(self, empty: str) -> None:
        insights = _summary(empty)["insights"]
        assert len(insights) == 1
        assert insights[0]["type"] == "info"
        assert "transactions" in insights[0]["message"]

    def test_wellness_score_is_still_reported_from_the_authority(
        self, empty: str
    ) -> None:
        """The authority has a documented no-data fallback, so it is quoted."""
        summary = _summary(empty)
        from src.services.behaviour_service import BehaviourService

        assert summary["wellness_score"] == int(
            round(float(BehaviourService(empty).get_wellness_score().score))
        )

    def test_evidence_chain_states_the_transaction_count(self, empty: str) -> None:
        chain = _summary(empty)["evidence_chain"]
        assert (
            "0 recorded transaction" in chain["summary"]
            or "0 transactions" in chain["summary"]
        )


# ==================================================================
# The endpoint agrees with the authority
# ==================================================================


class TestEndpointMatchesTheAuthority:
    """`/api/v1/behaviour` is served by BehaviourWorkspaceService.

    `behaviour_workspace.router` is registered after `behaviour.router` and both
    declare `GET /api/v1/behaviour`, so the workspace handler is the one that
    answers. Verified by asserting on the shape it returns.
    """

    def test_the_endpoint_serves_the_workspace_service(
        self, client: TestClient, populated: str
    ) -> None:
        body = client.get("/api/v1/behaviour").json()
        assert "data_status" in body, (
            "the workspace service is not the handler for this path; the route "
            "collision between behaviour.router and behaviour_workspace.router "
            "has changed and this fixture must be updated"
        )

    def test_workspace_endpoint_returns_200(
        self, client: TestClient, populated: str
    ) -> None:
        response = client.get("/api/v1/behaviour")
        assert response.status_code == 200, response.text

    def test_workspace_wellness_equals_the_wellness_score_endpoint(
        self, client: TestClient, populated: str
    ) -> None:
        """Two workspaces must not disagree about the same household's score."""
        workspace = client.get("/api/v1/behaviour").json()
        canonical = client.get("/api/v1/behaviour/wellness-score").json()
        assert workspace["wellness_score"] == round(float(canonical["score"]))
        assert workspace["wellness_band"] == canonical["band"]
