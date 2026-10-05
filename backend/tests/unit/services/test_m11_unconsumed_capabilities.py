"""M11 — Unconsumed backend capabilities: audit findings and broken-path fixes.

Found while auditing the three feature areas M10 reported as having no frontend
surface. Two of M10's named areas (the insights and search routers) do not exist
in this repository at any commit M10 measured; the three real areas are audited
here instead. See `docs/audits/m11-agent3-capability-audit.md` for the full
classification table.

Defects fixed here
------------------
1. `get_debt_health` read `snapshot["debt_cycle_score"]`, but
   `debt_cycle_score` is not a column on `behaviour_snapshots` and
   `BehaviourRepository._map_snapshot_row` cannot produce it. It raised
   `KeyError: 'debt_cycle_score'` and turned `GET /api/v1/behaviour/debt-health`
   — plus every endpoint composing it, including
   `/api/v1/financial-intelligence/outlook` and `/report` — into HTTP 500
   whenever a snapshot existed.

2. `FinancialGoalRepository.list_goals` ordered by, and `create_goal` inserted,
   a `priority` column the `financial_goals` DDL never declared:
   `OperationalError: no such column: priority`, surfacing as HTTP 500 on
   `/financial-intelligence/priorities` and `/report`.

3. `RecommendationService.get_recommendations` returned a HARDCODED
   demonstration profile (`borrowed_lifestyle_ratio=0.35`, `foir=0.45`,
   `liquidity_months=1`, "No subscriptions in demo") and derived every
   recommendation from it, so the same advice was reported to every household.
   It also called `r.dict()`, removed in Pydantic v2, leaving raw domain objects
   in the response and producing HTTP 500 "Unable to serialize unknown type".

4. `RecommendationService.get_recommendation_details` returned a fixed "Build
   Emergency Fund" payload for ANY id, with the fabricated evidence line "63% of
   Indians cannot cover a ₹50,000 emergency (RBI survey)" and a static 0.95
   confidence.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from src.core.db.connection import get_connection_context


def _seed(db_path: str, transactions: int = 12) -> None:
    """Add three months of cashflow.

    Idempotent: the `client` fixture already creates account 1 and statement 1,
    so the account is reused rather than inserted again.
    """
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
        # Three months of income and expense, which is what the behaviour and
        # recommendation engines require before deriving anything.
        months = ["2026-01-05", "2026-02-05", "2026-03-05"]
        seq = 0
        for month in months:
            for kind, amount in (("credit", 900000), ("debit", 250000)):
                seq += 1
                conn.execute(
                    """
                    INSERT INTO transactions (statement_id, sequence_num, date,
                        date_iso, description, type, amount_paise, category, account_id)
                    VALUES (1, ?, ?, ?, ?, ?, ?, 'x', 1)
                    """,
                    (seq, month, month, f"{kind}-{month}", kind, amount),
                )
        for i in range(transactions - len(months) * 2):
            seq += 1
            conn.execute(
                """
                INSERT INTO transactions (statement_id, sequence_num, date,
                    date_iso, description, type, amount_paise, category, account_id)
                VALUES (1, ?, '2026-03-10', '2026-03-10', ?, 'debit', ?, 'x', 1)
                """,
                (seq, f"extra-{i}", 10000 + i),
            )


@pytest.fixture
def seeded(finance_db: Any) -> str:
    _seed(str(finance_db.db_path))
    return str(finance_db.db_path)


# ==================================================================
# 1. debt_cycle_score
# ==================================================================


class TestDebtHealthDoesNotKeyError:
    def test_debt_health_endpoint_returns_200(self, seeded: str) -> None:
        from src.services.behaviour_service import BehaviourService

        BehaviourService(seeded).get_wellness_score()
        response = BehaviourService(seeded).get_debt_health()
        assert response.debt_cycle_score is not None
        assert 0 <= float(response.debt_cycle_score) <= 100

    def test_financial_intelligence_outlook_returns_200(
        self, client: TestClient, seeded: str
    ) -> None:
        from src.services.behaviour_service import BehaviourService

        # A snapshot must exist for the defect to have fired.
        BehaviourService(seeded).get_wellness_score()
        response = client.get("/api/v1/financial-intelligence/outlook")
        assert response.status_code == 200, response.text

    def test_financial_intelligence_report_returns_200(
        self, client: TestClient, seeded: str
    ) -> None:
        from src.services.behaviour_service import BehaviourService

        BehaviourService(seeded).get_wellness_score()
        response = client.get("/api/v1/financial-intelligence/report")
        assert response.status_code == 200, response.text

    def test_debt_cycle_score_is_not_read_from_the_snapshot_row(self) -> None:
        """The defect was reading a field the read model cannot produce."""
        import inspect

        from src.services.behaviour_service import BehaviourService

        source = inspect.getsource(BehaviourService.get_debt_health)
        assert 'snapshot["debt_cycle_score"]' not in source


# ==================================================================
# 2. financial_goals.priority
# ==================================================================


class TestFinancialGoalsPriorityColumn:
    def test_a_fresh_database_has_the_column(self, finance_db: Any) -> None:
        with get_connection_context(str(finance_db.db_path)) as conn:
            columns = {
                row[1] for row in conn.execute("PRAGMA table_info(financial_goals)")
            }
        assert "priority" in columns

    def test_get_household_goals_does_not_raise(self, seeded: str) -> None:
        from src.repositories.financial_goal_repository import FinancialGoalRepository

        repository = FinancialGoalRepository(seeded)
        assert isinstance(repository.get_household_goals("primary"), list)

    def test_create_then_read_round_trips(self, seeded: str) -> None:
        from src.repositories.financial_goal_repository import FinancialGoalRepository

        repository = FinancialGoalRepository(seeded)
        goal_id = repository.create_goal(
            goal_id=1,
            household_id="primary",
            goal_type="emergency_fund",
            name="Emergency Fund",
            target_amount_paise=500000,
            priority="high",
        )
        assert goal_id == 1
        stored = repository.get_goal(1)
        assert stored is not None
        assert stored["priority"] == "high"
        assert any(g["id"] == 1 for g in repository.get_household_goals("primary"))

    def test_default_priority_is_applied_when_omitted(self, seeded: str) -> None:
        from src.repositories.financial_goal_repository import FinancialGoalRepository

        repository = FinancialGoalRepository(seeded)
        repository.create_goal(
            goal_id=2,
            household_id="primary",
            goal_type="emergency_fund",
            name="No Priority",
            target_amount_paise=1000,
        )
        stored = repository.get_goal(2)
        assert stored is not None
        assert stored["priority"] == "medium"

    def test_priorities_endpoint_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/v1/financial-intelligence/priorities")
        assert response.status_code == 200, response.text

    def test_migration_adds_priority_to_a_pre_existing_table(
        self, finance_db: Any
    ) -> None:
        """A database created before the DDL change is brought up to date."""
        import sqlite3

        from src.core.db.schema import run_migrations

        db = str(finance_db.db_path)
        with sqlite3.connect(db) as conn:
            conn.execute("DROP TABLE financial_goals")
            conn.execute("""
                CREATE TABLE financial_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    household_id TEXT NOT NULL DEFAULT 'primary',
                    owner_id TEXT DEFAULT 'self',
                    goal_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    target_amount_paise INTEGER NOT NULL,
                    current_amount_paise INTEGER DEFAULT 0,
                    target_date TEXT,
                    status TEXT DEFAULT 'active',
                    category TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
                """)
            conn.commit()
            columns = {r[1] for r in conn.execute("PRAGMA table_info(financial_goals)")}
        assert "priority" not in columns

        run_migrations(db)

        with get_connection_context(db) as conn:
            columns = {r[1] for r in conn.execute("PRAGMA table_info(financial_goals)")}
        assert "priority" in columns


# ==================================================================
# 3. Recommendations must be derived, not demonstrated
# ==================================================================


class TestRecommendationsAreDerived:
    #: The hardcoded demonstration profile this method used to return.
    DEMO_BORROWED_LIFESTYLE_RATIO = 0.35
    DEMO_FOIR = 0.45
    DEMO_LIQUIDITY_MONTHS = 1

    def test_endpoint_returns_200(self, client: TestClient, seeded: str) -> None:
        response = client.get("/api/v1/financial-intelligence/recommendations")
        assert response.status_code == 200, response.text

    def test_profile_is_derived_not_the_demo_profile(self, seeded: str) -> None:
        from src.services.recommendation_service import RecommendationService

        result = RecommendationService(seeded).get_recommendations()
        assert result["status"] == "available"
        profile = result["profile"]
        assert profile is not None
        assert profile["borrowed_lifestyle_ratio"] != self.DEMO_BORROWED_LIFESTYLE_RATIO
        assert profile["foir"] != self.DEMO_FOIR
        assert profile["liquidity_months"] != self.DEMO_LIQUIDITY_MONTHS

    def test_no_data_reports_insufficient_rather_than_demo_values(
        self, finance_db: Any
    ) -> None:
        from src.services.recommendation_service import RecommendationService

        result = RecommendationService(str(finance_db.db_path)).get_recommendations()
        assert result["status"] == "insufficient_data"
        assert result["recommendations"] == []
        assert result["profile"] is None
        assert result["reason"]
        assert "at least" in result["reason"]

    def test_responses_are_serialisable_dicts(self, seeded: str) -> None:
        from src.services.recommendation_service import RecommendationService

        result = RecommendationService(seeded).get_recommendations()
        for recommendation in result["recommendations"]:
            assert isinstance(recommendation, dict), (
                "a raw domain object reached the response and FastAPI cannot "
                "serialise it"
            )

    def test_no_hardcoded_rbi_statistic_is_emitted(self, seeded: str) -> None:
        """The fabricated evidence line attached to the fixed detail payload."""
        from src.services.recommendation_service import RecommendationService

        service = RecommendationService(seeded)
        payload = service.get_recommendation_details("1")
        serialised = str(payload)
        assert "63% of Indians" not in serialised
        assert "RBI survey" not in serialised

    def test_detail_for_an_unknown_id_reports_not_found(self, seeded: str) -> None:
        from src.services.recommendation_service import RecommendationService

        payload = RecommendationService(seeded).get_recommendation_details(
            "does-not-exist"
        )
        assert payload["found"] is False
        assert payload["detail"] is None

    def test_no_demo_profile_or_wrong_serialiser_remains(self) -> None:
        import inspect

        from src.services.recommendation_service import RecommendationService

        source = inspect.getsource(RecommendationService)
        assert "Sample financial profile" not in source
        assert "For now, return sample recommendations" not in source

        # `Recommendation` is a plain class with its own `to_dict()` — not a
        # Pydantic model. The original code did
        # `r.dict() if hasattr(r, "dict") else r`; `Recommendation` has neither
        # `dict` nor `model_dump`, so the raw domain object reached FastAPI's
        # serialiser and the endpoint returned HTTP 500 "Unable to serialize
        # unknown type: Recommendation". It must call `to_dict()`.
        #
        # Comments are stripped before the check, because the comments that
        # explain the defect necessarily quote the wrong call.
        import io
        import tokenize

        code_lines: list[str] = []
        with open(inspect.getsourcefile(RecommendationService) or "") as handle:
            for token in tokenize.generate_tokens(io.StringIO(handle.read()).readline):
                if token.type == tokenize.COMMENT:
                    continue
                code_lines.append(token.line)
        code = "".join(code_lines)
        # Also drop docstring content, which explains the defect in prose.
        code = "\n".join(
            line for line in code.splitlines() if '"' not in line or "to_dict" in line
        )

        assert "to_dict()" in code, "recommendations must be serialised with to_dict()"
        for wrong in ("r.dict()", "r.model_dump()"):
            assert (
                wrong not in code
            ), f"{wrong} is not the serialiser Recommendation has"

    def test_recommendation_class_really_has_to_dict(self) -> None:
        """Guards the assertion above against the engine changing shape."""
        from src.engines.recommendation_engine.recommendations import Recommendation

        assert hasattr(Recommendation, "to_dict")
        assert not hasattr(Recommendation, "dict")
        assert not hasattr(Recommendation, "model_dump")


# ==================================================================
# 4. Audit: the three capability areas and their live reachability
# ==================================================================


class TestCapabilityAuditReachability:
    """Every endpoint named in the audit responds rather than raising."""

    AREA_ENDPOINTS = {
        "credit-cards": [
            ("GET", "/api/v1/credit-cards"),
            ("GET", "/api/v1/workspaces/credit-cards"),
        ],
        "loans": [
            ("GET", "/api/v1/loans"),
            ("GET", "/api/v1/workspaces/loans"),
            ("GET", "/api/v1/loans/analysis/priority"),
        ],
        "financial-intelligence": [
            ("GET", "/api/v1/financial-intelligence/cashflow-forecast"),
            ("GET", "/api/v1/financial-intelligence/credit-forecast"),
            ("GET", "/api/v1/financial-intelligence/liquidity-forecast"),
            ("GET", "/api/v1/financial-intelligence/outlook"),
            ("GET", "/api/v1/financial-intelligence/priorities"),
            ("GET", "/api/v1/financial-intelligence/recommendations"),
            ("GET", "/api/v1/financial-intelligence/report"),
        ],
    }

    @pytest.mark.parametrize(
        ("area", "method", "path"),
        [
            (area, method, path)
            for area, endpoints in AREA_ENDPOINTS.items()
            for method, path in endpoints
        ],
    )
    def test_endpoint_responds(
        self, client: TestClient, area: str, method: str, path: str
    ) -> None:
        response = client.request(method, path)
        assert response.status_code == 200, f"{area} {method} {path}: {response.text}"

    def test_the_insights_and_search_routers_do_not_exist(self) -> None:
        """M10's audit named these two areas; neither router is in the repo."""
        import os

        import src

        backend = os.path.dirname(os.path.dirname(os.path.abspath(src.__file__)))
        for name in ("insights.py", "search.py"):
            assert not os.path.exists(os.path.join(backend, "routers", name)), (
                f"{name} exists now, so the M11 audit's classification of the "
                f"unconsumed areas must be revisited"
            )
