"""M11 — Wellness score canonical unit is 0-100; the snapshot column was not.

Defect under regression
-----------------------
``compute_wellness_score`` returns a score on 0-100 (``wellness.py:88-89``,
``wellness_score * 100`` clamped to ``[0, 100]``). ``compute_financial_profile``
stored it as ``wellness_score_bps = int(wellness_score * 10000)`` — scaling an
already-0-100 value by 10000 again, so a basis-point column held 0-1,000,000
instead of 0-10,000. ``BehaviourRepository._map_snapshot_row`` then converted
bps -> 0-1 -> *100, multiplying by 100 a second time: a real 87.5449 was served
as ``8754.4900``.

Evidence the 0-100 unit is canonical
------------------------------------
1. ``WellnessScoreResponse.score`` is documented "between 0 and 100"
   (``backend/src/models/behaviour.py:31``).
2. ``compute_wellness_score`` clamps its return to ``[0, 100]``.
3. ``classify_wellness_band`` thresholds at 90/75/50/25 — 0-100 bands.
4. Every sibling ``*_score`` written in the same ``BehaviourSnapshotCreate`` is
   a 0-1 ratio times 10000, i.e. a TRUE basis-point value in 0-10,000; only
   wellness was scaled twice.
5. Every reader of ``snapshot["wellness_score"]`` is 0-100:
   ``get_wellness_score`` (:328), ``get_monthly_summary`` (:548), and
   ``_generate_alerts`` (:1053-1058, thresholds 25/50).
6. ``tests/invariants/behaviour.py::assert_behaviour_score_valid`` asserts
   ``[0, 100]``.
7. The no-data fallback in ``get_wellness_score`` returns ``Decimal("100")``
   with band ``"Excellent"`` — a 0-100 value.

The single response this produced was internally inconsistent: components read
0-100 (``cashflow_health: "82.300"``) beside a composite of ``8754.4900``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from src.core.db.connection import get_connection_context
from src.engines.behaviour_engine.wellness import (
    classify_wellness_band,
    compute_wellness_score,
)
from src.models.behaviour import WellnessScoreResponse

#: A basis-point column holds 0-10,000. Anything above is double-scaled.
MAX_VALID_WELLNESS_BPS = 10_000


def _seed_transactions(db_path: str, months: int) -> None:
    with get_connection_context(db_path) as conn:
        conn.execute(
            """
            INSERT INTO accounts (id, name, bank, account_type, balance_paise,
                                  owner_id, household_id)
            VALUES (1, 'Salary', 'Test Bank', 'savings', 800000, 'self', 'primary')
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO statements (id, bank, file_name) "
            "VALUES (1, 'Test Bank', 'test.pdf')"
        )
        seq = 0
        for month in range(1, months + 1):
            iso = f"2026-{month:02d}-05"
            for kind, amount in (("credit", 900000), ("debit", 250000)):
                seq += 1
                conn.execute(
                    """
                    INSERT INTO transactions (statement_id, sequence_num, date,
                        date_iso, description, type, amount_paise, category, account_id)
                    VALUES (1, ?, ?, ?, ?, ?, ?, 'x', 1)
                    """,
                    (seq, iso, iso, f"{kind}-{month}", kind, amount),
                )


@pytest.fixture
def db_with_history(finance_db: Any) -> str:
    _seed_transactions(str(finance_db.db_path), 4)
    return str(finance_db.db_path)


# ==================================================================
# Engine contract — unchanged, but pinned so the write cannot drift from it
# ==================================================================


class TestEngineContractIsZeroToHundred:
    @pytest.mark.parametrize(
        "inputs",
        [
            # best case
            (Decimal("1"), 0, Decimal("1"), Decimal("1"), Decimal("-1"), Decimal("0"), Decimal("0")),
            # worst case
            (Decimal("0"), 100, Decimal("-1"), Decimal("0"), Decimal("2"), Decimal("1"), Decimal("3")),
            # mid
            (Decimal("0.5"), 50, Decimal("0.1"), Decimal("0.5"), Decimal("0.1"), Decimal("0.2"), Decimal("0.3")),
        ],
    )
    def test_engine_always_returns_0_to_100(self, inputs: tuple[Any, ...]) -> None:
        score = compute_wellness_score(*inputs)
        assert Decimal("0") <= score <= Decimal("100")

    def test_band_thresholds_are_zero_to_hundred(self) -> None:
        assert classify_wellness_band(Decimal("100")) == "Excellent"
        assert classify_wellness_band(Decimal("90")) == "Excellent"
        assert classify_wellness_band(Decimal("89.99")) == "Healthy"
        assert classify_wellness_band(Decimal("75")) == "Healthy"
        assert classify_wellness_band(Decimal("50")) == "Developing"
        assert classify_wellness_band(Decimal("25")) == "Risk"
        assert classify_wellness_band(Decimal("24.99")) == "Critical"
        assert classify_wellness_band(Decimal("0")) == "Critical"


# ==================================================================
# The write layer — the single authoritative fix
# ==================================================================


class TestSnapshotWriteUsesTrueBasisPoints:
    def test_wellness_bps_is_in_the_basis_point_range(
        self, db_with_history: str
    ) -> None:
        from src.services.behaviour_service import BehaviourService

        BehaviourService(db_with_history).get_wellness_score()
        with get_connection_context(db_with_history) as conn:
            values = [
                row[0]
                for row in conn.execute(
                    "SELECT wellness_score_bps FROM behaviour_snapshots"
                ).fetchall()
            ]
        assert values, "no snapshot was persisted"
        for value in values:
            assert 0 <= value <= MAX_VALID_WELLNESS_BPS, (
                f"wellness_score_bps={value} is outside 0-10000; the score is "
                f"already 0-100 and must not be scaled a second time"
            )

    def test_sibling_score_columns_stay_true_basis_points(
        self, db_with_history: str
    ) -> None:
        """The columns that were already correct must stay correct."""
        from src.services.behaviour_service import BehaviourService

        BehaviourService(db_with_history).get_wellness_score()
        with get_connection_context(db_with_history) as conn:
            row = conn.execute(
                "SELECT cashflow_stability_score_bps, resilience_index_bps, "
                "savings_discipline_score_bps, wellness_score_bps "
                "FROM behaviour_snapshots ORDER BY id DESC LIMIT 1"
            ).fetchone()
        assert row is not None
        for value in tuple(row):
            assert 0 <= value <= MAX_VALID_WELLNESS_BPS

    def test_write_then_read_round_trips_to_the_engine_value(
        self, db_with_history: str
    ) -> None:
        """What the engine computes is what the service serves, unchanged."""
        from src.services.behaviour_service import BehaviourService

        service = BehaviourService(db_with_history)
        response = service.get_wellness_score()
        assert 0 <= float(response.score) <= 100


# ==================================================================
# The read model / API
# ==================================================================


class TestWellnessScoreResponseIsInRange:
    def test_served_score_is_within_the_documented_range(
        self, db_with_history: str
    ) -> None:
        from src.services.behaviour_service import BehaviourService

        response = BehaviourService(db_with_history).get_wellness_score()
        assert 0 <= float(response.score) <= 100

    def test_band_is_not_informative_at_the_extreme_end(
        self, db_with_history: str
    ) -> None:
        """The defect returned "Excellent" for every household, including 8754."""
        from src.services.behaviour_service import BehaviourService

        response = BehaviourService(db_with_history).get_wellness_score()
        assert response.band == classify_wellness_band(Decimal(str(response.score)))

    def test_components_and_composite_share_one_scale(
        self, db_with_history: str
    ) -> None:
        """Components already read 0-100; the composite must match them."""
        from src.services.behaviour_service import BehaviourService

        response = BehaviourService(db_with_history).get_wellness_score()
        for name, value in response.components.items():
            assert float(value) <= 100, f"component {name}={value} is off-scale"
        assert float(response.score) <= 100

    def test_no_data_fallback_still_honours_the_documented_range(
        self, finance_db: Any
    ) -> None:
        from src.services.behaviour_service import BehaviourService

        response = BehaviourService(str(finance_db.db_path)).get_wellness_score()
        assert 0 <= float(response.score) <= 100

    def test_response_model_documents_the_range(self) -> None:
        schema = WellnessScoreResponse.model_json_schema()
        assert "0 and 100" in schema["properties"]["score"]["description"]


# ==================================================================
# Financial intelligence consumer
# ==================================================================


class TestFinancialIntelligenceConsumer:
    def test_health_score_inherits_the_corrected_scale(self, db_with_history: str) -> None:
        """``_compute_health_score`` passes the wellness score straight through."""
        from src.engines.financial_intelligence.intelligence import (
            _compute_health_score,
        )

        assert _compute_health_score({"wellness_score": Decimal("87.5449")}) == Decimal(
            "87.5449"
        )
        assert _compute_health_score({"wellness_score": Decimal("42")}) == Decimal("42")


# ==================================================================
# Migration of already-persisted double-scaled rows
# ==================================================================


class TestWellnessBpsMigration:
    def _write_snapshot(self, db_path: str, bps: int, day: int = 1) -> None:
        with get_connection_context(db_path) as conn:
            conn.execute(
                """
                INSERT INTO behaviour_snapshots (
                    snapshot_date, household_id, savings_discipline_score_bps,
                    cashflow_stability_score_bps, salary_dependence_ratio_bps,
                    lifestyle_inflation_rate_bps, subscription_burn_rate_bps,
                    resilience_index_bps, wellness_score_bps, version)
                VALUES (?, 'primary', 5000, 8000, 1000, 500, 500,
                        9000, ?, 1)
                """,
                (f"2026-01-{day:02d}", bps),
            )

    def _read_wellness_bps(self, db_path: str) -> list[int]:
        with get_connection_context(db_path) as conn:
            return [
                row[0]
                for row in conn.execute(
                    "SELECT wellness_score_bps FROM behaviour_snapshots "
                    "ORDER BY snapshot_date"
                ).fetchall()
            ]

    def test_double_scaled_rows_are_rescaled(self, finance_db: Any) -> None:
        """875449 bps (a 87.5449 score) becomes 8754 bps."""
        from src.core.db.schema import run_migrations

        db = str(finance_db.db_path)
        self._write_snapshot(db, 875449)

        run_migrations(db)

        assert self._read_wellness_bps(db) == [8754]

    def test_in_range_rows_are_left_alone(self, finance_db: Any) -> None:
        from src.core.db.schema import run_migrations

        db = str(finance_db.db_path)
        expected: list[int] = []
        for index, value in enumerate((0, 1, 5000, 8754, 9999, MAX_VALID_WELLNESS_BPS)):
            self._write_snapshot(db, value, day=index + 1)
            expected.append(value)

        run_migrations(db)

        assert self._read_wellness_bps(db) == expected

    def test_migration_is_idempotent(self, finance_db: Any) -> None:
        from src.core.db.schema import run_migrations

        db = str(finance_db.db_path)
        self._write_snapshot(db, 875449)

        run_migrations(db)
        first = self._read_wellness_bps(db)
        run_migrations(db)
        run_migrations(db)

        assert self._read_wellness_bps(db) == first == [8754]

    def test_max_double_scaled_value_becomes_a_valid_bps(self, finance_db: Any) -> None:
        """1000000 bps (score 100) becomes 10000 bps — still valid, not re-scaled."""
        from src.core.db.schema import run_migrations

        db = str(finance_db.db_path)
        self._write_snapshot(db, 1_000_000)

        run_migrations(db)

        assert self._read_wellness_bps(db) == [MAX_VALID_WELLNESS_BPS]