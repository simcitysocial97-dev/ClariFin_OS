"""
M9-C57 — Financial invariant definitions and assertion helpers.

Each invariant encodes a mathematical or business-rule property that must
hold for financial computations. When an invariant is violated, the
exception carries structured metadata (id, expected, actual, context,
remediation) so that verification reports can surface domain-meaningful
diagnostics instead of raw tracebacks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Invariant registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FinancialInvariant:
    """A single financial domain invariant."""

    invariant_id: str
    domain: str
    description: str
    consequence: str
    remediation_pattern: str
    implemented_in: str


FINANCIAL_INVARIANTS: dict[str, FinancialInvariant] = {
    "emi_must_exceed_interest": FinancialInvariant(
        invariant_id="emi_must_exceed_interest",
        domain="loan_engine",
        description="EMI must exceed monthly interest to reduce principal",
        consequence="Creates negative amortization where balance grows despite payments",
        remediation_pattern="Increase tenure or reduce principal to lower monthly interest",
        implemented_in="backend/src/engines/loan_engine/emi.py",
    ),
    "closure_requires_zero_balance": FinancialInvariant(
        invariant_id="closure_requires_zero_balance",
        domain="loan_engine",
        description="Loan closure requires final balance to be zero",
        consequence="Account remains open with residual debt or overpayment",
        remediation_pattern="Verify all payments applied; check for rounding discrepancies",
        implemented_in="backend/src/engines/loan_engine/foreclosure.py",
    ),
    "total_payment_covers_principal": FinancialInvariant(
        invariant_id="total_payment_covers_principal",
        domain="loan_engine",
        description="Total repayment must cover the original principal",
        consequence="Principal侵蚀 leads to lender loss and borrower windfall",
        remediation_pattern="Check EMI formula and tenure; ensure interest is positive",
        implemented_in="backend/src/engines/loan_engine/prepayment.py",
    ),
    "reconciliation_match_within_tolerance": FinancialInvariant(
        invariant_id="reconciliation_match_within_tolerance",
        domain="reconciliation_engine",
        description="Matched transactions must agree within tolerance",
        consequence="Un reconciled transactions cause ledger imbalance",
        remediation_pattern="Investigate amount or date drift beyond configured tolerance",
        implemented_in="backend/src/engines/reconciliation_engine.py",
    ),
    "balance_equals_sum_of_transactions": FinancialInvariant(
        invariant_id="balance_equals_sum_of_transactions",
        domain="balance_engine",
        description="Running balance must equal sum of all transactions",
        consequence="Balance drift indicates missing or duplicated entries",
        remediation_pattern="Audit transaction log for duplicates or gaps",
        implemented_in="backend/src/engines/balance_engine.py",
    ),
    "prepayment_reduces_principal_or_tenure": FinancialInvariant(
        invariant_id="prepayment_reduces_principal_or_tenure",
        domain="loan_engine",
        description="Prepayment must reduce either principal outstanding or total tenure",
        consequence="Prepayment has no benefit if neither principal nor tenure decreases",
        remediation_pattern="Verify prepayment application logic; check schedule recalculation",
        implemented_in="backend/src/engines/loan_engine/prepayment.py",
    ),
    "floating_rate_bounded": FinancialInvariant(
        invariant_id="floating_rate_bounded",
        domain="loan_engine",
        description="Floating rate must stay within contractual caps and floors",
        consequence="Out-of-band rates produce invalid EMI calculations",
        remediation_pattern="Cap/floor rate to contractual limits before computation",
        implemented_in="backend/src/engines/loan_engine/floating_rate.py",
    ),
    "cashflow_category_valid": FinancialInvariant(
        invariant_id="cashflow_category_valid",
        domain="cashflow_engine",
        description="Cashflow categories must be from the allowed set",
        consequence="Invalid categories break aggregation and reporting",
        remediation_pattern="Map unknown categories to canonical set or flag for review",
        implemented_in="backend/src/engines/cashflow_engine.py",
    ),
    "forecast_horizon_positive": FinancialInvariant(
        invariant_id="forecast_horizon_positive",
        domain="financial_intelligence",
        description="Forecast horizon must be a positive number of periods",
        consequence="Non-positive horizon produces undefined or trivial forecasts",
        remediation_pattern="Validate horizon > 0 before invoking forecast engine",
        implemented_in="backend/src/engines/financial_intelligence/forecasting.py",
    ),
    "net_worth_equals_assets_minus_liabilities": FinancialInvariant(
        invariant_id="net_worth_equals_assets_minus_liabilities",
        domain="cashflow_engine",
        description="Net worth must equal total assets minus total liabilities",
        consequence="Imbalanced net worth breaks portfolio analytics",
        remediation_pattern="Reconcile asset and liability totals; check for missing accounts",
        implemented_in="backend/src/engines/cashflow_engine.py",
    ),
}


# ---------------------------------------------------------------------------
# Violation exception
# ---------------------------------------------------------------------------


class FinancialInvariantViolation(AssertionError):
    """Raised when a financial invariant is violated.

    Attributes:
        invariant_id: The invariant that was violated.
        expected: Human-readable description of the expected condition.
        actual: Human-readable description of the actual value.
        context: Additional diagnostic data (e.g. loan parameters).
        remediation: Suggested remediation action.
    """

    def __init__(
        self,
        invariant_id: str,
        expected: str,
        actual: str,
        context: dict[str, Any] | None = None,
        remediation: str = "",
    ) -> None:
        self.invariant_id = invariant_id
        self.expected = expected
        self.actual = actual
        self.context = context or {}
        self.remediation = remediation

        inv = FINANCIAL_INVARIANTS.get(invariant_id)
        description = inv.description if inv else invariant_id
        lines = [
            f"Financial Invariant Violated: {invariant_id}",
            f"  Invariant: {description}",
            f"  Expected: {expected}",
            f"  Actual: {actual}",
        ]
        if context:
            ctx_str = ", ".join(f"{k}={v}" for k, v in sorted(context.items()))
            lines.append(f"  Context: {{{ctx_str}}}")
        if remediation:
            lines.append(f"  Remediation: {remediation}")
        super().__init__("\n".join(lines))

    def to_dict(self) -> dict[str, Any]:
        return {
            "invariant_id": self.invariant_id,
            "expected": self.expected,
            "actual": self.actual,
            "context": self.context,
            "remediation": self.remediation,
        }


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------


class FinancialAssertion:
    """Static helpers for asserting financial invariants in tests."""

    @staticmethod
    def emi_exceeds_interest(emi_paise: int, interest_paise: int, context: dict[str, Any] | None = None) -> None:
        """Assert EMI > monthly interest (principal must be reducing)."""
        inv = FinancialAssertion._get_inv("emi_must_exceed_interest")
        if emi_paise <= interest_paise:
            ctx = {**(context or {}), "emi_paise": emi_paise, "interest_paise": interest_paise}
            raise FinancialInvariantViolation(
                invariant_id="emi_must_exceed_interest",
                expected=f"emi ({emi_paise}) > interest ({interest_paise})",
                actual=f"emi ({emi_paise}) <= interest ({interest_paise})",
                context=ctx,
                remediation=inv.remediation_pattern,
            )

    @staticmethod
    def closure_zero_balance(final_balance: int, context: dict[str, Any] | None = None) -> None:
        """Assert loan closure leaves zero balance."""
        inv = FinancialAssertion._get_inv("closure_requires_zero_balance")
        if final_balance != 0:
            ctx = {**(context or {}), "final_balance_paise": final_balance}
            raise FinancialInvariantViolation(
                invariant_id="closure_requires_zero_balance",
                expected="final_balance == 0",
                actual=f"final_balance == {final_balance}",
                context=ctx,
                remediation=inv.remediation_pattern,
            )

    @staticmethod
    def total_payment_covers_principal(total_payment: int, principal: int, context: dict[str, Any] | None = None) -> None:
        """Assert total repayment >= original principal."""
        inv = FinancialAssertion._get_inv("total_payment_covers_principal")
        if total_payment < principal:
            ctx = {**(context or {}), "total_payment_paise": total_payment, "principal_paise": principal}
            raise FinancialInvariantViolation(
                invariant_id="total_payment_covers_principal",
                expected=f"total_payment ({total_payment}) >= principal ({principal})",
                actual=f"total_payment ({total_payment}) < principal ({principal})",
                context=ctx,
                remediation=inv.remediation_pattern,
            )

    @staticmethod
    def reconciliation_within_tolerance(diff: int, tolerance: int, context: dict[str, Any] | None = None) -> None:
        """Assert transaction match difference is within tolerance."""
        inv = FinancialAssertion._get_inv("reconciliation_match_within_tolerance")
        if abs(diff) > tolerance:
            ctx = {**(context or {}), "diff": diff, "tolerance": tolerance}
            raise FinancialInvariantViolation(
                invariant_id="reconciliation_match_within_tolerance",
                expected=f"|diff| <= tolerance ({tolerance})",
                actual=f"|diff| = {abs(diff)} > tolerance ({tolerance})",
                context=ctx,
                remediation=inv.remediation_pattern,
            )

    @staticmethod
    def balance_equals_transaction_sum(balance: int, transaction_sum: int, context: dict[str, Any] | None = None) -> None:
        """Assert running balance equals sum of transactions."""
        inv = FinancialAssertion._get_inv("balance_equals_sum_of_transactions")
        if balance != transaction_sum:
            ctx = {**(context or {}), "balance": balance, "transaction_sum": transaction_sum}
            raise FinancialInvariantViolation(
                invariant_id="balance_equals_sum_of_transactions",
                expected=f"balance ({balance}) == transaction_sum ({transaction_sum})",
                actual=f"balance ({balance}) != transaction_sum ({transaction_sum})",
                context=ctx,
                remediation=inv.remediation_pattern,
            )

    @staticmethod
    def prepayment_reduces_outstanding(old_outstanding: int, new_outstanding: int, context: dict[str, Any] | None = None) -> None:
        """Assert prepayment reduces outstanding principal."""
        inv = FinancialAssertion._get_inv("prepayment_reduces_principal_or_tenure")
        if new_outstanding >= old_outstanding:
            ctx = {**(context or {}), "old_outstanding": old_outstanding, "new_outstanding": new_outstanding}
            raise FinancialInvariantViolation(
                invariant_id="prepayment_reduces_principal_or_tenure",
                expected=f"new_outstanding ({new_outstanding}) < old_outstanding ({old_outstanding})",
                actual=f"new_outstanding ({new_outstanding}) >= old_outstanding ({old_outstanding})",
                context=ctx,
                remediation=inv.remediation_pattern,
            )

    @staticmethod
    def floating_rate_bounded(rate_bps: int, floor_bps: int, cap_bps: int, context: dict[str, Any] | None = None) -> None:
        """Assert floating rate stays within contractual bounds."""
        inv = FinancialAssertion._get_inv("floating_rate_bounded")
        if rate_bps < floor_bps or rate_bps > cap_bps:
            ctx = {**(context or {}), "rate_bps": rate_bps, "floor_bps": floor_bps, "cap_bps": cap_bps}
            raise FinancialInvariantViolation(
                invariant_id="floating_rate_bounded",
                expected=f"floor ({floor_bps}) <= rate ({rate_bps}) <= cap ({cap_bps})",
                actual=f"rate ({rate_bps}) out of bounds [{floor_bps}, {cap_bps}]",
                context=ctx,
                remediation=inv.remediation_pattern,
            )

    @staticmethod
    def cashflow_category_valid(category: str, valid_categories: list[str], context: dict[str, Any] | None = None) -> None:
        """Assert cashflow category is in the allowed set."""
        inv = FinancialAssertion._get_inv("cashflow_category_valid")
        if category not in valid_categories:
            ctx = {**(context or {}), "category": category, "valid_categories": valid_categories}
            raise FinancialInvariantViolation(
                invariant_id="cashflow_category_valid",
                expected=f"category in {valid_categories}",
                actual=f"category = {category!r}",
                context=ctx,
                remediation=inv.remediation_pattern,
            )

    @staticmethod
    def forecast_horizon_positive(horizon: int, context: dict[str, Any] | None = None) -> None:
        """Assert forecast horizon is positive."""
        inv = FinancialAssertion._get_inv("forecast_horizon_positive")
        if horizon <= 0:
            ctx = {**(context or {}), "horizon": horizon}
            raise FinancialInvariantViolation(
                invariant_id="forecast_horizon_positive",
                expected="horizon > 0",
                actual=f"horizon = {horizon}",
                context=ctx,
                remediation=inv.remediation_pattern,
            )

    @staticmethod
    def net_worth_balanced(assets: int, liabilities: int, net_worth: int, context: dict[str, Any] | None = None) -> None:
        """Assert net worth equals assets minus liabilities."""
        inv = FinancialAssertion._get_inv("net_worth_equals_assets_minus_liabilities")
        expected_nw = assets - liabilities
        if net_worth != expected_nw:
            ctx = {**(context or {}), "assets": assets, "liabilities": liabilities, "net_worth": net_worth}
            raise FinancialInvariantViolation(
                invariant_id="net_worth_equals_assets_minus_liabilities",
                expected=f"net_worth ({net_worth}) == assets ({assets}) - liabilities ({liabilities})",
                actual=f"net_worth ({net_worth}) != expected ({expected_nw})",
                context=ctx,
                remediation=inv.remediation_pattern,
            )

    @staticmethod
    def _get_inv(invariant_id: str) -> FinancialInvariant:
        inv = FINANCIAL_INVARIANTS.get(invariant_id)
        if inv is None:
            raise ValueError(f"Unknown invariant: {invariant_id}")
        return inv
