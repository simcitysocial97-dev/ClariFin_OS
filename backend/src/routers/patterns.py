"""Liquidity Pattern Management Endpoints.

API endpoints for managing liquidity provider/purpose patterns.
"""
from typing import Any

from fastapi import APIRouter, HTTPException

from src.repositories.liquidity_pattern_repository import LiquidityPatternRepository

router = APIRouter(prefix="/api/v1/patterns", tags=["patterns"])


@router.post("/confirm")
def confirm_pattern(pattern_id: int) -> dict[str, Any]:
    """
    Confirm a liquidity pattern as user-verified.

    Args:
        pattern_id: ID of the provider pattern to confirm.

    Returns:
        Success status.
    """
    repo = LiquidityPatternRepository()
    updated = repo.confirm_pattern(pattern_id)

    if not updated:
        raise HTTPException(status_code=404, detail="Pattern not found")

    return {"success": True, "pattern_id": pattern_id, "confirmed": True}


@router.post("/new")
def create_pattern(
    provider_name: str,
    description_pattern: str,
    fee_min_bps: int = 150,
    fee_max_bps: int = 400,
    review_fee_min_bps: int = 50,
    review_fee_max_bps: int = 800,
    typical_settlement_days: int = 2,
) -> dict[str, Any]:
    """
    Create a new liquidity provider pattern.

    Args:
        provider_name: Name of the provider (e.g., 'NewProvider').
        description_pattern: Regex pattern to match descriptions.
        fee_min_bps: Minimum fee in basis points for auto zone.
        fee_max_bps: Maximum fee in basis points for auto zone.
        review_fee_min_bps: Minimum fee for review zone.
        review_fee_max_bps: Maximum fee for review zone.
        typical_settlement_days: Expected settlement window in days.

    Returns:
        Created pattern ID.
    """
    repo = LiquidityPatternRepository()
    pattern_id = repo.insert_new_pattern(
        provider_name=provider_name,
        description_pattern=description_pattern,
        fee_min_bps=fee_min_bps,
        fee_max_bps=fee_max_bps,
        review_fee_min_bps=review_fee_min_bps,
        review_fee_max_bps=review_fee_max_bps,
        typical_settlement_days=typical_settlement_days,
    )

    return {"success": True, "pattern_id": pattern_id, "provider_name": provider_name}


@router.get("/providers")
def list_providers() -> dict[str, Any]:
    """Get all active liquidity provider patterns."""
    repo = LiquidityPatternRepository()
    patterns = repo.get_active_provider_patterns()
    return {"providers": patterns}


@router.get("/purposes")
def list_purposes() -> dict[str, Any]:
    """Get all active liquidity purpose patterns."""
    repo = LiquidityPatternRepository()
    patterns = repo.get_active_purpose_patterns()
    return {"purposes": patterns}