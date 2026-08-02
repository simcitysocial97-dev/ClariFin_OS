"""Account management endpoints.

All endpoints include request timing and structured error logging.
All monetary values in integer paise, all dates in ISO-8601 format.

Follows the same pattern as credit_cards.py and loans.py - no FinanceDB import,
no calculation logic, pure HTTP delegation to AccountService.
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Query

from src.core.dtos.accounts_dto import (
    AccountAnalyticsDTO,
    AccountDetailDTO,
    AccountLinkDTO,
    BalanceSnapshotDTO,
    InstitutionDTO,
)
from src.errors import NotFoundError
from src.models.account import (
    AccountCreateRequest,
    AccountUpdateRequest,
)
from src.models.account_balance import BalanceSnapshotRequest
from src.models.account_link import AccountLinkRequest
from src.models.institution import (
    InstitutionCreateRequest,
    InstitutionUpdateRequest,
)
from src.services.account_service import AccountService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["accounts"])


def _timed_log(
    endpoint: str,
    account_id: str | int | None,
    duration_ms: float,
    success: bool = True,
    error: str | None = None,
) -> None:
    """Emit structured timing log for account endpoints."""
    log_data = {
        "type": "account_request",
        "endpoint": endpoint,
        "account_id": account_id,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning(
            "[ACCOUNT] %s | account_id=%s | %.0fms | FAIL: %s",
            endpoint,
            account_id,
            duration_ms,
            error,
        )
    else:
        logger.info(
            "[ACCOUNT] %s | account_id=%s | %.0fms", endpoint, account_id, duration_ms
        )


# ============================================================
# Account CRUD Endpoints
# ============================================================


@router.get("/accounts", response_model=list[AccountDetailDTO])
def list_accounts() -> list[AccountDetailDTO]:
    """Get all active accounts via AccountService."""
    start = time.monotonic()
    service = AccountService()
    accounts = service.list_accounts()
    result = [
        AccountDetailDTO(
            id=acc["id"],
            name=acc["name"],
            type=acc["account_type"],
            institution=acc["bank"],
            balance_paise=acc["balance_paise"],
            status="active" if acc.get("is_active", True) else "inactive",
            account_number_last4=acc.get("account_number_last4"),
            opened_date=acc.get("created_at"),
            closed_date=(
                acc.get("updated_at") if not acc.get("is_active", True) else None
            ),
            notes=acc.get("notes"),
        )
        for acc in accounts
    ]
    _timed_log("GET /accounts", None, (time.monotonic() - start) * 1000)
    return result


@router.post("/accounts")
def create_account(request: AccountCreateRequest) -> dict[str, Any]:
    """Create a new account via AccountService."""
    start = time.monotonic()
    service = AccountService()

    created = service.create_account(
        name=request.name,
        bank=request.bank,
        account_type=request.account_type,
        balance_paise=request.balance_paise,
        account_number_last4=request.account_number_last4,
        notes=request.notes,
    )
    created_id = created.get("id") if created else None
    _timed_log("POST /accounts", created_id, (time.monotonic() - start) * 1000)
    return {"success": True, "account_id": created_id}


@router.get("/accounts/{account_id}", response_model=AccountDetailDTO)
def get_account(account_id: int | str) -> AccountDetailDTO:
    """Get account details via AccountService."""
    start = time.monotonic()
    service = AccountService()
    try:
        account = service.get_account(account_id)
        if not account:
            _timed_log(
                "GET /accounts/{id}",
                account_id,
                (time.monotonic() - start) * 1000,
                success=False,
                error="Not found",
            )
            raise NotFoundError(f"Account {account_id} not found")
        result = AccountDetailDTO(
            id=account["id"],
            name=account["name"],
            type=account["account_type"],
            institution=account["bank"],
            balance_paise=account["balance_paise"],
            status="active" if account.get("is_active", True) else "inactive",
            account_number_last4=account.get("account_number_last4"),
            opened_date=account.get("created_at"),
            closed_date=(
                account.get("updated_at")
                if not account.get("is_active", True)
                else None
            ),
            notes=account.get("notes"),
        )
        _timed_log("GET /accounts/{id}", account_id, (time.monotonic() - start) * 1000)
        return result
    except ValueError as e:
        _timed_log(
            "GET /accounts/{id}",
            account_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise NotFoundError(str(e)) from e


@router.put("/accounts/{account_id}")
def update_account(
    account_id: int | str,
    request: AccountUpdateRequest,
) -> dict[str, Any]:
    """Update account via AccountService."""
    start = time.monotonic()
    service = AccountService()

    update_data: dict[str, Any] = {}
    if request.name is not None:
        update_data["name"] = request.name
    if request.bank is not None:
        update_data["bank"] = request.bank
    if request.account_type is not None:
        update_data["account_type"] = request.account_type
    if request.balance_paise is not None:
        update_data["balance_paise"] = request.balance_paise
    if request.account_number_last4 is not None:
        update_data["account_number_last4"] = request.account_number_last4
    if request.notes is not None:
        update_data["notes"] = request.notes

    updated = service.update_account(account_id, **update_data)
    if not updated:
        _timed_log(
            "PUT /accounts/{id}",
            account_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error="Not found",
        )
        raise NotFoundError(f"Account {account_id} not found")
    _timed_log("PUT /accounts/{id}", account_id, (time.monotonic() - start) * 1000)
    return {"success": True}


@router.delete("/accounts/{account_id}")
def deactivate_account(account_id: int | str) -> dict[str, Any]:
    """Soft delete account via AccountService."""
    start = time.monotonic()
    service = AccountService()

    success = service.deactivate_account(account_id)
    if not success:
        _timed_log(
            "DELETE /accounts/{id}",
            account_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error="Not found",
        )
        raise NotFoundError(f"Account {account_id} not found")
    _timed_log("DELETE /accounts/{id}", account_id, (time.monotonic() - start) * 1000)
    return {"success": True}


# ============================================================
# Balance Snapshot Endpoints
# ============================================================


@router.post("/accounts/{account_id}/balance-history")
def insert_balance_snapshot(
    account_id: int | str,
    request: BalanceSnapshotRequest,
) -> dict[str, Any]:
    """Insert a balance snapshot for an account."""
    start = time.monotonic()
    service = AccountService()

    snapshot_id = service.insert_balance_snapshot(
        account_id=str(account_id),
        balance_paise=request.balance_paise,
        date_iso=request.date_iso,
        source=request.source,
    )

    # Fetch the created snapshot
    snapshot = service.get_balance_history(str(account_id), limit=1)
    if snapshot:
        result = {
            "id": str(snapshot[0]["id"]),
            "account_id": str(snapshot[0]["account_id"]),
            "balance_paise": snapshot[0]["balance_paise"],
            "date_iso": snapshot[0].get("date_iso"),
            "source": snapshot[0].get("source"),
            "created_at": snapshot[0].get("created_at"),
        }
        _timed_log(
            "POST /accounts/{id}/balance-history",
            account_id,
            (time.monotonic() - start) * 1000,
        )
        return {"success": True, "snapshot_id": snapshot_id, "snapshot": result}
    _timed_log(
        "POST /accounts/{id}/balance-history",
        account_id,
        (time.monotonic() - start) * 1000,
        success=False,
        error="Failed to create snapshot",
    )
    raise NotFoundError("Failed to create balance snapshot")


@router.get(
    "/accounts/{account_id}/balance-history", response_model=list[BalanceSnapshotDTO]
)
def get_balance_history(
    account_id: int | str,
    limit: int = Query(90, ge=1, le=365),
) -> list[BalanceSnapshotDTO]:
    """Get balance history for an account."""
    start = time.monotonic()
    service = AccountService()

    history = service.get_balance_history(str(account_id), limit)
    result = [
        BalanceSnapshotDTO(
            id=str(h["id"]),
            account_id=str(h["account_id"]),
            balance_paise=h["balance_paise"],
            date_iso=h.get("date_iso"),
            source=h.get("source"),
            created_at=h.get("created_at"),
        )
        for h in history
    ]
    _timed_log(
        "GET /accounts/{id}/balance-history",
        account_id,
        (time.monotonic() - start) * 1000,
    )
    return result


@router.get(
    "/accounts/{account_id}/balance-history/latest", response_model=BalanceSnapshotDTO
)
def get_latest_balance(account_id: int | str) -> BalanceSnapshotDTO:
    """Get the most recent balance snapshot for an account."""
    start = time.monotonic()
    service = AccountService()

    snapshot = service.get_latest_balance(str(account_id))
    if not snapshot:
        _timed_log(
            "GET /accounts/{id}/balance-history/latest",
            account_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error="No balance history",
        )
        raise NotFoundError(f"No balance history for account {account_id}")

    result = BalanceSnapshotDTO(
        id=str(snapshot["id"]),
        account_id=str(snapshot["account_id"]),
        balance_paise=snapshot["balance_paise"],
        date_iso=snapshot.get("date_iso"),
        source=snapshot.get("source"),
        created_at=snapshot.get("created_at"),
    )
    _timed_log(
        "GET /accounts/{id}/balance-history/latest",
        account_id,
        (time.monotonic() - start) * 1000,
    )
    return result


# ============================================================
# Analytics Endpoints
# ============================================================


@router.get("/accounts/{account_id}/analytics", response_model=AccountAnalyticsDTO)
def get_account_analytics(account_id: int | str) -> AccountAnalyticsDTO:
    """Get account analytics via AccountService."""
    start = time.monotonic()
    service = AccountService()

    # Get analytics metrics from service
    avg_balance = service.calculate_average_balance(str(account_id))
    balance_change = service.calculate_balance_change(str(account_id))
    growth = service.calculate_balance_growth(str(account_id))
    trend = service.calculate_balance_trend(str(account_id))
    velocity = service.calculate_balance_velocity(str(account_id))

    response = AccountAnalyticsDTO(
        average_balance_paise=avg_balance,
        balance_change_paise=balance_change,
        balance_growth_bps=growth,
        trend=trend,
        velocity_paise_per_day=velocity,
    )

    _timed_log(
        "GET /accounts/{id}/analytics", account_id, (time.monotonic() - start) * 1000
    )
    return response


@router.get("/accounts/{account_id}/metrics")
def get_account_metrics(account_id: int | str) -> dict[str, Any]:
    """Get comprehensive account metrics via AccountService."""
    start = time.monotonic()
    service = AccountService()

    try:
        metrics = service.get_account_metrics(str(account_id))
        _timed_log(
            "GET /accounts/{id}/metrics", account_id, (time.monotonic() - start) * 1000
        )
        return metrics
    except ValueError as e:
        _timed_log(
            "GET /accounts/{id}/metrics",
            account_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise NotFoundError(str(e)) from e


@router.get("/accounts/{account_id}/status")
def get_account_status(account_id: int | str) -> dict[str, str]:
    """Get account status via AccountService."""
    start = time.monotonic()
    service = AccountService()

    try:
        status = service.get_account_status(str(account_id))
        _timed_log(
            "GET /accounts/{id}/status", account_id, (time.monotonic() - start) * 1000
        )
        return {"status": status}
    except ValueError as e:
        _timed_log(
            "GET /accounts/{id}/status",
            account_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise NotFoundError(str(e)) from e


@router.get("/accounts/{account_id}/dormancy")
def get_account_dormancy(account_id: int | str) -> dict[str, Any]:
    """Check if account is dormant via AccountService."""
    start = time.monotonic()
    service = AccountService()

    # Get dormancy info from service
    is_dormant = service.is_account_dormant(str(account_id), threshold_days=365)
    days = service.get_days_since_activity(str(account_id))

    _timed_log(
        "GET /accounts/{id}/dormancy", account_id, (time.monotonic() - start) * 1000
    )
    return {"dormant": is_dormant, "days_since_activity": days}


# ============================================================
# Institution Endpoints
# ============================================================


@router.get("/institutions", response_model=list[InstitutionDTO])
def list_institutions() -> list[InstitutionDTO]:
    """Get all institutions via AccountService."""
    start = time.monotonic()
    service = AccountService()

    institutions = service.list_institutions()
    result = [
        InstitutionDTO(
            id=inst["id"],
            name=inst["name"],
            institution_type=inst["institution_type"],
            interest_rate_bps=inst.get("interest_rate_bps"),
            supported_features_json=inst.get("supported_features_json"),
            created_at=inst.get("created_at"),
            updated_at=inst.get("updated_at"),
        )
        for inst in institutions
    ]
    _timed_log("GET /institutions", None, (time.monotonic() - start) * 1000)
    return result


@router.post("/institutions")
def create_institution(request: InstitutionCreateRequest) -> dict[str, Any]:
    """Create a new institution via AccountService."""
    start = time.monotonic()
    service = AccountService()

    institution_id = service.create_institution(
        institution_id=request.institution_id,
        name=request.name,
        institution_type=request.institution_type,
        interest_rate_bps=request.interest_rate_bps,
        supported_features_json=request.supported_features_json,
    )
    _timed_log("POST /institutions", institution_id, (time.monotonic() - start) * 1000)
    return {"success": True, "institution_id": institution_id}


@router.get("/institutions/{institution_id}", response_model=InstitutionDTO)
def get_institution(institution_id: str) -> InstitutionDTO:
    """Get institution details via AccountService."""
    start = time.monotonic()
    service = AccountService()

    try:
        institution = service.get_institution(institution_id)
        if not institution:
            _timed_log(
                "GET /institutions/{id}",
                institution_id,
                (time.monotonic() - start) * 1000,
                success=False,
                error="Not found",
            )
            raise NotFoundError(f"Institution {institution_id} not found")

        result = InstitutionDTO(
            id=institution["id"],
            name=institution["name"],
            institution_type=institution["institution_type"],
            interest_rate_bps=institution.get("interest_rate_bps"),
            supported_features_json=institution.get("supported_features_json"),
            created_at=institution.get("created_at"),
            updated_at=institution.get("updated_at"),
        )
        _timed_log(
            "GET /institutions/{id}", institution_id, (time.monotonic() - start) * 1000
        )
        return result
    except ValueError as e:
        _timed_log(
            "GET /institutions/{id}",
            institution_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise NotFoundError(str(e)) from e


@router.put("/institutions/{institution_id}")
def update_institution(
    institution_id: str,
    request: InstitutionUpdateRequest,
) -> dict[str, Any]:
    """Update institution via AccountService."""
    start = time.monotonic()
    service = AccountService()

    update_data: dict[str, Any] = {}
    if request.name is not None:
        update_data["name"] = request.name
    if request.institution_type is not None:
        update_data["institution_type"] = request.institution_type
    if request.interest_rate_bps is not None:
        update_data["interest_rate_bps"] = request.interest_rate_bps
    if request.supported_features_json is not None:
        update_data["supported_features_json"] = request.supported_features_json

    updated = service.update_institution(institution_id, **update_data)
    if not updated:
        _timed_log(
            "PUT /institutions/{id}",
            institution_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error="Not found",
        )
        raise NotFoundError(f"Institution {institution_id} not found")

    _timed_log(
        "PUT /institutions/{id}", institution_id, (time.monotonic() - start) * 1000
    )
    return {"success": True}


# ============================================================
# Account Linking Endpoints
# ============================================================


@router.post("/accounts/{account_id}/links")
def link_accounts(
    account_id: int | str,
    request: AccountLinkRequest,
) -> dict[str, Any]:
    """Create a link between two accounts via AccountService."""
    start = time.monotonic()
    service = AccountService()

    try:
        success = service.link_accounts(
            primary_account_id=str(account_id),
            linked_account_id=request.linked_account_id,
            relationship_type=request.relationship_type,
        )
        _timed_log(
            "POST /accounts/{id}/links", account_id, (time.monotonic() - start) * 1000
        )
        return {"success": success}
    except ValueError as e:
        _timed_log(
            "POST /accounts/{id}/links",
            account_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error=str(e),
        )
        raise NotFoundError(str(e)) from e


@router.delete("/accounts/{account_id}/links/{linked_account_id}")
def unlink_accounts(
    account_id: int | str,
    linked_account_id: int | str,
) -> dict[str, Any]:
    """Remove a link between two accounts via AccountService."""
    start = time.monotonic()
    service = AccountService()

    success = service.unlink_accounts(str(account_id), str(linked_account_id))
    if not success:
        _timed_log(
            "DELETE /accounts/{id}/links/{linked_id}",
            account_id,
            (time.monotonic() - start) * 1000,
            success=False,
            error="Link not found",
        )
        raise NotFoundError("Link not found")

    _timed_log(
        "DELETE /accounts/{id}/links/{linked_id}",
        account_id,
        (time.monotonic() - start) * 1000,
    )
    return {"success": True}


@router.get("/accounts/{account_id}/links", response_model=list[AccountLinkDTO])
def get_linked_accounts(account_id: int | str) -> list[AccountLinkDTO]:
    """Get all accounts linked to the given account via AccountService."""
    start = time.monotonic()
    service = AccountService()

    links = service.get_linked_accounts(str(account_id))
    result = [
        AccountLinkDTO(
            id=str(link["id"]),
            primary_account_id=str(link["primary_account_id"]),
            linked_account_id=str(link["linked_account_id"]),
            relationship_type=link["relationship_type"],
            created_at=link.get("created_at"),
        )
        for link in links
    ]
    _timed_log(
        "GET /accounts/{id}/links", account_id, (time.monotonic() - start) * 1000
    )
    return result
