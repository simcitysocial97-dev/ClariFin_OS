"""Credit Card Payment Detector - Pure function for detecting CC payment lifecycle states.

Detects credit card payments from debit transactions and classifies them into
lifecycle states based on statement matching and payment amounts.

No database access - all data is passed as parameters.
"""
import re
from dataclasses import dataclass
from typing import Any, Literal

# Payment channel types for Phase 5 support
PaymentChannel = Literal["DIRECT", "CRED", "CHEQ", "SPAYLATER", "NOBROKER", "UNKNOWN"]

# Lifecycle states
LifecycleState = Literal[
    "statement_generated",
    "payment_received",
    "minimum_paid",
    "fully_paid",
    "revolving",
    "rolled_forward",
    "unknown",
]


# Card number patterns in description (e.g., "XX1234", "1234", masked formats)
_CARD_NUMBER_PATTERNS = [
    r"XX(\d{4})",           # XX1234 format
    r"(\d{4})",              # Last 4 digits standalone
    r"\*\*\*\*(\d{4})",     # ****1234 format
]


def extract_card_last4(description: str) -> str | None:
    """
    Extract card last4 from transaction description.

    Patterns matched:
    - "XX1234" (most common in Indian bank statements)
    - Just 4 digits (when description is just the card reference)
    - "****1234" masked format

    Returns the last 4 digits or None if no pattern found.
    """
    desc_upper = description.upper()

    # Try XX1234 pattern first (most specific)
    xx_match = re.search(r"XX(\d{4})", desc_upper)
    if xx_match:
        return xx_match.group(1)

    # Try masked format
    masked_match = re.search(r"\*\*\*\*(\d{4})", desc_upper)
    if masked_match:
        return masked_match.group(1)

    # Try standalone 4 digits (only if clearly not part of other number)
    # Look for word boundary context
    standalone_matches = re.findall(r"(?:^|[^0-9])(\d{4})(?:$|[^0-9])", desc_upper)
    for match in standalone_matches:
        # Verify it's likely a card reference (not year like 2025)
        match_str = str(match)  # Type guard for mypy
        if not desc_upper.startswith("20") and len(match_str) == 4:
            return match_str

    return None


def determine_payment_channel(description: str) -> PaymentChannel:
    """
    Determine the payment channel from transaction description.

    Returns one of: DIRECT, CRED, CHEQ, SPAYLATER, NOBROKER, UNKNOWN
    """
    desc_lower = description.lower()

    # CRED patterns (but not "credit card" - that's DIRECT)
    if "cred" in desc_lower and "credit card" not in desc_lower:
        return "CRED"

    # CheQ patterns
    if "cheq" in desc_lower or "chequebook" in desc_lower:
        return "CHEQ"

    # SBI/IndusInd SPayLater patterns
    if "spaylater" in desc_lower or "s-pa" in desc_lower:
        return "SPAYLATER"

    # NoBroker patterns (if applicable)
    if "nobroker" in desc_lower:
        return "NOBROKER"

    # Default to DIRECT (direct bank transfer/NEFT/RTGS/UPI to card)
    return "DIRECT"


def _convert_to_paise(value: Any) -> int:
    """
    Convert a value to paise (integer).

    Handles:
    - Integer paise values (passed through)
    - Float rupee values (multiplied by 100)
    - String amounts (parsed and converted)
    """
    if value is None:
        return 0

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        # Value is in rupees, convert to paise
        return int(value * 100)

    if isinstance(value, str):
        # Parse string amount (could be rupees or paise format)
        cleaned = value.replace(",", "").strip()
        try:
            # Assume rupees if it looks like a decimal
            if "." in cleaned:
                return int(float(cleaned) * 100)
            # Assume paise if it's a large integer
            return int(cleaned)
        except ValueError:
            return 0

    return 0


@dataclass(frozen=True)
class CCPaymentDetectionResult:
    """Result from credit card payment detection.

    Attributes:
        matched_statement_id: ID of the matched statement (or None)
        classification: Always 'credit_card_payment'
        lifecycle_state: Current lifecycle state
        payment_channel: How the payment was made
        confidence_bps: Confidence score (2000-9500)
        payment_amount_paise: Amount paid in paise
        statement_amount_paise: Total due on matched statement
        minimum_due_paise: Minimum due on matched statement
        remaining_outstanding_paise: Outstanding after payment
        source: Source of detection
        match_reason: Why this matched (for debugging)
    """
    matched_statement_id: int | None
    classification: str
    lifecycle_state: LifecycleState
    payment_channel: PaymentChannel
    confidence_bps: int
    payment_amount_paise: int
    statement_amount_paise: int
    minimum_due_paise: int
    remaining_outstanding_paise: int
    source: Literal["computed", "bank_statement"]
    match_reason: str


def classify_cc_payment(
    debit_txn: dict[str, Any],
    statement_row: dict[str, Any] | None,
    payment_channel: PaymentChannel = "DIRECT",
) -> CCPaymentDetectionResult:
    """
    Classify a debit transaction as a credit card payment.

    Args:
        debit_txn: Transaction dict with id, description, amount_paise, date_iso
        statement_row: Matched statement row (or None)
        payment_channel: Payment channel (default DIRECT)

    Returns:
        CCPaymentDetectionResult with lifecycle state and details.
    """
    payment_amount_paise = int(debit_txn.get("amount_paise", 0) or 0)

    # No matching statement found
    if statement_row is None:
        return CCPaymentDetectionResult(
            matched_statement_id=None,
            classification="credit_card_payment_unmatched",
            lifecycle_state="unknown",
            payment_channel=payment_channel,
            confidence_bps=2000,  # Low confidence for unmatched
            payment_amount_paise=payment_amount_paise,
            statement_amount_paise=0,
            minimum_due_paise=0,
            remaining_outstanding_paise=0,
            source="computed",
            match_reason="no_matching_statement_found",
        )

    statement_id = statement_row.get("id")
    total_due_raw = statement_row.get("total_amount_due", 0)
    min_due_raw = statement_row.get("minimum_amount_due", 0)

    statement_amount_paise = _convert_to_paise(total_due_raw)
    minimum_due_paise = _convert_to_paise(min_due_raw)

    # Full payment clears the statement
    # Using 100 paise tolerance for rounding differences
    if payment_amount_paise >= statement_amount_paise - 100:
        return CCPaymentDetectionResult(
            matched_statement_id=statement_id,
            classification="credit_card_payment",
            lifecycle_state="fully_paid",
            payment_channel=payment_channel,
            confidence_bps=9500,
            payment_amount_paise=payment_amount_paise,
            statement_amount_paise=statement_amount_paise,
            minimum_due_paise=minimum_due_paise,
            remaining_outstanding_paise=0,
            source="computed",
            match_reason="full_payment_matched",
        )

    # Payment meets or exceeds minimum due
    if payment_amount_paise >= minimum_due_paise:
        return CCPaymentDetectionResult(
            matched_statement_id=statement_id,
            classification="credit_card_payment",
            lifecycle_state="revolving",  # Partial payment = revolving balance
            payment_channel=payment_channel,
            confidence_bps=8500,
            payment_amount_paise=payment_amount_paise,
            statement_amount_paise=statement_amount_paise,
            minimum_due_paise=minimum_due_paise,
            remaining_outstanding_paise=statement_amount_paise - payment_amount_paise,
            source="computed",
            match_reason="partial_payment_above_minimum",
        )

    # Payment below minimum due
    return CCPaymentDetectionResult(
        matched_statement_id=statement_id,
        classification="credit_card_payment",
        lifecycle_state="payment_received",  # Received but below minimum
        payment_channel=payment_channel,
        confidence_bps=7000,
        payment_amount_paise=payment_amount_paise,
        statement_amount_paise=statement_amount_paise,
        minimum_due_paise=minimum_due_paise,
        remaining_outstanding_paise=statement_amount_paise - payment_amount_paise,
        source="computed",
        match_reason="payment_below_minimum_due",
    )


def detect_cc_payment(
    debit_txn: dict[str, Any],
    statement_row: dict[str, Any] | None,
) -> CCPaymentDetectionResult | None:
    """
    Detect if a debit transaction is a credit card payment.

    Args:
        debit_txn: Transaction dict with description, amount_paise, date_iso
        statement_row: Optional matched statement for lifecycle analysis

    Returns:
        CCPaymentDetectionResult if this looks like a CC payment, None otherwise.
    """
    description = (debit_txn.get("description") or "").upper()

    # Check for common CC payment keywords in description
    cc_keywords = [
        "CREDIT CARD",
        "CC PAYMENT",
        "CARD PAYMENT",
        "XX",  # Card number masked format
        "HDFC CREDIT",
        "ICICI CREDIT",
        "AXIS CREDIT",
        "SBI CARD",
        "IDFC FIRST",
        "INDUSIND",
    ]

    # Must have at least one CC keyword OR a card number pattern
    has_keyword = any(kw in description for kw in cc_keywords)
    has_card_pattern = bool(extract_card_last4(debit_txn.get("description", "")))

    if not has_keyword and not has_card_pattern:
        # Check if amount looks like a CC payment (typically round amounts like 5000, 10000)
        amount = int(debit_txn.get("amount_paise", 0) or 0)
        # Common minimum due amounts (₹100-₹5000 in paise)
        if amount > 10000 and amount <= 500000 and not has_card_pattern:
            # Still could be a CC payment - pass through for loose matching
            # But only if we have a statement match
            if statement_row is None:
                return None

    # Determine payment channel from description
    payment_channel = determine_payment_channel(debit_txn.get("description", ""))

    return classify_cc_payment(debit_txn, statement_row, payment_channel)
