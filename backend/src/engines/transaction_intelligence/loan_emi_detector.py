"""Loan EMI Payment Detector.

Pure function: accepts plain data, returns classification result.
No database access - schedule and loan data are passed in as parameters.
"""
from datetime import date
from typing import Any, Literal

from src.engines.transaction_intelligence.detector_result import EMIDetectionResult

# EMI keywords for description matching
EMI_KEYWORDS = {"emi", "loan", "installment", "repayment", "mortgage", "hdfc", "icici", "sbi", "axis"}


def _is_emi_description(description: str) -> bool:
    """Check if description contains EMI-related keywords."""
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in EMI_KEYWORDS)


def _amount_within_tolerance(amount_paise: int, expected_paise: int, tolerance_pct: float = 0.01) -> bool:
    """Check if amount is within ±tolerance_pct of expected."""
    if expected_paise == 0:
        return False
    diff = abs(amount_paise - expected_paise)
    tolerance_paise = int(expected_paise * tolerance_pct)
    return diff <= tolerance_paise


def _date_near_expected(txn_date_iso: str, expected_date_iso: str, days: int = 3) -> bool:
    """Check if transaction date is within N days of expected date."""
    try:
        txn_date = date.fromisoformat(txn_date_iso)
        expected_date = date.fromisoformat(expected_date_iso)
        return abs((txn_date - expected_date).days) <= days
    except (ValueError, TypeError):
        return False


def detect_emi_payment(
    debit_txn: dict[str, Any],
    loan_candidates: list[dict[str, Any]],
    schedule_lookup: dict[tuple[int, str], dict[str, Any]],
) -> EMIDetectionResult | None:
    """
    Detect if a debit transaction is an EMI payment.

    Args:
        debit_txn: Transaction dict with id, account_id, amount_paise, date_iso, description.
        loan_candidates: Loans where credit side matches a known loan account (caller filters these).
        schedule_lookup: Dict mapping (loan_id, due_date) to schedule row dicts.

    Returns:
        EMIDetectionResult if match found, None otherwise.
    """
    source_computed: Literal["computed"] = "computed"
    source_bank: Literal["bank_statement"] = "bank_statement"

    txn_amount = int(debit_txn.get("debit", 0) or debit_txn.get("amount_paise", 0) or 0)
    txn_date_iso = debit_txn.get("date_iso", "")
    txn_desc = debit_txn.get("description", "") or ""

    if txn_amount <= 0 or not txn_date_iso:
        return None

    best_match: EMIDetectionResult | None = None
    best_priority = 0

    for loan in loan_candidates:
        loan_id = int(loan["id"])
        emi_paise = int(loan.get("emi_paise", 0) or 0)
        next_emi_date = loan.get("next_emi_date")

        if emi_paise <= 0:
            continue

        # Check for bank statement override first (higher priority)
        bank_stmt_row = schedule_lookup.get((loan_id, txn_date_iso))
        if bank_stmt_row:
            # Bank statement schedule takes precedence
            return EMIDetectionResult(
                classification="liability_payment",
                sub_classification="emi",
                priority=100,
                confidence_bps=8000,  # 0.8 confidence
                source=source_bank,
                match_reason="bank_statement_override",
                matched_entity_id=loan_id,
                schedule_row_id=bank_stmt_row.get("id"),
                principal_paise=int(bank_stmt_row.get("principal_paise", 0)),
                interest_paise=int(bank_stmt_row.get("interest_paise", 0)),
                outstanding_after_paise=int(bank_stmt_row.get("outstanding_after_paise", 0)),
            )

        # Check computed schedule for this date
        txn_date_str = txn_date_iso[:10] if len(txn_date_iso) > 10 else txn_date_iso
        schedule_row = schedule_lookup.get((loan_id, txn_date_str))

        # Amount match check
        amount_matches = _amount_within_tolerance(txn_amount, emi_paise, 0.01)

        if amount_matches:
            if schedule_row:
                # Amount + schedule match
                priority = 90
                confidence = 9000
                match_reason = "amount_match"
            else:
                priority = 80
                confidence = 7500
                match_reason = "amount_only"

            if priority > best_priority:
                best_priority = priority
                best_match = EMIDetectionResult(
                    classification="liability_payment",
                    sub_classification="emi",
                    priority=priority,
                    confidence_bps=confidence,
                    source=source_computed,
                    match_reason=match_reason,
                    matched_entity_id=loan_id,
                    schedule_row_id=schedule_row.get("id") if schedule_row else None,
                    principal_paise=int(schedule_row.get("principal_paise", 0)) if schedule_row else 0,
                    interest_paise=int(schedule_row.get("interest_paise", 0)) if schedule_row else 0,
                    outstanding_after_paise=int(schedule_row.get("outstanding_after_paise", emi_paise)) if schedule_row else emi_paise,
                )

        # Date proximity match (priority 75 or 85 if combined with amount)
        if next_emi_date and _date_near_expected(txn_date_iso, next_emi_date, 3):
            # If we already have an amount match, date proximity boosts it to priority 85
            # Otherwise, use priority 75 with date proximity alone
            if amount_matches:
                # Amount + date proximity = priority 85 (only if not already matched)
                if best_match is None or best_priority < 85:
                    priority = 85
                    confidence = 7500
                    match_reason = "amount+date"
                    schedule_row_for_result = schedule_row if schedule_row else None

                    if priority > best_priority:
                        best_priority = priority
                        best_match = EMIDetectionResult(
                            classification="liability_payment",
                            sub_classification="emi",
                            priority=priority,
                            confidence_bps=confidence,
                            source=source_computed,
                            match_reason=match_reason,
                            matched_entity_id=loan_id,
                            schedule_row_id=schedule_row_for_result.get("id") if schedule_row_for_result else None,
                            principal_paise=int(schedule_row_for_result.get("principal_paise", 0)) if schedule_row_for_result else 0,
                            interest_paise=int(schedule_row_for_result.get("interest_paise", 0)) if schedule_row_for_result else 0,
                            outstanding_after_paise=int(schedule_row_for_result.get("outstanding_after_paise", emi_paise)) if schedule_row_for_result else emi_paise,
                        )
            else:
                # Try to find any schedule row near this date for principal/interest split
                found_row = None
                for (lid, due_date), row in schedule_lookup.items():
                    if lid == loan_id and _date_near_expected(txn_date_iso, due_date, 3):
                        found_row = row
                        break

                if found_row:
                    priority = 75
                    confidence = 7000
                    match_reason = "date_proximity"

                    if priority > best_priority:
                        best_priority = priority
                        best_match = EMIDetectionResult(
                            classification="liability_payment",
                            sub_classification="emi",
                            priority=priority,
                            confidence_bps=confidence,
                            source=source_computed,
                            match_reason=match_reason,
                            matched_entity_id=loan_id,
                            schedule_row_id=found_row.get("id"),
                            principal_paise=int(found_row.get("principal_paise", 0)),
                            interest_paise=int(found_row.get("interest_paise", 0)),
                            outstanding_after_paise=int(found_row.get("outstanding_after_paise", 0)),
                        )

        # Description keyword match (priority 60)
        if _is_emi_description(txn_desc):
            priority = 60
            confidence = 6000
            match_reason = "description_keyword"
            if priority > best_priority or best_match is None:
                best_priority = priority
                best_match = EMIDetectionResult(
                    classification="liability_payment",
                    sub_classification="emi",
                    priority=priority,
                    confidence_bps=confidence,
                    source=source_computed,
                    match_reason=match_reason,
                    matched_entity_id=loan_id,
                    schedule_row_id=schedule_row.get("id") if schedule_row else None,
                    principal_paise=int(schedule_row.get("principal_paise", 0)) if schedule_row else 0,
                    interest_paise=int(schedule_row.get("interest_paise", 0)) if schedule_row else 0,
                    outstanding_after_paise=int(schedule_row.get("outstanding_after_paise", emi_paise)) if schedule_row else emi_paise,
                )

    return best_match


def find_loan_candidates_for_account(
    transaction_account_id: str,
    loans: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Filter loans where lender matches the transaction account.

    Args:
        transaction_account_id: The account that made the payment.
        loans: All loans to filter.

    Returns:
        Loans where the account is likely the loan account.
    """
    return [
        loan for loan in loans
        if str(loan.get("lender", "")) == transaction_account_id
        or str(loan.get("lender", "")).lower() in transaction_account_id.lower()
    ]
