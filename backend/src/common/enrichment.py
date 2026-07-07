"""Transaction enrichment utilities."""
from .formatting import clean_description, format_date_display, format_inr
from .parsing import get_weekday, parse_date


def enrich_transaction(txn: dict) -> dict:
    """Add computed fields to a transaction."""
    dt = parse_date(txn.get("date", ""))
    # Use stored amount_paise as primary source (avoids float precision issues)
    amount_paise = int(txn.get("amount_paise") or 0)
    amount = amount_paise / 100.0  # Derive float for display

    return {
        **txn,
        "parsed_date": dt.strftime("%Y-%m-%d") if dt else "",
        "date_display": format_date_display(txn.get("date", "")),
        "month_key": dt.strftime("%Y-%m") if dt else "",
        "weekday": get_weekday(txn.get("date", "")),
        "amount_display": format_inr(amount),
        "amount": amount,
        "amount_paise": amount_paise,  # Canonical paise field
        "description_display": clean_description(txn.get("description", "")),
    }