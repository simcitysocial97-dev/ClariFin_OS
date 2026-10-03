"""M11 — POST /api/v1/investments returned HTTP 500 for every valid payload.

Defect under regression
-----------------------
Two defects on the same path, the second masked by the first:

1. ``InvestmentService.create_investment`` passed ``buy_price_paise=`` to
   ``InvestmentRepository.create()``, which did not accept it:
   ``TypeError: InvestmentRepository.create() got an unexpected keyword
   argument 'buy_price_paise'``.

2. ``InvestmentRepository.create()`` named ``platform``, ``purchase_date``,
   ``maturity_date`` and ``linked_account_id`` — none of which exist on the
   ``investments`` table (``backend/src/core/db/schema.py``) — supplied TEN
   values for NINE placeholders, and its values were positionally offset, so
   ``platform`` would have been written into ``invested_paise``. With (1)
   removed it failed as ``OperationalError: table investments has no column
   named purchase_date``.

Fix: the repository INSERT is derived from the same DDL as the table, and the
service and router pass only columns that exist.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from src.core.db.connection import get_connection_context

VALID_PAYLOAD = {
    "name": "Nifty Index Fund",
    "investment_type": "mutual_funds",
    "invested_paise": 100000,
    "current_value_paise": 125000,
    "units": 12.5,
}


class TestCreateInvestmentDoesNot500:
    """The endpoint must accept a schema-valid payload."""

    def test_minimal_payload_returns_200(self, client: TestClient) -> None:
        response = client.post("/api/v1/investments", json=VALID_PAYLOAD)
        assert response.status_code == 200, response.text

    def test_the_documented_m10_reproduction_no_longer_500s(
        self, client: TestClient
    ) -> None:
        """M10 recorded this exact request producing a 500.

        It used ``investment_type="equity"``, which is outside the canonical
        ``InvestmentType`` vocabulary the portfolio read returns, so it is now
        a 422 at the boundary instead of a row that permanently breaks the
        read. Both outcomes are asserted.
        """
        rejected = client.post(
            "/api/v1/investments",
            json={
                "name": "X",
                "investment_type": "equity",
                "invested_paise": 1000,
                "current_value_paise": 2000,
                "units": 1.5,
            },
        )
        assert rejected.status_code == 422, rejected.text

        accepted = client.post(
            "/api/v1/investments",
            json={
                "name": "X",
                "investment_type": "stocks",
                "invested_paise": 1000,
                "current_value_paise": 2000,
                "units": 1.5,
            },
        )
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["invested_paise"] == 1000

    def test_a_type_outside_the_vocabulary_is_rejected_not_stored(
        self, client: TestClient
    ) -> None:
        """The read contract is a closed enum; the write must not exceed it."""
        response = client.post(
            "/api/v1/investments",
            json={**VALID_PAYLOAD, "investment_type": "crypto"},
        )
        assert response.status_code == 422

        portfolio = client.get("/api/v1/investments")
        assert portfolio.status_code == 200, portfolio.text
        assert all(
            item["type"] != "crypto" for item in portfolio.json()["investments"]
        )

    def test_every_optional_field_is_accepted_and_persisted(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/v1/investments",
            json={
                **VALID_PAYLOAD,
                "buy_price_paise": 8000,
                "current_price_paise": 10000,
                "as_of_date": "2026-09-30",
                "notes": "SIP monthly",
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["buy_price_paise"] == 8000
        assert body["current_price_paise"] == 10000
        assert body["as_of_date"] == "2026-09-30"
        assert body["notes"] == "SIP monthly"

    def test_amounts_are_not_silently_shifted_between_columns(
        self, client: TestClient
    ) -> None:
        """`platform` was being written into `invested_paise` by position."""
        response = client.post("/api/v1/investments", json=VALID_PAYLOAD)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["invested_paise"] == 100000
        assert body["current_value_paise"] == 125000
        assert body["units"] == 12.5
        assert body["name"] == "Nifty Index Fund"
        assert body["investment_type"] == "mutual_funds"

    def test_missing_as_of_date_is_supplied_because_the_column_requires_it(
        self, client: TestClient
    ) -> None:
        response = client.post("/api/v1/investments", json=VALID_PAYLOAD)
        assert response.status_code == 200, response.text
        assert response.json()["as_of_date"], "as_of_date is NOT NULL in the DDL"

    def test_the_identifier_is_a_string_in_both_reads(self, client: TestClient) -> None:
        """The mutation returned an int id; the read returned a string id."""
        created = client.post("/api/v1/investments", json=VALID_PAYLOAD)
        assert created.status_code == 200, created.text
        created_id = created.json()["id"]
        assert isinstance(created_id, str), (
            f"create returned id={created_id!r} ({type(created_id).__name__}); the "
            f"portfolio read returns InvestmentSummaryDTO.id as str"
        )
        portfolio = client.get("/api/v1/investments").json()
        assert any(item["id"] == created_id for item in portfolio["investments"])

    def test_two_creates_do_not_collide(self, client: TestClient) -> None:
        first = client.post("/api/v1/investments", json=VALID_PAYLOAD)
        second = client.post(
            "/api/v1/investments", json={**VALID_PAYLOAD, "name": "Second"}
        )
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["id"] != second.json()["id"]


class TestRepositoryColumnContract:
    """The repository must only name columns the table actually has."""

    def test_every_named_column_exists(self, finance_db: Any) -> None:
        """Every value the INSERT names must land in the column it names."""
        from src.repositories.investment_repository import InvestmentRepository

        db = str(finance_db.db_path)
        repository = InvestmentRepository(db)
        new_id = repository.create(
            name="Col Check",
            investment_type="mutual_funds",
            invested_paise=1,
            current_value_paise=2,
            as_of_date="2026-05-31",
            units=1.25,
            buy_price_paise=80,
            current_price_paise=160,
            notes="note",
        )
        assert new_id > 0

        with get_connection_context(db) as conn:
            row = conn.execute(
                "SELECT name, investment_type, invested_paise, current_value_paise, "
                "as_of_date, units, buy_price_paise, current_price_paise, notes "
                "FROM investments WHERE id = ?",
                (new_id,),
            ).fetchone()
        assert row is not None
        assert row["name"] == "Col Check"
        assert row["investment_type"] == "mutual_funds"
        assert row["invested_paise"] == 1
        assert row["current_value_paise"] == 2
        assert row["as_of_date"] == "2026-05-31"
        assert row["units"] == 1.25
        assert row["buy_price_paise"] == 80
        assert row["current_price_paise"] == 160
        assert row["notes"] == "note"

    def test_the_ddl_columns_are_the_ones_the_repository_names(self) -> None:
        """The INSERT column list and the values tuple cannot drift apart."""
        import inspect
        import re

        from src.repositories.investment_repository import InvestmentRepository

        source = inspect.getsource(InvestmentRepository.create)
        columns = re.search(r"columns = \((.*?)\)", source, re.DOTALL)
        assert columns is not None
        named = re.findall(r'"(\w+)"', columns.group(1))

        schema_source = (
            __import__("pathlib").Path(__file__).resolve().parents[3]
            / "src"
            / "core"
            / "db"
            / "schema.py"
        ).read_text()
        ddl = re.search(r"CREATE TABLE IF NOT EXISTS investments \((.*?)\n\);", schema_source, re.DOTALL)
        assert ddl is not None, "investments DDL not found"
        ddl_columns = {
            line.strip().split()[0]
            for line in ddl.group(1).strip().splitlines()
            if line.strip()
        }
        for column in named:
            assert column in ddl_columns, f"{column} is not a column on investments"

    def test_round_trip_through_the_repository(self, finance_db: Any) -> None:
        from src.repositories.investment_repository import InvestmentRepository

        db = str(finance_db.db_path)
        repository = InvestmentRepository(db)
        new_id = repository.create(
            name="Round Trip",
            investment_type="debt",
            invested_paise=500000,
            current_value_paise=510000,
            as_of_date="2026-06-30",
            units=3.0,
            buy_price_paise=166666,
            current_price_paise=170000,
            notes="note",
        )
        row = repository.get_by_id(new_id)
        assert row is not None
        assert row["name"] == "Round Trip"
        assert row["investment_type"] == "debt"
        assert row["invested_paise"] == 500000
        assert row["current_value_paise"] == 510000
        assert row["as_of_date"] == "2026-06-30"
        assert row["units"] == 3.0
        assert row["buy_price_paise"] == 166666
        assert row["current_price_paise"] == 170000
        assert row["notes"] == "note"

    def test_create_signature_only_offers_persistable_fields(self) -> None:
        import inspect

        from src.repositories.investment_repository import InvestmentRepository

        params = set(inspect.signature(InvestmentRepository.create).parameters)
        for nonexistent in (
            "platform",
            "purchase_date",
            "maturity_date",
            "linked_account_id",
        ):
            assert nonexistent not in params, (
                f"{nonexistent} is not a column on the investments table"
            )

    def test_service_signature_matches_the_router_contract(self) -> None:
        import inspect

        from src.routers.investments import InvestmentCreate
        from src.services.investment_service import InvestmentService

        create_params = set(
            inspect.signature(InvestmentService.create_investment).parameters
        )
        for field in InvestmentCreate.model_fields:
            assert field in create_params, (
                f"the router accepts {field} but the service cannot pass it, so "
                f"the field is accepted and then silently dropped"
            )


class TestFullMutationChain:
    """user action -> API -> DB -> response -> cache source -> visible UI data."""

    def test_created_investment_appears_in_the_portfolio_read(
        self, client: TestClient
    ) -> None:
        """The mutation must be visible to the query the UI invalidates."""
        before = client.get("/api/v1/investments").json()["investment_count"]

        created = client.post("/api/v1/investments", json=VALID_PAYLOAD)
        assert created.status_code == 200, created.text

        after_response = client.get("/api/v1/investments")
        assert after_response.status_code == 200
        after = after_response.json()

        assert after["investment_count"] == before + 1
        assert after["total_invested_paise"] >= 100000

        new_id = created.json()["id"]
        summaries = {item["id"]: item for item in after["investments"]}
        assert new_id in summaries, (
            "the created investment is missing from the portfolio read the UI "
            "renders"
        )
        summary = summaries[new_id]
        assert summary["name"] == "Nifty Index Fund"
        assert summary["invested_paise"] == 100000
        assert summary["current_value_paise"] == 125000
        assert summary["returns_paise"] == 25000
        assert summary["returns_percentage"] == 25.0

    def test_persisted_row_satisfies_the_ddl_constraints(
        self, client: TestClient, finance_db: Any
    ) -> None:
        response = client.post("/api/v1/investments", json=VALID_PAYLOAD)
        assert response.status_code == 200, response.text
        new_id = response.json()["id"]

        with get_connection_context(str(finance_db.db_path)) as conn:
            row = conn.execute(
                "SELECT name, investment_type, invested_paise, current_value_paise, "
                "as_of_date, is_active FROM investments WHERE id = ?",
                (int(new_id),),
            ).fetchone()
        assert row is not None
        assert row["name"] == "Nifty Index Fund"
        assert row["investment_type"] == "mutual_funds"
        assert row["invested_paise"] == 100000
        assert row["current_value_paise"] == 125000
        assert row["as_of_date"]
        assert row["is_active"] == 1

    def test_update_and_delete_still_work(self, client: TestClient) -> None:
        created = client.post("/api/v1/investments", json=VALID_PAYLOAD)
        assert created.status_code == 200
        new_id = created.json()["id"]

        updated = client.put(
            f"/api/v1/investments/{new_id}",
            json={"current_value_paise": 130000, "notes": "marked up"},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["current_value_paise"] == 130000

        deleted = client.delete(f"/api/v1/investments/{new_id}")
        assert deleted.status_code == 200, deleted.text
        assert deleted.json()["success"] is True

        remaining = client.get("/api/v1/investments").json()["investment_count"]
        assert all(
            item["id"] != new_id for item in client.get("/api/v1/investments").json()["investments"]
        )
        assert remaining >= 0


class TestValidationStillRejectsBadInput:
    def test_missing_required_field_is_422(self, client: TestClient) -> None:
        response = client.post("/api/v1/investments", json={"name": "X"})
        assert response.status_code == 422

    def test_non_integer_paise_is_422(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/investments",
            json={**VALID_PAYLOAD, "invested_paise": 100.5},
        )
        assert response.status_code == 422


def test_isolated_database_is_used(finance_db: Any) -> None:
    """Guard against the test silently hitting a shared database."""
    assert str(finance_db.db_path).endswith(".db")