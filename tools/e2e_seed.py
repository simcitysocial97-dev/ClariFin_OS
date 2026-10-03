#!/usr/bin/env python3
# tools/e2e_seed.py
"""Canonical E2E fixture seed — populates backend SQLite via the API path.

WHY THIS EXISTS
---------------
M10 recorded (`docs/audits/m10-agent3-04-remaining-issues.md` #21) that this
script "cannot seed anything": every route it called 404'd because the
registered product surface is `/api/v1/*`, not `/api/*`. A fresh worktree
therefore had an empty database, every financial workspace rendered in its
empty state, and no chart could be validated against real data. M10 Agent 3
had to seed by hand and recorded the recipe in
`docs/audits/m10-agent3-03-ui-and-charts.md` §3.7.

This file IS that recipe, mechanised. It seeds only through the canonical
`/api/v1/*` HTTP surface — never direct SQL, never Zustand/localStorage
writes — which is the standing M9 constraint. It introduces no second
seeding framework: the product's own routers, Pydantic models and import
pipeline are the only writers.

REUSE, NOT A NEW FRAMEWORK
--------------------------
Investigated before writing (M11 Task 18):
  * `backend/tests/fixtures/seed.py` — 5 rows of raw SQL via
    `get_connection_context`. It is a *pytest* fixture, writes the database
    directly (violating the API-path constraint), and is far too thin to
    drive a 6-month chart. Not reusable.
  * `backend/tests/fixtures/factories.py` / `builders.py` — pure-Python
    dict builders with no database and no HTTP. Unit-test helpers, not an
    E2E seeder, and they live under `backend/tests/`.
  * `backend/tests/fixtures/database.py` — the session-scoped
    `_pristine_db_template` schema builder. Reused implicitly: entering the
    app's lifespan runs the same migration path, so a fresh database is
    created with the canonical schema.
  * No backend seed/demo endpoint exists (verified against the full OpenAPI
    route table, 164 paths). None was added — the product surface is
    sufficient.

DETERMINISM
-----------
The dataset is a fixed, ordered CSV plus fixed account/loan/investment/card
records, all values literal in this file. Nothing is derived from the clock,
the filesystem, the network, `random`, or `uuid`. Seeding a fresh database
twice produces byte-identical read-back, which `--json` exposes as a
`fingerprint` field so a regression test can assert equality directly.

  python -m tools.e2e_seed --db /tmp/a.db --reset --json > run1.json
  python -m tools.e2e_seed --db /tmp/b.db --reset --json > run2.json
  diff run1.json run2.json    # only `database` (the path) may differ

The `database` field is the resolved path and is the ONLY intentionally
machine-dependent value; `--assert-deterministic` excludes it.

Usage
-----
  PYTHONPATH=backend .venv/bin/python tools/e2e_seed.py --reset
  PYTHONPATH=backend .venv/bin/python tools/e2e_seed.py --db /tmp/e2e.db --reset
  PYTHONPATH=backend .venv/bin/python tools/e2e_seed.py --db /tmp/e2e.db \
      --reset --json --assert-deterministic

Against an already-running server instead of in-process:
  PYTHONPATH=backend .venv/bin/python tools/e2e_seed.py --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))

# The canonical product surface. M10 finding #21: `/api/*` is unregistered.
API = "/api/v1"

# The canonical CSV header the import pipeline accepts
# (docs/audits/m10-agent3-03-ui-and-charts.md §3.7). Six months of data so
# that trend charts (cashflow, net worth) have more than one point.
SEED_CSV = """date,description,amount,type,category
2025-01-15,Salary Credit,50000,credit,salary
2025-01-16,UPI Payment - Amazon,2999,debit,shopping
2025-01-17,ATM Withdrawal,5000,debit,cash
2025-01-18,Netflix Subscription,649,debit,entertainment
2025-01-20,Grocery Store,1500,debit,groceries
2025-01-25,Electricity Bill,1200,debit,utilities
2025-02-01,Salary Credit,52000,credit,salary
2025-02-05,UPI Payment - Swiggy,450,debit,dining
2025-02-10,Mutual Fund SIP,10000,debit,investment
2025-02-14,Airport Taxi,980,debit,travel
2025-02-18,Grocery Store,1750,debit,groceries
2025-02-22,Netflix Subscription,649,debit,entertainment
2025-03-01,Salary Credit,52000,credit,salary
2025-03-04,UPI Payment - Amazon,3450,debit,shopping
2025-03-08,Restaurant Dinner,2240,debit,dining
2025-03-12,Fuel,2100,debit,transport
2025-03-16,Mobile Recharge,799,debit,utilities
2025-03-20,Grocery Store,1900,debit,groceries
2025-03-25,Netflix Subscription,649,debit,entertainment
2025-04-01,Salary Credit,54000,credit,salary
2025-04-03,UPI Payment - Swiggy,610,debit,dining
2025-04-09,Mutual Fund SIP,10000,debit,investment
2025-04-15,Pharmacy,540,debit,health
2025-04-19,Grocery Store,2100,debit,groceries
2025-04-24,ATM Withdrawal,3000,debit,cash
2025-05-01,Salary Credit,54000,credit,salary
2025-05-06,UPI Payment - Amazon,2899,debit,shopping
2025-05-11,Electricity Bill,1450,debit,utilities
2025-05-17,Restaurant Dinner,1980,debit,dining
2025-05-21,Grocery Store,1750,debit,groceries
2025-05-28,Flight Booking,6500,debit,travel
2025-06-01,Salary Credit,55000,credit,salary
2025-06-05,UPI Payment - Swiggy,520,debit,dining
2025-06-10,Mutual Fund SIP,10000,debit,investment
2025-06-14,Mobile Recharge,799,debit,utilities
2025-06-18,Grocery Store,1850,debit,groceries
2025-06-24,Netflix Subscription,699,debit,entertainment
"""

# Accounts. NOTE: `balance_paise` has `minimum: 0.0`, so an opening balance
# can never be negative — a liability belongs to the credit-card resource,
# not to a negative account row. The previous version of this script sent
# `{"type": ..., "bank_id": ..., "balance": ...}`, which is not the
# `AccountCreateRequest` schema at all and is rejected with 422.
SEED_ACCOUNTS: list[dict[str, Any]] = [
    {
        "name": "Primary Savings",
        "account_type": "savings",
        "bank": "Test Bank",
        "balance_paise": 5_000_000,
        "account_number_last4": "1234",
    },
    {
        "name": "Salary Current",
        "account_type": "current",
        "bank": "Test Bank",
        "balance_paise": 750_000,
        "account_number_last4": "5678",
    },
    {
        "name": "Rewards Card Account",
        "account_type": "credit_card",
        "bank": "Test Bank",
        "balance_paise": 0,
        "account_number_last4": "9012",
    },
]

SEED_INSTITUTIONS: list[dict[str, Any]] = [
    {
        "institution_id": "TESTBANK",
        "name": "Test Bank",
        "institution_type": "BANK",
        "interest_rate_bps": 350,
    }
]

SEED_LOANS: list[dict[str, Any]] = [
    {
        "name": "Home Loan",
        "lender": "Test Bank",
        "loan_type": "home",
        "principal_paise": 25_000_000,
        "outstanding_paise": 23_000_000,
        "rate_bps": 850,
        "tenure_months": 240,
        "disbursed_date": "2023-04-01",
        "emi_paise": 205_000,
    }
]

# `bank` is validated against `src.models.credit_card.VALID_BANKS`.
SEED_CREDIT_CARDS: list[dict[str, Any]] = [
    {
        "name": "Rewards Card",
        "bank": "hdfc",
        "credit_limit_paise": 500_000,
        "annual_fee_paise": 5_000,
        "interest_rate_bps": 1800,
        "billing_day": 5,
        "due_day_offset": 21,
        "card_last4": "9012",
    }
]

SEED_INVESTMENTS: list[dict[str, Any]] = [
    {
        "name": "Index Fund",
        "investment_type": "mutual_funds",
        "invested_paise": 1_200_000,
        "current_value_paise": 1_485_000,
        "units": 120.0,
        "buy_price_paise": 10_000,
        "current_price_paise": 12_375,
        "as_of_date": "2025-06-30",
    },
    {
        "name": "Fixed Deposit",
        "investment_type": "fd",
        "invested_paise": 500_000,
        "current_value_paise": 530_000,
        "as_of_date": "2025-06-30",
    },
]

# Surfaces that are empty for a documented architectural reason, not because
# the fixture failed to reach them. Listed explicitly so that they are
# reported rather than silently ignored, and so that the day the underlying
# gap is closed this list must shrink and the test will fail until it does.
#
# `behaviour_patterns`: `GET /api/v1/behaviour/patterns` reads the
# `behaviour_patterns` table. Its only writer,
# `PatternRepository.create_pattern`
# (backend/src/repositories/pattern_repository.py:18), has ZERO callers in
# backend/src — no router, service, startup hook or job invokes it — so the
# table is never populated and the endpoint is structurally always `[]`.
# This is NOT fixable by seeding: writing the table directly would bypass
# the canonical /api/v1 path and create a second seeding framework, which
# the standing M9 constraint forbids. Reported to the backend owner.
KNOWN_EMPTY_SURFACES: dict[str, str] = {
    "behaviour_patterns": "behaviour_patterns table has no writer (dead write path)",
}

# Read-only surfaces the frontend actually renders. Each entry is
# (label, path, extractor) where extractor pulls a comparable scalar or
# container out of the response for the determinism fingerprint.
VERIFY_SURFACES: list[tuple[str, str]] = [
    ("dashboard", f"{API}/dashboard/summary"),
    ("accounts", f"{API}/accounts"),
    ("transactions", f"{API}/transactions"),
    ("cashflow", f"{API}/cashflow"),
    ("cashflow_monthly", f"{API}/cashflow/monthly"),
    ("cashflow_categories", f"{API}/cashflow/categories"),
    ("net_worth", f"{API}/net-worth"),
    ("forecast", f"{API}/forecast"),
    ("behaviour", f"{API}/behaviour"),
    ("behaviour_profile", f"{API}/behaviour/profile"),
    ("behaviour_wellness", f"{API}/behaviour/wellness-score"),
    ("behaviour_patterns", f"{API}/behaviour/patterns"),
    ("loans", f"{API}/loans"),
    ("investments", f"{API}/investments"),
    ("credit_cards", f"{API}/credit-cards"),
    ("overview", f"{API}/overview"),
    ("analytics", f"{API}/analytics"),
    ("categories", f"{API}/categories"),
]

# Platform-console surfaces. These answer from generated repo/runtime
# evidence, not from the seeded database, so they are verified for
# reachability and shape only and are never fingerprinted (they embed
# `generated_at`).
#
# Split by cost. The two deep entries run a full architectural/integrity scan
# and were MEASURED at 12.0 s and 25.4 s respectively on this host — 37.5 s,
# more than half the script's total runtime. They are also not E2E seed
# concerns: the same authorities are already gated by
# `python -m runtime.verify integrity`, which `run_runtime_verification.sh`
# runs as its own step. Duplicating them here bought nothing and made the
# tool unusable inside a `--timeout=30` test. They remain available via
# `--deep-platform`.
PLATFORM_SURFACES: list[str] = [
    "/platform/v1/status",
    "/platform/v1/capabilities",
    "/platform/v1/architecture/boundaries",
    "/platform/v1/verification",
    "/health",
    "/ready",
]

PLATFORM_SURFACES_DEEP: list[str] = [
    "/platform/v1/architecture/authorities",
    "/platform/v1/framework/integrity",
]

# `POST /api/v1/members` is not needed: the app's lifespan already creates
# the default member "Self" (id=1). The previous version of this script
# POSTed it unconditionally and died with
# `sqlite3.IntegrityError: UNIQUE constraint failed: members.name`.
DEFAULT_MEMBER = "Self"


class SeedError(RuntimeError):
    """Raised when a required seed or verification step fails."""


def _require(resp: Any, what: str) -> Any:
    if resp.status_code not in (200, 201):
        raise SeedError(f"{what} failed: HTTP {resp.status_code} {resp.text[:300]}")
    return resp


def _strip_volatile(value: Any) -> Any:
    """Drop keys whose values legitimately vary between identical runs.

    Every key here is a SERVER-GENERATED wall-clock or surrogate value, not
    seeded state. Nothing this script writes is ever stripped, so the
    fingerprint still covers the entire seeded dataset.

    `opened_date` was found empirically: two fresh runs 40 s apart produced
    `2026-10-02 15:04:58` and `2026-10-02 15:05:39` on identical input, which
    is what first proved the run was not yet deterministic.

    `id` is deliberately NOT stripped. Row identifiers are assigned by
    autoincrement from a fresh database and are therefore reproducible;
    including them makes the fingerprint sensitive to ID reassignment, which
    is a real regression signal rather than noise.
    """
    volatile = {
        "generated_at",
        "created_at",
        "updated_at",
        "opened_date",
        "run_id",
        "duration_seconds",
        "measured_at",
        "correlation_id",
    }
    if isinstance(value, dict):
        return {
            k: _strip_volatile(v) for k, v in sorted(value.items()) if k not in volatile
        }
    if isinstance(value, list):
        return [_strip_volatile(v) for v in value]
    return value


def _build_client(base_url: str | None) -> tuple[Any, Any]:
    """Return (client, closer).

    With `base_url` the script drives an already-running server over HTTP.
    Without it, it drives the ASGI app in-process via `TestClient`.

    The in-process path MUST enter the client's context manager: that runs
    the application lifespan, which is what creates/migrates the SQLite
    schema and seeds the default member. A bare `TestClient(app)` skips
    lifespan, the schema never exists, and the first write fails.
    """
    if base_url:
        import httpx

        return httpx.Client(base_url=base_url, timeout=120.0), None

    from fastapi.testclient import TestClient
    from src.api import app

    # raise_server_exceptions=False is REQUIRED, not cosmetic: with the
    # default True, TestClient re-raises the application's own exception
    # instead of letting the app's exception handler turn it into the 500
    # response a real HTTP client would receive. That would make one broken
    # endpoint abort the whole seed run instead of being reported alongside
    # the surfaces that do work.
    client = TestClient(app, raise_server_exceptions=False)
    client.__enter__()
    return client, client


def _ensure_member(client: Any) -> str:
    """Return the member name transactions are attributed to.

    Reuses the lifespan-seeded default member instead of re-creating it.
    """
    resp = _require(client.get(f"{API}/members"), "GET members")
    members = (resp.json() or {}).get("members") or []
    if any(m.get("name") == DEFAULT_MEMBER for m in members):
        return DEFAULT_MEMBER
    _require(
        client.post(
            f"{API}/members", json={"name": DEFAULT_MEMBER, "color": "#6366F1"}
        ),
        "POST members",
    )
    return DEFAULT_MEMBER


def _seed_accounts(client: Any, errors: list[str]) -> list[dict[str, Any]]:
    existing = {
        a.get("name")
        for a in (
            (_require(client.get(f"{API}/accounts"), "GET accounts").json()) or []
        )
    }
    created: list[dict[str, Any]] = []
    for payload in SEED_ACCOUNTS:
        if payload["name"] in existing:
            continue
        resp = client.post(f"{API}/accounts", json=payload)
        if resp.status_code in (200, 201):
            created.append(payload)
        else:
            errors.append(
                f"POST accounts {payload['name']}: "
                f"HTTP {resp.status_code} {resp.text[:160]}"
            )
    return created


def _seed_institutions(client: Any, errors: list[str]) -> int:
    n = 0
    for payload in SEED_INSTITUTIONS:
        resp = client.post(f"{API}/institutions", json=payload)
        if resp.status_code in (200, 201):
            n += 1
        elif resp.status_code == 409:
            continue  # already present — idempotent re-run
        else:
            errors.append(
                f"POST institutions {payload['institution_id']}: "
                f"HTTP {resp.status_code} {resp.text[:160]}"
            )
    return n


def _seed_transactions(client: Any, errors: list[str]) -> int:
    """Import the fixed CSV through the canonical import pipeline.

    `/api/v1/import/detect` discovers the column mapping (so the script
    never hard-codes a guess that could silently drift from the parser) and
    `/api/v1/import/execute` performs the write. This is the one import path
    M10 confirmed working.
    """
    detect = client.post(
        f"{API}/import/detect",
        files={"file": ("e2e_seed.csv", io.BytesIO(SEED_CSV.encode()), "text/csv")},
    )
    if detect.status_code != 200:
        errors.append(
            f"POST import/detect: HTTP {detect.status_code} {detect.text[:160]}"
        )
        return 0
    detected = (detect.json() or {}).get("detected_mapping") or {}
    mapping = {
        "date_column": detected.get("date_column") or "date",
        "description_column": detected.get("description_column") or "description",
        "amount_column": detected.get("amount_column") or "amount",
        "type_column": detected.get("type_column") or "type",
        "date_format": "%Y-%m-%d",
        "bank_name": "Test Bank",
    }
    execute = client.post(
        f"{API}/import/execute",
        json={"filename": "e2e_seed.csv", "mapping": mapping, "member": DEFAULT_MEMBER},
    )
    if execute.status_code != 200:
        errors.append(
            f"POST import/execute: HTTP {execute.status_code} {execute.text[:160]}"
        )
        return 0
    body = execute.json() or {}
    if not body.get("success"):
        errors.append(f"import/execute reported failure: {body}")
        return 0
    return int(body.get("count", 0))


def _seed_loans(client: Any, errors: list[str]) -> int:
    n = 0
    for payload in SEED_LOANS:
        resp = client.post(f"{API}/loans", json=payload)
        if resp.status_code in (200, 201):
            n += 1
        else:
            errors.append(
                f"POST loans {payload['name']}: HTTP {resp.status_code} {resp.text[:160]}"
            )
    return n


def _seed_credit_cards(client: Any, errors: list[str]) -> int:
    accounts = (_require(client.get(f"{API}/accounts"), "GET accounts").json()) or []
    by_name = {a.get("name"): a for a in accounts}
    n = 0
    for payload in SEED_CREDIT_CARDS:
        account = by_name.get("Rewards Card Account")
        if account is None:
            continue
        body = {**payload, "account_id": str(account.get("id"))}
        resp = client.post(f"{API}/credit-cards", json=body)
        if resp.status_code in (200, 201):
            n += 1
        else:
            errors.append(
                f"POST credit-cards {payload['name']}: "
                f"HTTP {resp.status_code} {resp.text[:160]}"
            )
    return n


def _seed_investments(client: Any, errors: list[str]) -> int:
    n = 0
    for payload in SEED_INVESTMENTS:
        resp = client.post(f"{API}/investments", json=payload)
        if resp.status_code in (200, 201):
            n += 1
        else:
            errors.append(
                f"POST investments {payload['name']}: "
                f"HTTP {resp.status_code} {resp.text[:160]}"
            )
    return n


def _verify(client: Any) -> dict[str, Any]:
    """Read back every surface the product renders and fingerprint it.

    Three outcomes are distinguished, because conflating them is exactly how
    this problem stayed hidden:

    * ``error`` — the endpoint itself failed (HTTP >= 400). That is a
      BACKEND defect, not a seeding defect. It is recorded and named rather
      than raised, so one broken endpoint cannot prevent the other 17
      surfaces from being seeded and verified.
    * ``empty`` — HTTP 200 but no data. That is a SEEDING defect: the
      fixture did not reach this surface. This is the empty-state condition
      M10 hit, and the whole point of this script is to make it impossible
      to mistake for a broken chart.
    * ``rows > 0`` — seeded and readable.
    """
    report: dict[str, Any] = {}
    for label, path in VERIFY_SURFACES:
        resp = client.get(path)
        if resp.status_code != 200:
            report[label] = {
                "path": path,
                "http_status": resp.status_code,
                "error": resp.text[:200],
                "rows": 0,
                "empty": False,
                "payload": None,
            }
            continue
        payload = _strip_volatile(resp.json())
        rows = _row_count(payload)
        report[label] = {
            "path": path,
            "http_status": resp.status_code,
            "rows": rows,
            "empty": rows == 0,
            "payload": payload,
        }
    return report


def _row_count(payload: Any) -> int:
    """Cardinality of a response, for empty-state detection.

    Recursive on purpose. An early version of this function only inspected
    top-level keys, which reported `cashflow` and `net-worth` as EMPTY even
    though they carried 37 transactions and a full asset/liability
    composition — their rows live under nested objects (`trend`,
    `composition.asset_breakdown`). A false "empty" is as damaging as a
    missed one: it is exactly the signal that tells an engineer a chart is
    broken when the data was never missing.

    Rule: the cardinality of a response is the largest list found anywhere
    inside it; if it contains no list at all, it is a scalar summary and is
    non-empty when it carries at least one non-zero number.
    """
    best = 0

    def walk(node: Any) -> None:
        nonlocal best
        if isinstance(node, list):
            best = max(best, len(node))
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for value in node.values():
                walk(value)

    walk(payload)
    if best:
        return best

    scalars: list[Any] = []

    def collect(node: Any) -> None:
        if isinstance(node, dict):
            for value in node.values():
                collect(value)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            scalars.append(node)

    collect(payload)
    if scalars:
        return sum(1 for v in scalars if v)
    return 1 if payload else 0


def _verify_platform(client: Any, deep: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {}
    paths = PLATFORM_SURFACES + (PLATFORM_SURFACES_DEEP if deep else [])
    for path in paths:
        resp = _require(client.get(path), f"GET {path}")
        body = resp.json() or {}
        report[path] = {
            "kind": body.get("kind"),
            "status": body.get("status"),
            "ok": bool(body),
        }
    return report


def _fingerprint(verification: dict[str, Any]) -> str:
    """Stable digest of every surface that responded.

    Surfaces that returned an HTTP error are excluded: their payload is a
    backend defect report, not seeded state, and folding a stack trace into
    the digest would make the determinism check compare error text instead
    of data. They are still listed by name in ``surfaces_erroring``.
    """
    comparable = {
        label: entry for label, entry in verification.items() if not entry.get("error")
    }
    canonical = json.dumps(comparable, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def seed(
    base_url: str | None = None,
    db_path: str | None = None,
    reset: bool = False,
    deep_platform: bool = False,
) -> dict[str, Any]:
    """Seed the canonical dataset and return a deterministic report."""
    if db_path:
        resolved = str(Path(db_path).expanduser().resolve())
        if reset:
            for suffix in ("", "-wal", "-shm"):
                candidate = Path(resolved + suffix)
                if candidate.exists():
                    candidate.unlink()
        # Must be set before the app resolves its database path.
        os.environ["FINANCE_DB_PATH"] = resolved
    else:
        resolved = os.environ.get("FINANCE_DB_PATH") or "data/finance.db"

    client, closer = _build_client(base_url)
    try:
        member = _ensure_member(client)
        # A write failure is a BACKEND defect, and it is recorded rather than
        # raised. Raising would destroy the report: one broken write endpoint
        # would leave the operator with no evidence about the 17 surfaces that
        # did work, which is the opposite of what this tool is for.
        errors: list[str] = []
        created_accounts = _seed_accounts(client, errors)
        institutions = _seed_institutions(client, errors)
        imported = _seed_transactions(client, errors)
        loans = _seed_loans(client, errors)
        cards = _seed_credit_cards(client, errors)
        investments = _seed_investments(client, errors)
        verification = _verify(client)
        platform = _verify_platform(client, deep=deep_platform)
    finally:
        if closer is not None:
            closer.__exit__(None, None, None)

    empty = sorted(label for label, r in verification.items() if r["empty"])
    erroring = sorted(label for label, r in verification.items() if r.get("error"))
    platform_erroring = sorted(p for p, r in platform.items() if not r["ok"])
    # An "empty" surface is only acceptable if its emptiness is documented.
    unexplained_empty = [label for label in empty if label not in KNOWN_EMPTY_SURFACES]
    return {
        "schema": "clarifin/e2e-seed/v1",
        "database": resolved,
        "mode": "http" if base_url else "in-process",
        "member": member,
        "written": {
            "accounts": len(created_accounts),
            "institutions": institutions,
            "transactions_imported": imported,
            "loans": loans,
            "credit_cards": cards,
            "investments": investments,
        },
        "surfaces_total": len(verification),
        "surfaces_empty": empty,
        "surfaces_empty_known": [
            label for label in empty if label in KNOWN_EMPTY_SURFACES
        ],
        "surfaces_empty_unexplained": unexplained_empty,
        "surfaces_erroring": erroring,
        "platform_erroring": platform_erroring,
        "write_errors": errors,
        "verification": verification,
        "platform": platform,
        "fingerprint": _fingerprint(verification),
    }


def _determinism_view(report: dict[str, Any]) -> dict[str, Any]:
    """Report with the machine-dependent database path removed."""
    return {k: v for k, v in report.items() if k != "database"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Seed deterministic E2E fixtures through the canonical /api/v1 path."
    )
    parser.add_argument(
        "--db",
        help="SQLite path to seed (sets FINANCE_DB_PATH). Default: backend default.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete the target database (and -wal/-shm) before seeding.",
    )
    parser.add_argument(
        "--base-url",
        help="Seed an already-running server over HTTP instead of in-process.",
    )
    parser.add_argument("--json", action="store_true", help="Emit the JSON report.")
    parser.add_argument(
        "--deep-platform",
        action="store_true",
        help=(
            "Also verify the two expensive platform scans "
            "(architecture/authorities ~12s, framework/integrity ~25s). "
            "Off by default: they duplicate the runtime.verify integrity gate "
            "and dominate this tool's runtime."
        ),
    )
    parser.add_argument(
        "--out",
        help="Write the JSON report to this file instead of stdout. Preferred for "
        "machine consumption: the application's own integrity scan writes "
        "'File not found: ...' lines to stdout, which would corrupt a "
        "stdout-only JSON stream.",
    )
    parser.add_argument(
        "--assert-deterministic",
        action="store_true",
        help="Fail unless every read-back surface is non-empty.",
    )
    args = parser.parse_args(argv)

    report = seed(
        base_url=args.base_url,
        db_path=args.db,
        reset=args.reset,
        deep_platform=args.deep_platform,
    )
    payload = _determinism_view(report) if args.assert_deterministic else report

    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2) + "\n")
    if args.json:
        print(json.dumps(payload, indent=2))

    if not (args.json or args.out):
        w = report["written"]
        print(f"database : {report['database']} ({report['mode']})")
        print(
            "seeded   : "
            f"{w['accounts']} accounts, {w['transactions_imported']} transactions, "
            f"{w['loans']} loans, {w['credit_cards']} cards, "
            f"{w['investments']} investments, {w['institutions']} institutions"
        )
        print(
            f"surfaces : {report['surfaces_total']} verified, "
            f"empty={report['surfaces_empty']}, erroring={report['surfaces_erroring']}"
        )
        print(
            f"platform : {len(report['platform'])} console surfaces, "
            f"erroring={report['platform_erroring']}"
        )
        print(f"fingerprint: {report['fingerprint']}")

    if not args.assert_deterministic:
        return 0

    failed = False
    if report["surfaces_empty_unexplained"]:
        print(
            "SEED CHECK FAILED: these surfaces returned HTTP 200 with no data and "
            "are not documented as structurally empty: "
            f"{report['surfaces_empty_unexplained']}",
            file=sys.stderr,
        )
        failed = True
    if report["surfaces_empty_known"]:
        print(
            "NOTE: documented structurally-empty surfaces "
            f"{report['surfaces_empty_known']} — see KNOWN_EMPTY_SURFACES.",
            file=sys.stderr,
        )
    if report["surfaces_erroring"]:
        print(
            "BACKEND CHECK FAILED: these surfaces returned an HTTP error "
            f"(product defect, not a seeding defect): {report['surfaces_erroring']}",
            file=sys.stderr,
        )
        failed = True
    if report["write_errors"]:
        print(
            "BACKEND CHECK FAILED: these seed writes were rejected "
            f"(product defect, not a seeding defect): {report['write_errors']}",
            file=sys.stderr,
        )
        failed = True
    if report["platform_erroring"]:
        print(
            "BACKEND CHECK FAILED: unreachable platform-console surfaces: "
            f"{report['platform_erroring']}",
            file=sys.stderr,
        )
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
