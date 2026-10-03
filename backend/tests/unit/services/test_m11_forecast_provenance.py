"""M11 — Forecast projection provenance: no fabricated financial values.

Defect under regression
-----------------------
``ForecastService._generate_cashflow_projections`` emitted a fixed
``income_paise=10_000_000 / expenses_paise=6_000_000 / net_paise=4_000_000``
triple for every month of every horizon, regardless of any data in the
database, and derived its month keys from
``date.today() + timedelta(days=30 * month)``, which lands two 30-day offsets
inside the same calendar month — so ``2026-12`` and ``2027-03`` each appeared
twice.

Two further fabrications in the same response: ``confidence_intervals``
returned net worth +/-10/15/20% for 90/95/99% from constants, and the scenario
projection date was ``f"202{horizon_months}-01-01"``, an invalid ISO date
(``20212-01-01`` at the default horizon of 12).

Fix
---
Cashflow projections are derived from measured history by the existing
``FinancialIntelligenceService`` / ``forecast_cashflow`` engine over
``CashflowRepository.get_true_monthly_cashflow``. When there is not enough
measurable history the series is EMPTY and ``cashflow_forecast_basis.status``
is ``"unavailable"`` with a reason — the absence is reported, never filled.

Net worth comes from ``NetWorthService``, the same authority
``GET /api/v1/net-worth`` reports.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from src.core.db.connection import get_connection_context
from src.services.forecast_service import (
    MIN_CASHFLOW_HISTORY_MONTHS,
    ForecastService,
    add_months,
    month_key,
)

# The exact triple the defect emitted. No projection may ever carry it unless a
# household's own measured history genuinely produces it.
PLACEHOLDER_INCOME_PAISE = 10_000_000
PLACEHOLDER_EXPENSES_PAISE = 6_000_000
PLACEHOLDER_NET_PAISE = 4_000_000


def _seed_months(db_path: str, months: list[str], income: int, expenses: int) -> None:
    """Seed one income and one expense transaction per calendar month."""
    with get_connection_context(db_path) as conn:
        conn.execute(
            """
            INSERT INTO accounts (id, name, bank, account_type, balance_paise,
                                  owner_id, household_id)
            VALUES (1, 'Salary', 'Test Bank', 'savings', 1000000, 'self', 'primary')
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO statements (id, bank, file_name) "
            "VALUES (1, 'Test Bank', 'test.pdf')"
        )
        seq = 0
        for iso in months:
            seq += 1
            conn.execute(
                """
                INSERT INTO transactions (statement_id, sequence_num, date, date_iso,
                    description, type, amount_paise, category, account_id)
                VALUES (1, ?, ?, ?, ?, 'credit', ?, 'salary', 1)
                """,
                (seq, iso, iso, f"income-{iso}", income),
            )
            seq += 1
            conn.execute(
                """
                INSERT INTO transactions (statement_id, sequence_num, date, date_iso,
                    description, type, amount_paise, category, account_id)
                VALUES (1, ?, ?, ?, ?, 'debit', ?, 'living', 1)
                """,
                (seq, iso, iso, f"expense-{iso}", expenses),
            )


@pytest.fixture
def empty_db(finance_db: Any) -> str:
    """A database with no transactions at all."""
    return str(finance_db.db_path)


@pytest.fixture
def sparse_db(finance_db: Any) -> str:
    """A database with exactly one month of measured cashflow."""
    _seed_months(str(finance_db.db_path), ["2026-01-05"], 800000, 300000)
    return str(finance_db.db_path)


@pytest.fixture
def populated_db(finance_db: Any) -> str:
    """A database with three months of measured cashflow."""
    _seed_months(
        str(finance_db.db_path),
        ["2026-01-05", "2026-02-05", "2026-03-05"],
        800000,
        300000,
    )
    return str(finance_db.db_path)


# ==================================================================
# Calendar arithmetic — the duplicate month key defect
# ==================================================================


class TestMonthArithmetic:
    """30-day offsets drift; calendar months do not."""

    @pytest.mark.parametrize(
        ("anchor", "months", "expected"),
        [
            (date(2026, 1, 15), 1, date(2026, 2, 15)),
            (date(2026, 1, 15), 2, date(2026, 3, 15)),
            (date(2026, 1, 15), 12, date(2027, 1, 15)),
            (date(2026, 1, 15), 13, date(2027, 2, 15)),
            (date(2026, 12, 2), 1, date(2027, 1, 2)),
            (date(2026, 11, 30), 1, date(2026, 12, 30)),
            (date(2026, 1, 31), 1, date(2026, 2, 28)),
            (date(2024, 1, 31), 1, date(2024, 2, 29)),
        ],
    )
    def test_add_months_is_calendar_exact(
        self, anchor: date, months: int, expected: date
    ) -> None:
        assert add_months(anchor, months) == expected

    def test_consecutive_months_never_share_a_month_key(self) -> None:
        """The exact property the 30-day offset violated."""
        anchor = date(2026, 1, 2)
        keys = [month_key(add_months(anchor, i)) for i in range(1, 25)]
        assert len(keys) == len(set(keys)), f"duplicate month keys: {keys}"

    def test_month_key_format(self) -> None:
        assert month_key(date(2026, 3, 7)) == "2026-03"
        assert month_key(date(2026, 12, 31)) == "2026-12"


# ==================================================================
# Cashflow projection provenance
# ==================================================================


class TestCashflowProjectionIsNotFabricated:
    """No projection may be produced without measured history behind it."""

    def test_populated_dataset_produces_a_measured_projection(
        self, populated_db: str
    ) -> None:
        dto = ForecastService(populated_db).get_forecast_summary(horizon_months=6)
        basis = dto.cashflow_forecast_basis

        assert basis.status == "available"
        assert basis.model == "v1.0-weightedaverage"
        assert basis.history_months == 3
        assert basis.projected_months == 6
        assert len(dto.cashflow_projections) == 6

    def test_populated_projection_matches_the_measured_history(
        self, populated_db: str
    ) -> None:
        """Every value must be derivable from the seeded 800000/300000 history."""
        dto = ForecastService(populated_db).get_forecast_summary(horizon_months=4)
        for row in dto.cashflow_projections:
            assert row.income_paise == 800000
            assert row.expenses_paise == 300000
            assert row.net_paise == 500000
            assert (
                row.income_paise,
                row.expenses_paise,
                row.net_paise,
            ) != (
                PLACEHOLDER_INCOME_PAISE,
                PLACEHOLDER_EXPENSES_PAISE,
                PLACEHOLDER_NET_PAISE,
            )

    def test_projection_months_follow_on_from_the_last_measured_month(
        self, populated_db: str
    ) -> None:
        """A forecast starts after the history, not at a hardcoded date."""
        dto = ForecastService(populated_db).get_forecast_summary(horizon_months=3)
        months = [row.month for row in dto.cashflow_projections]
        assert months == ["2026-04", "2026-05", "2026-06"]

    def test_empty_dataset_reports_unavailable_not_zero(
        self, empty_db: str
    ) -> None:
        """The absence of a projection is stated, not filled with constants."""
        dto = ForecastService(empty_db).get_forecast_summary(horizon_months=12)

        assert dto.cashflow_projections == []
        assert dto.cashflow_forecast_basis.status == "unavailable"
        assert dto.cashflow_forecast_basis.projected_months == 0
        assert dto.cashflow_forecast_basis.history_months == 0
        assert dto.cashflow_forecast_basis.reason
        assert dto.cashflow_forecast_basis.confidence_bps is None
        assert dto.evidence_chain is not None
        assert dto.evidence_chain.confidence_score is None

    def test_sparse_dataset_reports_unavailable_with_the_actual_count(
        self, sparse_db: str
    ) -> None:
        dto = ForecastService(sparse_db).get_forecast_summary(horizon_months=6)

        assert dto.cashflow_projections == []
        assert dto.cashflow_forecast_basis.status == "unavailable"
        assert dto.cashflow_forecast_basis.history_months == 1
        assert str(MIN_CASHFLOW_HISTORY_MONTHS) in dto.cashflow_forecast_basis.reason

    def test_no_confidence_interval_is_invented_without_history(
        self, empty_db: str, sparse_db: str
    ) -> None:
        for db in (empty_db, sparse_db):
            dto = ForecastService(db).get_forecast_summary(horizon_months=6)
            assert (
                dto.confidence_intervals == []
            ), "a bound with no measurement behind it is a fabricated number"

    def test_requested_horizon_beyond_the_model_limit_is_disclosed(
        self, populated_db: str
    ) -> None:
        dto = ForecastService(populated_db).get_forecast_summary(horizon_months=24)
        basis = dto.cashflow_forecast_basis

        assert basis.requested_horizon_months == 24
        assert basis.projected_months == 12
        assert basis.reason and "12" in basis.reason

    def test_horizon_one_still_produces_a_single_month(
        self, populated_db: str
    ) -> None:
        dto = ForecastService(populated_db).get_forecast_summary(horizon_months=1)
        assert len(dto.cashflow_projections) == 1
        assert dto.cashflow_forecast_basis.projected_months == 1


# ==================================================================
# No duplicate month keys in any series
# ==================================================================


class TestNoDuplicateMonthKeys:
    @pytest.mark.parametrize("horizon", [1, 2, 3, 6, 12, 24, 60])
    def test_cashflow_month_keys_unique(
        self, populated_db: str, horizon: int
    ) -> None:
        dto = ForecastService(populated_db).get_forecast_summary(horizon_months=horizon)
        keys = [row.month for row in dto.cashflow_projections]
        assert len(keys) == len(set(keys)), f"duplicate cashflow month keys: {keys}"

    @pytest.mark.parametrize("horizon", [1, 2, 3, 6, 12, 24, 60])
    def test_net_worth_projection_months_unique(
        self, populated_db: str, horizon: int
    ) -> None:
        dto = ForecastService(populated_db).get_forecast_summary(horizon_months=horizon)
        keys = [month_key(date.fromisoformat(p.date)) for p in dto.net_worth_projections]
        assert len(keys) == len(set(keys)), f"duplicate net worth month keys: {keys}"

    def test_scenario_projection_dates_are_valid_iso_dates(
        self, populated_db: str
    ) -> None:
        """The defect emitted the literal ``20212-01-01`` at horizon 12."""
        for horizon in (1, 6, 12, 24):
            dto = ForecastService(populated_db).get_forecast_summary(
                horizon_months=horizon
            )
            for scenario in dto.scenarios:
                for projection in scenario.net_worth_projections:
                    parsed = date.fromisoformat(projection.date)
                    assert parsed.isoformat() == projection.date

    def test_scenario_dates_track_the_requested_horizon(
        self, populated_db: str
    ) -> None:
        today = date.today()
        dto = ForecastService(populated_db).get_forecast_summary(horizon_months=6)
        for scenario in dto.scenarios:
            for projection in scenario.net_worth_projections:
                assert projection.date == add_months(today, 6).isoformat()


# ==================================================================
# Canonical paise representation
# ==================================================================


class TestPaiseRepresentation:
    def test_all_projection_values_are_integer_paise(self, populated_db: str) -> None:
        dto = ForecastService(populated_db).get_forecast_summary(horizon_months=6)

        for row in dto.cashflow_projections:
            for value in (row.income_paise, row.expenses_paise, row.net_paise):
                assert isinstance(value, int), f"{value!r} is not integer paise"
                assert not isinstance(value, bool)

        for projection in dto.net_worth_projections:
            for value in (
                projection.projected_paise,
                projection.lower_bound_paise,
                projection.upper_bound_paise,
            ):
                assert isinstance(value, int)
                assert not isinstance(value, bool)

    def test_net_is_income_minus_expenses(self, populated_db: str) -> None:
        dto = ForecastService(populated_db).get_forecast_summary(horizon_months=6)
        for row in dto.cashflow_projections:
            assert row.net_paise == row.income_paise - row.expenses_paise

    def test_bounds_bracket_the_projection(self, populated_db: str) -> None:
        dto = ForecastService(populated_db).get_forecast_summary(horizon_months=6)
        for projection in dto.net_worth_projections:
            assert projection.lower_bound_paise <= projection.projected_paise
            assert projection.projected_paise <= projection.upper_bound_paise


# ==================================================================
# Net worth must come from the net worth authority
# ==================================================================


class TestNetWorthAuthority:
    def test_summary_net_worth_matches_the_net_worth_endpoint(
        self, populated_db: str
    ) -> None:
        """Two workspaces reported two different "current net worth" figures."""
        from src.services.networth_service import NetWorthService

        authority = NetWorthService(populated_db).calculate()
        dto = ForecastService(populated_db).get_forecast_summary(horizon_months=6)

        assert dto.summary.current_net_worth_paise == authority.total_net_worth_paise
        assert dto.summary.current_net_worth_paise == 1_000_000

    def test_account_balances_are_included(self, populated_db: str) -> None:
        """The defect summed investments minus loans and dropped cash entirely."""
        dto = ForecastService(populated_db).get_forecast_summary(horizon_months=3)
        assert dto.summary.current_net_worth_paise >= 1_000_000


# ==================================================================
# The mapper must not carry an unsupported claim through
# ==================================================================


class TestMapperRejectsUnsupportedClaims:
    def test_available_with_no_projections_is_reported_unavailable(self) -> None:
        from src.core.mappers.forecast_mapper import ForecastMapper

        dto = ForecastMapper.to_dto(
            {
                "summary": {},
                "cashflow_projections": [],
                "cashflow_forecast_basis": {"status": "available"},
            }
        )
        assert dto.cashflow_forecast_basis.status == "unavailable"
        assert dto.cashflow_forecast_basis.reason

    def test_missing_basis_is_reported_unavailable(self) -> None:
        from src.core.mappers.forecast_mapper import ForecastMapper

        dto = ForecastMapper.to_dto({"summary": {}, "cashflow_projections": []})
        assert dto.cashflow_forecast_basis.status == "unavailable"
        assert dto.cashflow_forecast_basis.reason

    def test_available_basis_is_preserved_when_projections_exist(self) -> None:
        from src.core.mappers.forecast_mapper import ForecastMapper

        dto = ForecastMapper.to_dto(
            {
                "summary": {},
                "cashflow_projections": [
                    {
                        "month": "2026-04",
                        "income_paise": 1,
                        "expenses_paise": 2,
                        "net_paise": -1,
                    }
                ],
                "cashflow_forecast_basis": {
                    "status": "available",
                    "model": "v1.0-weightedaverage",
                    "confidence_bps": 9000,
                    "history_months": 6,
                    "projected_months": 1,
                    "requested_horizon_months": 12,
                },
            }
        )
        assert dto.cashflow_forecast_basis.status == "available"
        assert dto.cashflow_forecast_basis.confidence_bps == 9000


# ==================================================================
# Placeholder detection — a direct tripwire for the original defect
# ==================================================================


class TestPlaceholderTripwire:
    @pytest.mark.parametrize(
        "db_fixture", ["empty_db", "sparse_db", "populated_db"]
    )
    def test_placeholder_triple_never_appears(self, request: Any, db_fixture: str) -> None:
        db = request.getfixturevalue(db_fixture)
        dto = ForecastService(db).get_forecast_summary(horizon_months=12)

        for row in dto.cashflow_projections:
            assert (
                row.income_paise,
                row.expenses_paise,
                row.net_paise,
            ) != (
                PLACEHOLDER_INCOME_PAISE,
                PLACEHOLDER_EXPENSES_PAISE,
                PLACEHOLDER_NET_PAISE,
            ), "the hardcoded placeholder triple is being served as a projection"

    def test_constant_series_across_every_month_is_a_tripwire(
        self, populated_db: str
    ) -> None:
        """A genuine projection may be flat; it must be flat for a stated reason.

        Flatness alone is not a defect, so this asserts the flat value is
        traceable to the measured history rather than to a constant.
        """
        dto = ForecastService(populated_db).get_forecast_summary(horizon_months=6)
        distinct = {row.income_paise for row in dto.cashflow_projections}
        assert distinct == {800000}, (
            "unexpected projected income — the seeded history is a flat 800000 "
            f"income per month, got {distinct}"
        )