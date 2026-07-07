"""Transaction enrichment utilities."""
from typing import Any

from .formatting import clean_description, format_date_display, format_inr
from .parsing import parse_date


def enrich_transaction(txn: dict[str, Any]) -> dict[str, Any]:
    """
    Enrich transaction with formatted fields and metadata.

    Args:
        txn: Raw transaction dict from database

    Returns:
        Enriched transaction dict with display fields
    """
    enriched = txn.copy()

    # Format amount for display
    if "amount" in enriched:
        enriched["amount_formatted"] = format_inr(float(enriched["amount"]))

    # Format date for display
    if "date" in enriched:
        enriched["date_formatted"] = format_date_display(enriched["date"])

    # Clean description
    if "description" in enriched:
        enriched["description_clean"] = clean_description(enriched["description"])

    # Add parsed date object
    if "date" in enriched:
        enriched["date_parsed"] = parse_date(enriched["date"])

    return enriched
