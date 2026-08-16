"""
Loans DTOs
==========

Data Transfer Objects for loans API responses.
All monetary fields use _paise suffix for explicit units.
All interest rates use _bps suffix (basis points, 1% = 100 bps).
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

# ===== Loan Types =====

LoanType = Literal["personal", "home", "car", "education", "other"]
LoanStatus = Literal["active", "closed", "defaulted"]


# ===== Amortization Schedule Types =====


class AmortizationEntryDTO(BaseModel):
    """Single amortization schedule entry."""

    month: int = Field(description="Month number (1-based)")
    date: str = Field(description="Payment date (ISO format)")
    emi_paise: int = Field(description="EMI amount in paise")
    principal_paise: int = Field(description="Principal portion in paise")
    interest_paise: int = Field(description="Interest portion in paise")
    balance_paise: int = Field(description="Remaining balance in paise")


class AmortizationScheduleDTO(BaseModel):
    """Amortization schedule response DTO."""

    loan_id: str = Field(description="Loan identifier")
    emi_paise: int = Field(description="Monthly EMI in paise")
    total_interest_paise: int = Field(
        description="Total interest over loan term in paise"
    )
    schedule: list[AmortizationEntryDTO] = Field(
        description="Amortization schedule entries"
    )


# ===== Loan Summary Types =====


class LoanSummaryDTO(BaseModel):
    """Loan summary information."""

    id: str = Field(description="Loan identifier")
    name: str = Field(description="Loan name")
    type: LoanType = Field(description="Loan type")
    lender: str = Field(description="Lending institution")
    original_amount_paise: int = Field(description="Original loan amount in paise")
    outstanding_paise: int = Field(description="Outstanding balance in paise")
    interest_rate_bps: int = Field(description="Annual interest rate in basis points")
    tenure_months: int = Field(description="Original tenure in months")
    remaining_months: int = Field(description="Remaining tenure in months")
    emi_paise: int = Field(description="Monthly EMI in paise")
    status: LoanStatus = Field(description="Loan status")
    start_date: str = Field(description="Loan start date (ISO format)")
    end_date: str | None = Field(default=None, description="Loan end date (ISO format)")


# ===== Payment Progress Types =====


class PaymentProgressDTO(BaseModel):
    """Payment progress for a loan."""

    loan_id: str = Field(description="Loan identifier")
    total_payments: int = Field(description="Total number of payments made")
    total_principal_paise: int = Field(description="Total principal paid in paise")
    total_interest_paise: int = Field(description="Total interest paid in paise")
    principal_percentage: float = Field(
        description="Percentage of principal paid (0-100)"
    )
    interest_percentage: float = Field(
        description="Percentage of interest paid (0-100)"
    )


# ===== Interest Analysis Types =====


class InterestAnalysisDTO(BaseModel):
    """Interest analysis for a loan."""

    loan_id: str = Field(description="Loan identifier")
    total_interest_paise: int = Field(description="Total interest to be paid in paise")
    paid_interest_paise: int = Field(description="Interest paid so far in paise")
    remaining_interest_paise: int = Field(
        description="Interest remaining to be paid in paise"
    )
    interest_ratio: float = Field(description="Interest to principal ratio")


# ===== Loan Insight Types =====

LoanInsightType = Literal["positive", "warning", "info", "alert"]
LoanInsightSeverity = Literal["low", "medium", "high"]


class LoanInsightDTO(BaseModel):
    """Insight about loan changes or patterns."""

    type: LoanInsightType = Field(description="Insight type")
    severity: LoanInsightSeverity = Field(description="Insight severity")
    message: str = Field(description="Human-readable insight message")
    action_url: str | None = Field(
        default=None, description="URL for detailed view or action"
    )


# ===== Loan Evidence Types =====


class LoanEvidenceItemDTO(BaseModel):
    """Evidence item for loan calculation."""

    type: str = Field(description="Evidence type (payment, calculation, adjustment)")
    summary: str = Field(description="Human-readable summary")
    source: str = Field(description="Source reference")
    confidence: float | None = Field(
        default=None, description="Confidence score (0-100)"
    )


class LoanCalculationStepDTO(BaseModel):
    """Calculation step in the loan derivation chain."""

    name: str = Field(description="Step name")
    description: str = Field(description="Step description")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Input values")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Output values")


class LoanEvidenceChainDTO(BaseModel):
    """Evidence chain for loan calculation."""

    summary: str = Field(description="Overall summary of the calculation")
    evidence: list[LoanEvidenceItemDTO] = Field(
        default_factory=list, description="List of evidence items"
    )
    calculation_steps: list[LoanCalculationStepDTO] = Field(
        default_factory=list, description="Calculation chain steps"
    )
    source_references: list[str] = Field(
        default_factory=list, description="Source references for traceability"
    )
    confidence_score: float = Field(description="Overall confidence (0-100)")


class PaymentResponseDTO(BaseModel):
    """Payment response DTO."""

    success: bool = Field(default=True, description="Payment success status")
    payment_id: str = Field(description="Payment identifier")


class PrepaymentSimulationDTO(BaseModel):
    """Prepayment simulation response DTO."""

    original_interest_paise: int = Field(description="Original total interest in paise")
    new_interest_paise: int = Field(
        description="New total interest after prepayment in paise"
    )
    interest_saved_paise: int = Field(description="Interest saved in paise")
    new_tenure_months: int = Field(description="New tenure in months")
    tenure_saved_months: int = Field(description="Tenure saved in months")
    new_emi_paise: int | None = Field(default=None, description="New EMI in paise")


class ForeclosureSimulationDTO(BaseModel):
    """Foreclosure simulation response DTO."""

    outstanding_paise: int = Field(description="Outstanding balance in paise")
    penalty_paise: int = Field(description="Foreclosure penalty in paise")
    foreclosure_amount_paise: int = Field(
        description="Total foreclosure amount in paise"
    )
    interest_saved_paise: int = Field(description="Interest saved in paise")


# ===== Main Loans DTO =====


class LoansDTO(BaseModel):
    """
    Loans data transfer object.

    Monetary fields:
    - total_outstanding_paise: Total outstanding in paise (canonical)
    - total_emi_paise: Total EMI in paise
    """

    loans: list[LoanSummaryDTO] = Field(
        default_factory=list, description="List of loan summaries"
    )
    total_outstanding_paise: int = Field(
        description="Total outstanding across all loans in paise"
    )
    total_emi_paise: int = Field(description="Total monthly EMI in paise")
    loan_count: int = Field(description="Total number of active loans")
    insights: list[LoanInsightDTO] = Field(
        default_factory=list, description="List of insights about loans"
    )
    evidence_chain: LoanEvidenceChainDTO | None = Field(
        default=None, description="Evidence chain for explainability"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "loans": [],
                "total_outstanding_paise": 50000000,  # ₹5,00,000.00
                "total_emi_paise": 2500000,  # ₹25,000.00
                "loan_count": 2,
                "insights": [],
                "evidence_chain": None,
            }
        }


# ===== Loans Response Types =====


class LoansAmortizationResponse(BaseModel):
    """Response for amortization schedule endpoint."""

    schedule: list[AmortizationEntryDTO] = Field(
        default_factory=list, description="Amortization schedule entries"
    )
    total_count: int = Field(description="Total number of entries")


class LoansPaymentProgressResponse(BaseModel):
    """Response for payment progress endpoint."""

    progress: list[PaymentProgressDTO] = Field(
        default_factory=list, description="Payment progress for each loan"
    )


class LoansInterestAnalysisResponse(BaseModel):
    """Response for interest analysis endpoint."""

    analysis: list[InterestAnalysisDTO] = Field(
        default_factory=list, description="Interest analysis for each loan"
    )
