"""M11 — two defects found by seeding a real database, both reported by Agent 2.

Defect A: ``GET /api/v1/behaviour/profile`` returned HTTP 500 on every call
after the first
-----------------------------------------------------------------------
``behaviour_snapshots`` carries ``UNIQUE(household_id, snapshot_date)`` — one
snapshot per household per day — but ``BehaviourRepository.create_snapshot``
issued a bare ``INSERT``. ``compute_financial_profile`` is invoked on demand
(from ``get_wellness_score`` when no snapshot exists, and from
``GET /api/v1/behaviour/profile``), so a second call on the same day is normal
traffic, and it raised::

    sqlite3.IntegrityError: UNIQUE constraint failed:
        behaviour_snapshots.household_id, behaviour_snapshots.snapshot_date

Reproduced exactly: call 1 → 200, call 2 → 500, call 3 → 500.

Fixed by making ``create_snapshot`` an upsert. Same class of fix for
``PatternRepository.create_pattern``, which had the identical problem against
``UNIQUE(pattern_type, pattern_key, household_id)``.

Defect B: ``GET /api/v1/behaviour/patterns`` was structurally always ``[]``
-----------------------------------------------------------------------
``PatternRepository.create_pattern`` is the only writer of
``behaviour_patterns`` and had ZERO callers — no router, service, startup hook
or job. The table could therefore never hold a row, so no amount of seeding
could change the response, and the three other readers of the same table
(``get_monthly_summary``, ``_generate_alerts``, the workspace aggregate) saw
nothing either.

Fixed by detecting patterns from the household's recorded transactions and
persisting them through ``create_pattern`` from inside
``BehaviourService.get_patterns`` — the canonical ``/api/v1/*`` path. That
service already establishes on-demand computation for behaviour data
(``get_wellness_score`` computes a snapshot when none exists), so detection on
read introduces no second architecture.

Three further defects surfaced while wiring it up, all of the same "the reader
expects a key the mapper does not produce" shape:

* ``get_patterns`` and ``generate_monthly_summary`` read ``p["strength_bps"]``
  and ``p["total_amount_paise"]``. ``_map_pattern_row`` emits ``strength``
  (0-100) and ``total_amount`` (rupees). Both were ``KeyError`` → HTTP 500.
* ``_compute_subscription_alerts`` read ``p["total_amount_paise"]`` the same way.
* ``get_patterns``'s second parameter was named ``limit`` and documented as
  "maximum number of patterns" while being passed straight to
  ``get_recent_patterns(days=...)``. The router's own parameter is ``days``
  (default 30), so the default of 5 silently narrowed a 30-day query to 5 days.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from src.core.db.connection import get_connection_context


def _month_start(back: int) -> date:
    """First day of the calendar month `back` months from today."""
    year, month = date.today().year, date.today().month
    for _ in range(back):
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    return date(year, month, 1)


def _seed_household(db_path: str) -> None:
    """A household with a fixed monthly subscription and a repeating impulse.

    The subscription is identical in every month at the same amount; the impulse
    merchant recurs weekly at a small amount. Both are real recurring shapes a
    detector must be able to recognise from recorded transactions.
    """
    today = date.today()
    with get_connection_context(db_path) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO accounts (id, name, bank, account_type,
                balance_paise, owner_id, household_id)
            VALUES (1, 'Salary', 'Test Bank', 'savings', 900000, 'self', 'primary')
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO statements (id, bank, file_name) "
            "VALUES (1, 'Test Bank', 'test.pdf')"
        )
        conn.execute("UPDATE accounts SET balance_paise = 900000 WHERE id = 1")
        seq = 0
        for back in range(5, -1, -1):
            when = min(_month_start(back), today)
            for description, kind, amount in (
                ("ACME CORP SALARY", "credit", 900000),
                ("NETFLIX SUBSCRIPTION", "debit", 64900),
            ):
                seq += 1
                conn.execute(
                    """
                    INSERT INTO transactions (statement_id, sequence_num, date,
                        date_iso, description, type, amount_paise, category, account_id)
                    VALUES (1, ?, ?, ?, ?, ?, ?, 'x', 1)
                    """,
                    (seq, when.isoformat(), when.isoformat(), description, kind, amount),
                )
        for back in range(25, 0, -1):
            when = (today - timedelta(days=back)).isoformat()
            seq += 1
            conn.execute(
                """
                INSERT INTO transactions (statement_id, sequence_num, date,
                    date_iso, description, type, amount_paise, category, account_id)
                VALUES (1, ?, ?, ?, ?, ?, ?, 'x', 1)
                """,
                (seq, when, when, "ZARA impulse buy", "debit", 45000),
            )
        conn.commit()


@pytest.fixture
def seeded(finance_db: Any) -> str:
    _seed_household(str(finance_db.db_path))
    return str(finance_db.db_path)


# ==================================================================
# Defect A — snapshot upsert
# ==================================================================


class TestProfileEndpointIsRepeatable:
    def test_the_defect_reproduction_shape(self, client: TestClient, seeded: str) -> None:
        """Call 1 -> 200, call 2 -> 500, call 3 -> 500 before the fix."""
        responses = [
            client.get("/api/v1/behaviour/profile") for _ in range(3)
        ]
        assert [r.status_code for r in responses] == [200, 200, 200], (
            "a repeat call on the same day must refresh the day's snapshot, "
            "not raise UNIQUE(household_id, snapshot_date)"
        )

    def test_repeat_calls_are_stable(self, client: TestClient, seeded: str) -> None:
        first = client.get("/api/v1/behaviour/profile").json()
        second = client.get("/api/v1/behaviour/profile").json()
        assert first == second

    def test_only_one_snapshot_row_exists_per_day(self, seeded: str) -> None:
        from src.services.behaviour_service import BehaviourService

        BehaviourService(seeded).compute_financial_profile()
        BehaviourService(seeded).compute_financial_profile()
        BehaviourService(seeded).compute_financial_profile()

        with get_connection_context(seeded) as conn:
            rows = conn.execute(
                "SELECT COUNT(*) FROM behaviour_snapshots WHERE household_id = 'primary'"
            ).fetchone()[0]
        assert rows == 1

    def test_a_refreshed_snapshot_reports_the_new_value(self, seeded: str) -> None:
        """Upsert, not skip: the stored row must reflect the latest computation."""
        from src.services.behaviour_service import BehaviourService

        BehaviourService(seeded).compute_financial_profile()
        with get_connection_context(seeded) as conn:
            before = conn.execute(
                "SELECT wellness_score_bps FROM behaviour_snapshots"
            ).fetchone()[0]

        with get_connection_context(seeded) as conn:
            conn.execute(
                "UPDATE behaviour_snapshots SET wellness_score_bps = 1234"
            )
            conn.commit()

        BehaviourService(seeded).compute_financial_profile()
        with get_connection_context(seeded) as conn:
            after = conn.execute(
                "SELECT wellness_score_bps FROM behaviour_snapshots"
            ).fetchone()[0]

        assert after != 1234, (
            "the upsert must overwrite the stored row, not leave the previous "
            "value in place"
        )
        assert after == before, (
            "recomputing the same data is deterministic, so a refresh of "
            "unchanged data must not change the score"
        )

    def test_repository_upsert_directly(self, finance_db: Any) -> None:
        from src.repositories.behaviour_repository import BehaviourRepository

        repo = BehaviourRepository(str(finance_db.db_path))
        payload = {
            "snapshot_date": "2026-05-01",
            "household_id": "primary",
            "savings_discipline_score_bps": 5000,
            "cashflow_stability_score_bps": 6000,
            "salary_dependence_ratio_bps": 1000,
            "lifestyle_inflation_rate_bps": 500,
            "subscription_burn_rate_bps": 300,
            "resilience_index_bps": 7000,
            "wellness_score_bps": 8000,
            "version": 1,
        }
        first = repo.create_snapshot(dict(payload))
        second = repo.create_snapshot({**payload, "wellness_score_bps": 9000})
        assert first is not None
        assert second is not None
        assert first["id"] == second["id"], "the upsert must update, not duplicate"
        assert second["wellness_score"] == 90


# ==================================================================
# Defect B — pattern detection wired into the canonical path
# ==================================================================


class TestPatternsArePopulated:
    def test_the_pattern_table_is_no_longer_structurally_empty(
        self, seeded: str
    ) -> None:
        from src.services.behaviour_service import BehaviourService

        BehaviourService(seeded).get_patterns()
        with get_connection_context(seeded) as conn:
            count = conn.execute("SELECT COUNT(*) FROM behaviour_patterns").fetchone()[0]
        assert count > 0, (
            "no amount of seeding can populate behaviour_patterns unless "
            "something writes it; create_pattern had zero callers"
        )

    def test_endpoint_returns_patterns(self, client: TestClient, seeded: str) -> None:
        response = client.get("/api/v1/behaviour/patterns")
        assert response.status_code == 200, response.text
        body = response.json()
        assert isinstance(body, list)
        assert body, "detectable recurring activity produced no patterns"

    def test_a_recurring_fixed_amount_is_a_subscription(self, client: TestClient, seeded: str) -> None:
        body = client.get("/api/v1/behaviour/patterns").json()
        subscriptions = [p for p in body if p["pattern_type"] == "SUBSCRIPTION"]
        assert subscriptions, f"no SUBSCRIPTION detected in {body}"
        assert any("netflix" in p["pattern_key"] for p in subscriptions)

    def test_a_small_repeating_merchant_is_an_impulse(self, client: TestClient, seeded: str) -> None:
        body = client.get("/api/v1/behaviour/patterns").json()
        impulses = [p for p in body if p["pattern_type"] == "IMPULSE"]
        assert impulses, f"no IMPULSE detected in {body}"
        assert any("zara" in p["pattern_key"] for p in impulses)

    def test_pattern_type_filter_still_works(self, client: TestClient, seeded: str) -> None:
        body = client.get("/api/v1/behaviour/patterns?pattern_type=SUBSCRIPTION").json()
        assert body
        assert {p["pattern_type"] for p in body} == {"SUBSCRIPTION"}

    def test_strength_is_on_the_documented_zero_to_one_scale(
        self, client: TestClient, seeded: str
    ) -> None:
        """`FinancialPattern.strength` is documented "Strength of the pattern (0-1)"."""
        for pattern in client.get("/api/v1/behaviour/patterns").json():
            assert 0 <= float(pattern["strength"]) <= 1

    def test_total_amount_is_integer_paise(self, client: TestClient, seeded: str) -> None:
        for pattern in client.get("/api/v1/behaviour/patterns").json():
            assert isinstance(pattern["total_amount_paise"], int)
            assert pattern["total_amount_paise"] > 0

    def test_amounts_are_traceable_to_recorded_debits(
        self, client: TestClient, seeded: str
    ) -> None:
        from src.repositories.transaction_repository import TransactionRepository

        debits = sum(
            t["amount_paise"]
            for t in TransactionRepository(seeded).get_all_transactions()
            if t["type"] == "debit"
        )
        for pattern in client.get("/api/v1/behaviour/patterns").json():
            assert pattern["total_amount_paise"] <= debits

    def test_detection_is_idempotent(self, client: TestClient, seeded: str) -> None:
        """The table is UNIQUE per (type, key, household) and detection runs on
        every read, so a repeat read must update rather than raise."""
        for _ in range(3):
            assert client.get("/api/v1/behaviour/patterns").status_code == 200
        with get_connection_context(seeded) as conn:
            count = conn.execute("SELECT COUNT(*) FROM behaviour_patterns").fetchone()[0]
        assert count == 2, f"expected one row per detected pattern, got {count}"

    def test_create_pattern_upserts(self, finance_db: Any) -> None:
        from src.repositories.pattern_repository import PatternRepository

        repo = PatternRepository(str(finance_db.db_path))
        payload = {
            "pattern_type": "IMPULSE",
            "pattern_key": "merchant",
            "strength_bps": 1000,
            "first_observed": "2026-01-01",
            "last_observed": "2026-01-10",
            "transaction_count": 2,
            "total_amount_paise": 500,
        }
        first = repo.create_pattern(dict(payload))
        second = repo.create_pattern({**payload, "strength_bps": 9000})
        assert first is not None and second is not None
        assert first["id"] == second["id"]
        assert second["strength"] == 90

    def test_no_transactions_yields_no_patterns_not_a_fabricated_one(
        self, finance_db: Any
    ) -> None:
        from src.services.behaviour_service import BehaviourService

        assert BehaviourService(str(finance_db.db_path)).get_patterns() == []

    def test_a_non_recurring_merchant_is_not_called_a_pattern(
        self, finance_db: Any
    ) -> None:
        """One debit at one merchant is not a pattern."""
        with get_connection_context(str(finance_db.db_path)) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO accounts (id, name, bank, account_type,
                    balance_paise, owner_id, household_id)
                VALUES (1, 'A', 'B', 'savings', 100, 'self', 'primary')
                """
            )
            conn.execute(
                "INSERT OR IGNORE INTO statements (id, bank, file_name) "
                "VALUES (1, 'B', 's.pdf')"
            )
            conn.execute(
                """
                INSERT INTO transactions (statement_id, sequence_num, date, date_iso,
                    description, type, amount_paise, category, account_id)
                VALUES (1, 1, '2026-09-01', '2026-09-01', 'ONE OFF COFFEE', 'debit',
                        25000, 'x', 1)
                """
            )
            conn.commit()

        from src.services.behaviour_service import BehaviourService

        assert BehaviourService(str(finance_db.db_path)).get_patterns() == []


# ==================================================================
# The non-persisted snapshot reads — the same defect family
# ==================================================================


class TestNoNonPersistedSnapshotKeyIsRead:
    KEYS = (
        "debt_cycle_score",
        "credit_dependency_ratio",
        "credit_revolver_ratio",
        "income_stability_score",
        "expense_stability_score",
        "strength_bps",
        "total_amount_paise",
    )

    def test_service_source_reads_no_unmapped_key(self) -> None:
        import inspect

        from src.services.behaviour_service import BehaviourService

        source = inspect.getsource(BehaviourService)
        for key in self.KEYS:
            for accessor in (f'snapshot["{key}"]', f'_snapshot["{key}"]'):
                assert accessor not in source, (
                    f"{accessor} reads a key _map_snapshot_row cannot produce"
                )

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/behaviour",
            "/api/v1/behaviour/wellness-score",
            "/api/v1/behaviour/profile",
            "/api/v1/behaviour/debt-health",
            "/api/v1/behaviour/cashflow-health",
            "/api/v1/behaviour/patterns",
            "/api/v1/behaviour/patterns?pattern_type=SUBSCRIPTION",
            "/api/v1/financial-intelligence/outlook",
            "/api/v1/financial-intelligence/report",
            "/api/v1/financial-intelligence/recommendations",
        ],
    )
    def test_endpoint_responds_with_a_snapshot_present(
        self, client: TestClient, seeded: str, path: str
    ) -> None:
        """Every endpoint that reads a snapshot must survive one existing."""
        assert client.get("/api/v1/behaviour/wellness-score").status_code == 200
        response = client.get(path)
        assert response.status_code == 200, f"{path}: {response.text}"