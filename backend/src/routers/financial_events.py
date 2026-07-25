"""Financial Events API router."""

from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query

from src.services.financial_events_service import FinancialEventsService

router = APIRouter(prefix="/api/financial-events", tags=["financial-events"])


@router.post("/", response_model=int)
def create_event(
    event_type: str,
    transaction_ids: list[int],
    account_id: str,
    amount_paise: int = 0,
    asset_change_paise: int = 0,
    liability_change_paise: int = 0,
    expense_paise: int = 0,
    income_paise: int = 0,
    outstanding_paise: int = 0,
    date_iso: str = "",
    category: str = "",
    sub_type: str | None = None,
    provider: str | None = None,
    confidence_bps: int = 0,
    household_id: str = "primary",
    owner_id: str = "self",
) -> int:
    """
    Create a FinancialEvent and persist it.
    Returns the database ID of the created event.
    """
    service = FinancialEventsService()
    try:
        return service.create_and_persist_event(
            event_type=event_type,
            transaction_ids=transaction_ids,
            account_id=account_id,
            amount_paise=amount_paise,
            asset_change_paise=asset_change_paise,
            liability_change_paise=liability_change_paise,
            expense_paise=expense_paise,
            income_paise=income_paise,
            outstanding_paise=outstanding_paise,
            date_iso=date_iso,
            category=category,
            sub_type=sub_type,
            provider=provider,
            confidence_bps=confidence_bps,
            household_id=household_id,
            owner_id=owner_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list)
def list_events(
    month_bucket: str | None = Query(None),
    household_id: str = Query("primary"),
) -> list[dict[str, Any]]:
    """
    List events, optionally filtered by month_bucket.
    Returns list of event dicts with link information.
    """
    service = FinancialEventsService()
    try:
        if month_bucket:
            return service.get_events_with_links(month_bucket, household_id)
        else:
            # Return all events (no month filter) using get_events_with_links
            return service.get_events_with_links("", household_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{event_id}", response_model=dict)
def get_event(event_id: int = Path(..., description="Event ID")) -> dict[str, Any]:
    """
    Get a specific event by ID.
    """
    service = FinancialEventsService()
    try:
        # Fetch all events and filter by ID (repository has no single-event getter)
        all_events = service.event_repo.get_events_by_type("", "primary")
        event = next((e for e in all_events if e.get("id") == event_id), None)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
