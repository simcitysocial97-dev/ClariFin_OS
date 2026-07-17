"""
Explanation Models - Explainability contracts for financial metrics.

All monetary values are in paise (₹1.00 = 100 paise).
All confidence values are in basis points (0-10000).
"""

from typing import Literal
from pydantic import BaseModel, Field

# Type aliases
EvidenceType = Literal['data', 'calculation', 'source']
CalculationOperation = Literal[
    'ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE',
    'AVERAGE', 'LOOKUP', 'FILTER', 'GROUP', 'MATCH'
]
SourceType = Literal[
    'statement', 'account', 'loan', 'investment',
    'transaction', 'recommendation_engine', 'cashflow_engine',
    'behaviour_engine', 'user_input'
]


class SourceReference(BaseModel):
    """Business source reference for evidence provenance."""
    type: SourceType
    id: str | int
    name: str | None = None
    date: str | None = None


class Evidence(BaseModel):
    """Evidence for a calculation."""
    id: str
    type: EvidenceType
    description: str
    value: int | str | bool | None
    sourceId: str | int | None = None


class CalculationStep(BaseModel):
    """Single step in a calculation chain."""
    stepId: str
    description: str
    operation: CalculationOperation
    inputIds: list[str]
    outputId: str
    order: int


class Confidence(BaseModel):
    """Confidence in basis points (0-10000)."""
    value: int = Field(ge=0, le=10000)
    reason: str | None = None


class Explanation(BaseModel):
    """Complete explanation for a financial metric."""
    metric: str
    value: int
    confidence: Confidence
    evidence: list[Evidence]
    sources: list[SourceReference]
    calculationSteps: list[CalculationStep]


class NetWorthExplanation(BaseModel):
    """Explanation for net worth calculation."""
    netWorth: Explanation
    assets: Explanation
    liabilities: Explanation
    confidenceReason: str | None = None


class NetWorthResponse(BaseModel):
    """Canonical API response for /api/networth endpoint."""
    net_worth_paise: int
    assets: dict[str, int]
    liabilities: dict[str, int]
    is_partial: bool
    partial_reason: str | None = None
    explanation: NetWorthExplanation | None = None
