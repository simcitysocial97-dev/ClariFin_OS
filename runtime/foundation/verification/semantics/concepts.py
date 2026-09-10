"""
M9-C57 — Financial concept registry.

Maps financial domain concepts to their implementation locations and
encodes dependency relationships for blast-radius analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FinancialConcept:
    """A financial domain concept with its dependencies and invariants."""

    concept_id: str
    domain: str
    description: str
    depends_on: tuple[str, ...] = field(default_factory=tuple)
    affects: tuple[str, ...] = field(default_factory=tuple)
    invariants: tuple[str, ...] = field(default_factory=tuple)
    implemented_in: str = ""


FINANCIAL_CONCEPTS: dict[str, FinancialConcept] = {
    "emi_calculation": FinancialConcept(
        concept_id="emi_calculation",
        domain="loan_engine",
        description="Monthly EMI computation from principal, rate, and tenure",
        depends_on=("interest_computation",),
        affects=("schedule_generation", "prepayment_logic", "closure_validation"),
        invariants=("emi_must_exceed_interest", "total_payment_covers_principal"),
        implemented_in="backend/src/engines/loan_engine/emi.py",
    ),
    "interest_computation": FinancialConcept(
        concept_id="interest_computation",
        domain="loan_engine",
        description="Monthly interest calculation from outstanding balance and rate",
        depends_on=(),
        affects=("emi_calculation", "schedule_generation", "floating_rate_adjustment"),
        invariants=("emi_must_exceed_interest",),
        implemented_in="backend/src/engines/loan_engine/emi.py",
    ),
    "schedule_generation": FinancialConcept(
        concept_id="schedule_generation",
        domain="loan_engine",
        description="Amortization schedule generation with principal/interest breakdown",
        depends_on=("emi_calculation", "interest_computation"),
        affects=("closure_validation", "prepayment_logic", "metrics_computation"),
        invariants=("closure_requires_zero_balance", "total_payment_covers_principal"),
        implemented_in="backend/src/engines/loan_engine/amortization.py",
    ),
    "prepayment_logic": FinancialConcept(
        concept_id="prepayment_logic",
        domain="loan_engine",
        description="Prepayment application reducing principal or tenure",
        depends_on=("schedule_generation", "emi_calculation"),
        affects=("closure_validation", "metrics_computation"),
        invariants=("prepayment_reduces_principal_or_tenure", "total_payment_covers_principal"),
        implemented_in="backend/src/engines/loan_engine/prepayment.py",
    ),
    "closure_validation": FinancialConcept(
        concept_id="closure_validation",
        domain="loan_engine",
        description="Loan closure verification with zero-balance requirement",
        depends_on=("schedule_generation", "prepayment_logic"),
        affects=("metrics_computation"),
        invariants=("closure_requires_zero_balance",),
        implemented_in="backend/src/engines/loan_engine/foreclosure.py",
    ),
    "floating_rate_adjustment": FinancialConcept(
        concept_id="floating_rate_adjustment",
        domain="loan_engine",
        description="Floating rate bounded within contractual caps and floors",
        depends_on=("interest_computation",),
        affects=("emi_calculation", "schedule_generation"),
        invariants=("floating_rate_bounded", "emi_must_exceed_interest"),
        implemented_in="backend/src/engines/loan_engine/floating_rate.py",
    ),
    "transaction_matching": FinancialConcept(
        concept_id="transaction_matching",
        domain="reconciliation_engine",
        description="Cross-account transaction matching with tolerance bounds",
        depends_on=(),
        affects=("ledger_state", "balance_verification"),
        invariants=("reconciliation_match_within_tolerance",),
        implemented_in="backend/src/engines/reconciliation_engine.py",
    ),
    "running_balance": FinancialConcept(
        concept_id="running_balance",
        domain="balance_engine",
        description="Running balance from ordered transaction stream",
        depends_on=("transaction_matching",),
        affects=("balance_verification", "statement_validation"),
        invariants=("balance_equals_sum_of_transactions",),
        implemented_in="backend/src/engines/balance_engine.py",
    ),
    "cashflow_classification": FinancialConcept(
        concept_id="cashflow_classification",
        domain="cashflow_engine",
        description="Cashflow categorization into valid categories",
        depends_on=(),
        affects=("net_worth_computation", "forecasting"),
        invariants=("cashflow_category_valid",),
        implemented_in="backend/src/engines/cashflow_engine.py",
    ),
    "net_worth_computation": FinancialConcept(
        concept_id="net_worth_computation",
        domain="cashflow_engine",
        description="Net worth as assets minus liabilities",
        depends_on=("running_balance", "cashflow_classification"),
        affects=("forecasting", "risk_assessment"),
        invariants=("net_worth_equals_assets_minus_liabilities",),
        implemented_in="backend/src/engines/cashflow_engine.py",
    ),
    "forecasting": FinancialConcept(
        concept_id="forecasting",
        domain="financial_intelligence",
        description="Forward-looking financial forecasts with positive horizons",
        depends_on=("net_worth_computation", "cashflow_classification"),
        affects=("goal_planning", "scenario_analysis"),
        invariants=("forecast_horizon_positive",),
        implemented_in="backend/src/engines/financial_intelligence/forecasting.py",
    ),
    "goal_planning": FinancialConcept(
        concept_id="goal_planning",
        domain="financial_intelligence",
        description="Financial goal planning based on forecasts",
        depends_on=("forecasting",),
        affects=(),
        invariants=("forecast_horizon_positive",),
        implemented_in="backend/src/engines/financial_intelligence/goal_planner.py",
    ),
    "scenario_analysis": FinancialConcept(
        concept_id="scenario_analysis",
        domain="financial_intelligence",
        description="What-if scenario simulation for financial decisions",
        depends_on=("forecasting", "net_worth_computation"),
        affects=(),
        invariants=("forecast_horizon_positive",),
        implemented_in="backend/src/engines/financial_intelligence/scenario.py",
    ),
    "risk_assessment": FinancialConcept(
        concept_id="risk_assessment",
        domain="behaviour_engine",
        description="Financial risk scoring based on cashflow and balance patterns",
        depends_on=("running_balance", "cashflow_classification"),
        affects=(),
        invariants=("cashflow_category_valid",),
        implemented_in="backend/src/engines/behaviour_engine/core.py",
    ),
    "credit_utilization": FinancialConcept(
        concept_id="credit_utilization",
        domain="credit_card_engine",
        description="Credit utilization ratio computation and monitoring",
        depends_on=("running_balance",),
        affects=(),
        invariants=(),
        implemented_in="backend/src/engines/credit_card_engine/utilization.py",
    ),
}
