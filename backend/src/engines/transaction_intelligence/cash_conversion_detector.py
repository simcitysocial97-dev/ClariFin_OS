"""Cash Conversion Detector - Pure function for detecting liquidity extraction.

Detects when a debit transaction represents cash extracted via a provider
(CRED/Cheq/Spaid/NoBroker) into a savings/current account, with fee calculation.

No database access - all data is passed as parameters.
"""
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, cast


@dataclass(frozen=True)
class CashConversionResult:
    """Result from cash conversion detection.

    Attributes:
        matched_credit_transaction_id: ID of the matched credit transaction.
        provider_name: Name of the liquidity provider (or None for unknown).
        purpose: Matched purpose from purpose patterns (or None).
        zone: 'auto', 'review', or 'unmatched_provider'.
        confidence_bps: Confidence score in basis points (0-9900).
        fee_paise: Fee amount in paise.
        fee_bps: Fee percentage in basis points.
        settlement_days: Days between debit and credit.
        narrative: Human-readable explanation.
        match_reason: Why this matched.
    """
    matched_credit_transaction_id: int
    provider_name: str | None
    purpose: str | None
    zone: Literal["auto", "review", "unmatched_provider"]
    confidence_bps: int
    fee_paise: int
    fee_bps: int
    settlement_days: int
    narrative: str
    match_reason: str


# ============================================================
# Helper Functions
# ============================================================

def _parse_date_iso(date_iso: str) -> datetime | None:
    """Parse YYYY-MM-DD date string to datetime."""
    if not date_iso:
        return None
    try:
        return datetime.strptime(date_iso, "%Y-%m-%d")
    except ValueError:
        return None


def _date_difference_days(date_a: str, date_b: str) -> int:
    """Calculate difference in days between two ISO dates (credit - debit)."""
    dt_a = _parse_date_iso(date_a)
    dt_b = _parse_date_iso(date_b)

    if dt_a is None or dt_b is None:
        return 999  # Force out of window

    return (dt_b - dt_a).days  # Positive if credit is after debit


def _match_description_pattern(description: str, pattern: str) -> bool:
    """Check if description matches a regex pattern (case-insensitive)."""
    if not description or not pattern:
        return False
    try:
        return bool(re.search(pattern, description, re.IGNORECASE))
    except re.error:
        return False


def _match_purpose(description: str, purpose_patterns: list[dict[str, Any]]) -> str | None:
    """Match description against purpose patterns."""
    for pattern in purpose_patterns:
        purpose_val = pattern.get("purpose")
        if _match_description_pattern(description, pattern["description_pattern"]) and isinstance(purpose_val, str):
            return purpose_val
    return None


def _is_savings_or_current(account_type: str) -> bool:
    """Check if account type is savings or current."""
    return account_type in ("savings", "current")


def _calculate_fee_bps(debit_amount_paise: int, credit_amount_paise: int) -> int:
    """Calculate fee in basis points (1 bps = 0.01%)."""
    if debit_amount_paise <= 0:
        return 0
    fee_paise = debit_amount_paise - credit_amount_paise
    return int((fee_paise * 10000) / debit_amount_paise)


def _determine_zone(
    fee_bps: int,
    fee_min_bps: int,
    fee_max_bps: int,
    review_fee_min_bps: int,
    review_fee_max_bps: int,
) -> Literal["auto", "review"] | None:
    """
    Determine zone based on fee percentage.

    Returns:
        'auto' if fee within primary range (inclusive)
        'review' if fee within review range (inclusive, outside auto)
        None if fee outside all ranges (discard)
    """
    if fee_min_bps <= fee_bps <= fee_max_bps:
        return "auto"

    if review_fee_min_bps <= fee_bps <= review_fee_max_bps:
        return "review"

    return None


def _hungarian_inline(cost_matrix: list[list[float]]) -> list[tuple[int, int]]:
    """Inline Hungarian algorithm implementation."""
    n = len(cost_matrix)
    if n == 0:
        return []

    candidates: list[tuple[int, int, float]] = []
    for i in range(n):
        for j in range(n):
            if cost_matrix[i][j] < 1e8:
                candidates.append((i, j, cost_matrix[i][j]))

    if not candidates:
        return []

    candidates.sort(key=lambda x: (x[2], x[0], x[1]))

    assigned_debits: set[int] = set()
    assigned_credits: set[int] = set()
    assignments: list[tuple[int, int]] = []

    for i, j, _ in candidates:
        if i not in assigned_debits and j not in assigned_credits:
            assigned_debits.add(i)
            assigned_credits.add(j)
            assignments.append((i, j))

    return assignments


# ============================================================
# Core Detector Function
# ============================================================

# Type alias for candidate with zone info
_CandidateWithZone = dict[str, Any]  # {credit: dict, fee_paise: int, fee_bps: int, zone: Literal}


def detect(
    cc_debit_txn: dict[str, Any],
    candidate_credits: list[dict[str, Any]],
    provider_patterns: list[dict[str, Any]],
    purpose_patterns: list[dict[str, Any]],
    statement_row: dict[str, Any] | None = None,
) -> CashConversionResult | None:
    """
    Detect cash conversion (liquidity extraction) from a debit transaction.

    Args:
        cc_debit_txn: Debit transaction dict with id, description, amount_paise/debit, date_iso.
        candidate_credits: Credit transactions to match against (pre-filtered by service).
        provider_patterns: Active provider patterns for matching.
        purpose_patterns: Active purpose patterns for matching.
        statement_row: Optional statement for due date bonus (from service layer).

    Returns:
        CashConversionResult if valid conversion detected, None otherwise.
    """
    description = cc_debit_txn.get("description", "")
    debit_amount_paise = int(cc_debit_txn.get("debit", 0) or 0)

    if debit_amount_paise <= 0:
        return None

    # Step 1: Match provider pattern
    matched_provider: dict[str, Any] | None = None
    for pattern in provider_patterns:
        if _match_description_pattern(description, pattern["description_pattern"]):
            matched_provider = pattern
            break

    # Step 2: Unknown provider handling
    if matched_provider is None:
        liquidity_keywords = ["cred", "cheq", "spaid", "nobroker", "liquidity", "cash"]
        desc_lower = description.lower()
        has_liquidity_keyword = any(kw in desc_lower for kw in liquidity_keywords)

        if not has_liquidity_keyword:
            return None

        # Filter candidates for savings/current accounts in same household
        eligible_credits = [
            c for c in candidate_credits
            if _is_savings_or_current(c.get("account_type", "savings"))
            and c.get("household_id") == cc_debit_txn.get("household_id")
            and int(c.get("credit", 0) or 0) < debit_amount_paise
            and int(c.get("credit", 0) or 0) > 10000
        ]

        if not eligible_credits:
            return None

        # Unknown provider with valid credit match - still return for review
        # Find credit with fee closest to typical range (target ~225 bps midpoint)
        target_bps = 225
        best_credit = min(
            eligible_credits,
            key=lambda c: abs(_calculate_fee_bps(debit_amount_paise, int(c.get("credit", 0) or 0) - target_bps)),
        )

        credit_amount = int(best_credit.get("credit", 0) or 0)
        fee_paise = debit_amount_paise - credit_amount
        fee_bps = _calculate_fee_bps(debit_amount_paise, credit_amount)
        acc_id = best_credit.get("account_id", "?")

        return CashConversionResult(
            matched_credit_transaction_id=best_credit.get("id", 0),
            provider_name=None,
            purpose=_match_purpose(description, purpose_patterns),
            zone="unmatched_provider",
            confidence_bps=5000,
            fee_paise=fee_paise,
            fee_bps=fee_bps,
            settlement_days=_date_difference_days(
                cc_debit_txn.get("date_iso", ""),
                best_credit.get("date_iso", ""),
            ),
            narrative=(
                f"Rs{debit_amount_paise // 100} extracted via unknown provider "
                f"into {acc_id} "
                f"(amount: Rs{credit_amount // 100}, fee: Rs{fee_paise // 100} "
                f"({fee_bps / 100:.1f}%)); zone=unmatched_provider"
            ),
            match_reason="unknown_provider_structural_match",
        )

    # Step 3: Filter candidates by criteria
    settlement_days = matched_provider.get("typical_settlement_days", 2)
    household_id = cc_debit_txn.get("household_id")

    eligible_credits = []
    for credit in candidate_credits:
        if not _is_savings_or_current(credit.get("account_type", "savings")):
            continue

        if credit.get("household_id") != household_id:
            continue

        date_diff = _date_difference_days(
            cc_debit_txn.get("date_iso", ""),
            credit.get("date_iso", ""),
        )
        if date_diff < 0 or date_diff > settlement_days + 2:
            continue

        credit_amount = int(credit.get("credit", 0) or 0)
        if credit_amount >= debit_amount_paise:
            continue

        eligible_credits.append(credit)

    if not eligible_credits:
        return None

    # Step 4: Calculate zones and fees for each eligible credit
    candidates_with_zones = []
    for credit in eligible_credits:
        credit_amount = int(credit.get("credit", 0) or 0)
        fee_paise = debit_amount_paise - credit_amount
        fee_bps = _calculate_fee_bps(debit_amount_paise, credit_amount)

        zone = _determine_zone(
            fee_bps,
            matched_provider["fee_min_bps"],
            matched_provider["fee_max_bps"],
            matched_provider["review_fee_min_bps"],
            matched_provider["review_fee_max_bps"],
        )

        if zone is None:
            continue

        candidates_with_zones.append({
            "credit": credit,
            "fee_paise": fee_paise,
            "fee_bps": fee_bps,
            "zone": zone,
        })

    if not candidates_with_zones:
        return None

    # Step 5: Disambiguation - pick best match
    if len(candidates_with_zones) > 1:
        fee_range_midpoint = (matched_provider["fee_min_bps"] + matched_provider["fee_max_bps"]) // 2

        best = min(
            candidates_with_zones,
            key=lambda c: (
                0 if c["zone"] == "auto" else 1,
                abs(c["fee_bps"] - fee_range_midpoint) if c["zone"] == "auto" else c["fee_bps"],
            ),
        )
    else:
        best = candidates_with_zones[0]

    # Extract typed values from the best candidate dict
    matched_credit = cast(dict[str, Any], best["credit"])
    matched_zone: Literal["auto", "review"] = cast(Literal["auto", "review"], best["zone"])
    matched_fee_paise = cast(int, best["fee_paise"])
    matched_fee_bps = cast(int, best["fee_bps"])

    # Step 6: Calculate confidence
    confidence_bps: int = 8000 if matched_zone == "auto" else 5500

    if matched_provider.get("confirmed_by_user"):
        confidence_bps += 1000

    if statement_row:
        due_date_str = statement_row.get("payment_due_date", "")
        debit_date_str = cc_debit_txn.get("date_iso", "")
        if due_date_str and debit_date_str:
            # Parse due date with multiple format support
            due_date = None
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                try:
                    due_date = datetime.strptime(due_date_str, fmt).date()
                    break
                except ValueError:
                    continue

            # Parse debit date with multiple format support
            debit_date = None
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                try:
                    debit_date = datetime.strptime(debit_date_str, fmt).date()
                    break
                except ValueError:
                    continue

            if due_date and debit_date:
                days_to_due = (due_date - debit_date).days
                if 0 <= days_to_due <= 7:
                    confidence_bps += 1000

    confidence_bps = min(confidence_bps, 9900)

    # Step 7: Match purpose
    matched_purpose = _match_purpose(description, purpose_patterns)

    # Step 8: Build narrative
    fee_pct = matched_fee_bps / 100.0
    debit_rupees = debit_amount_paise // 100
    credit_rupees = int(matched_credit.get("credit", 0) or 0) // 100
    fee_rupees = matched_fee_paise // 100
    acc_id = matched_credit.get("account_id", "?")
    provider_name = matched_provider["provider_name"]

    narrative = (
        f"Rs{debit_rupees} extracted via {provider_name} "
        f"({matched_purpose or 'general liquidity'}) into "
        f"{acc_id} "
        f"(Rs{credit_rupees} received, fee: Rs{fee_rupees} ({fee_pct:.1f}%)); "
        f"zone={matched_zone}"
    )

    return CashConversionResult(
        matched_credit_transaction_id=matched_credit.get("id", 0),
        provider_name=provider_name,
        purpose=matched_purpose,
        zone=matched_zone,
        confidence_bps=confidence_bps,
        fee_paise=matched_fee_paise,
        fee_bps=matched_fee_bps,
        settlement_days=_date_difference_days(
            cc_debit_txn.get("date_iso", ""),
            matched_credit.get("date_iso", ""),
        ),
        narrative=narrative,
        match_reason=f"provider_match:{provider_name}:fee_in_range",
    )
