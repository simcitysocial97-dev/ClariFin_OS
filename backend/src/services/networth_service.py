"""Net worth business orchestration service."""

from datetime import datetime
from src.models.explanation import (
    Evidence,
    SourceReference,
    CalculationStep,
    Confidence,
    Explanation,
    NetWorthExplanation,
    NetWorthResponse,
)
from src.repositories import NetWorthRepository
from src.services.base import BaseService


class NetWorthService(BaseService):
    """Service for net worth calculation and orchestration."""

    def __init__(self, db_path: str | None = None):
        super().__init__(db_path)
        self.repo = NetWorthRepository(self.db_path)

    def calculate(self) -> NetWorthResponse:
        """
        Compute net worth from all financial data.

        Net Worth = Assets - Liabilities
        Assets = account balances + investment current values
        Liabilities = loan outstanding + card outstanding (latest statement)

        Returns:
            {
                net_worth_paise: int,
                assets: {total_paise, accounts_paise, investments_paise, account_count, investment_count},
                liabilities: {total_paise, loans_paise, cards_paise, loan_count, card_count},
                is_partial: bool,
                partial_reason: str | None
            }
        """
        data = self.repo.get_networth_data()
        accounts = data["accounts"]
        loans = data["loans"]
        investments = data["investments"]
        statements = data["statements"]

        # Assets
        account_balance_paise = sum(a["balance_paise"] for a in accounts)
        investment_value_paise = sum(i["current_value_paise"] for i in investments)
        total_assets_paise = account_balance_paise + investment_value_paise

        # Liabilities
        loan_outstanding_paise = sum(loan["outstanding_paise"] for loan in loans)

        # Card outstanding from latest statement per card
        card_outstanding_paise = 0
        seen_cards: set[str] = set()
        for stmt in sorted(
            statements,
            key=lambda s: str(s.get("statement_period_to") or s.get("imported_at") or ""),
            reverse=True,
        ):
            card_key = f"{stmt.get('bank', '')}_{stmt.get('card_last4', '')}"
            if card_key not in seen_cards:
                seen_cards.add(card_key)
                due = stmt.get("total_amount_due", 0) or 0
                card_outstanding_paise += int(round(due * 100))

        total_liabilities_paise = loan_outstanding_paise + card_outstanding_paise
        net_worth_paise = total_assets_paise - total_liabilities_paise

        return NetWorthResponse(
            net_worth_paise=net_worth_paise,
            assets={
                "total_paise": total_assets_paise,
                "accounts_paise": account_balance_paise,
                "investments_paise": investment_value_paise,
                "account_count": len(accounts),
                "investment_count": len(investments),
            },
            liabilities={
                "total_paise": total_liabilities_paise,
                "loans_paise": loan_outstanding_paise,
                "cards_paise": card_outstanding_paise,
                "loan_count": len(loans),
                "card_count": len(seen_cards),
            },
            is_partial=len(accounts) == 0 and len(investments) == 0,
            partial_reason=(
                "Add accounts and investments for complete net worth"
                if len(accounts) == 0
                else None
            ),
            last_updated=datetime.now().isoformat(),
        )

    def calculate_with_explanation(self) -> NetWorthResponse:
        """
        Compute net worth with full explainability.

        Returns:
            {
                net_worth_paise: int,
                assets: {...},
                liabilities: {...},
                is_partial: bool,
                partial_reason: str | None,
                explanation: NetWorthExplanation
            }
        """
        data = self.repo.get_networth_data()
        accounts = data["accounts"]
        loans = data["loans"]
        investments = data["investments"]
        statements = data["statements"]

        # Build evidence for accounts
        account_evidence: list[Evidence] = []
        account_sources: list[SourceReference] = []
        for acc in accounts:
            account_evidence.append(Evidence(
                id=f"account-balance-{acc.get('id', 'unknown')}",
                type="data",
                description=f"Account balance: {acc.get('name', 'Unknown')}",
                value=acc.get("balance_paise", 0),
                sourceId=acc.get("id", "unknown"),
            ))
            account_sources.append(SourceReference(
                type="account",
                id=acc.get("id", "unknown"),
                name=acc.get("name", "Unknown"),
            ))

        # Build evidence for investments
        investment_evidence: list[Evidence] = []
        investment_sources: list[SourceReference] = []
        for inv in investments:
            investment_evidence.append(Evidence(
                id=f"investment-value-{inv.get('id', 'unknown')}",
                type="data",
                description=f"Investment value: {inv.get('name', 'Unknown')}",
                value=inv.get("current_value_paise", 0),
                sourceId=inv.get("id", "unknown"),
            ))
            investment_sources.append(SourceReference(
                type="investment",
                id=inv.get("id", "unknown"),
                name=inv.get("name", "Unknown"),
            ))

        # Build evidence for loans
        loan_evidence: list[Evidence] = []
        loan_sources: list[SourceReference] = []
        for loan in loans:
            loan_evidence.append(Evidence(
                id=f"loan-outstanding-{loan.get('id', 'unknown')}",
                type="data",
                description=f"Loan outstanding: {loan.get('name', 'Unknown')}",
                value=loan.get("outstanding_paise", 0),
                sourceId=loan.get("id", "unknown"),
            ))
            loan_sources.append(SourceReference(
                type="loan",
                id=loan.get("id", "unknown"),
                name=loan.get("name", "Unknown"),
            ))

        # Build evidence for credit cards
        card_evidence: list[Evidence] = []
        card_sources: list[SourceReference] = []
        seen_cards: set[str] = set()
        for stmt in sorted(
            statements,
            key=lambda s: str(s.get("statement_period_to") or s.get("imported_at") or ""),
            reverse=True,
        ):
            card_key = f"{stmt.get('bank', '')}_{stmt.get('card_last4', '')}"
            if card_key not in seen_cards:
                seen_cards.add(card_key)
                due = stmt.get("total_amount_due", 0) or 0
                card_evidence.append(Evidence(
                    id=f"card-due-{card_key}",
                    type="data",
                    description=f"Card due: {stmt.get('bank', 'Unknown')} ending {stmt.get('card_last4', '****')}",
                    value=int(round(due * 100)),
                    sourceId=card_key,
                ))
                card_sources.append(SourceReference(
                    type="statement",
                    id=card_key,
                    name=f"{stmt.get('bank', 'Unknown')} Card",
                    date=stmt.get("statement_period_to"),
                ))

        # Calculate values
        account_balance_paise = sum(a.get("balance_paise", 0) for a in accounts)
        investment_value_paise = sum(i.get("current_value_paise", 0) for i in investments)
        total_assets_paise = account_balance_paise + investment_value_paise
        loan_outstanding_paise = sum(loan.get("outstanding_paise", 0) for loan in loans)
        card_outstanding_paise = sum(e.value for e in card_evidence)
        total_liabilities_paise = loan_outstanding_paise + card_outstanding_paise
        net_worth_paise = total_assets_paise - total_liabilities_paise

        # Calculate confidence
        # Start with 10000 (high), reduce for partial data
        confidence_bps = 10000
        confidence_reasons: list[str] = []

        if len(accounts) == 0:
            confidence_bps -= 2000
            confidence_reasons.append("No accounts linked")
        if len(investments) == 0:
            confidence_bps -= 1000
            confidence_reasons.append("No investments linked")
        if len(loans) == 0:
            confidence_bps -= 1000
            confidence_reasons.append("No loans linked")
        if len(card_sources) == 0:
            confidence_bps -= 1000
            confidence_reasons.append("No credit card statements")

        # Build calculation steps
        calculation_steps: list[CalculationStep] = [
            CalculationStep(
                stepId="sum-accounts",
                description="Sum all account balances",
                operation="ADD",
                inputIds=[e.id for e in account_evidence],
                outputId="assets-accounts",
                order=1,
            ),
            CalculationStep(
                stepId="sum-investments",
                description="Sum all investment values",
                operation="ADD",
                inputIds=[e.id for e in investment_evidence],
                outputId="assets-investments",
                order=2,
            ),
            CalculationStep(
                stepId="sum-assets",
                description="Total assets = accounts + investments",
                operation="ADD",
                inputIds=["assets-accounts", "assets-investments"],
                outputId="assets-total",
                order=3,
            ),
            CalculationStep(
                stepId="sum-loans",
                description="Sum all loan outstanding amounts",
                operation="ADD",
                inputIds=[e.id for e in loan_evidence],
                outputId="liabilities-loans",
                order=4,
            ),
            CalculationStep(
                stepId="sum-cards",
                description="Sum all credit card dues",
                operation="ADD",
                inputIds=[e.id for e in card_evidence],
                outputId="liabilities-cards",
                order=5,
            ),
            CalculationStep(
                stepId="sum-liabilities",
                description="Total liabilities = loans + cards",
                operation="ADD",
                inputIds=["liabilities-loans", "liabilities-cards"],
                outputId="liabilities-total",
                order=6,
            ),
            CalculationStep(
                stepId="net-worth",
                description="Net worth = assets - liabilities",
                operation="SUBTRACT",
                inputIds=["assets-total", "liabilities-total"],
                outputId="net-worth",
                order=7,
            ),
        ]

        # Build explanations
        all_evidence = account_evidence + investment_evidence + loan_evidence + card_evidence
        all_sources = account_sources + investment_sources + loan_sources + card_sources

        assets_explanation = Explanation(
            metric="assets",
            value=total_assets_paise,
            confidence=Confidence(value=confidence_bps, reason="Based on account and investment data"),
            evidence=account_evidence + investment_evidence,
            sources=account_sources + investment_sources,
            calculationSteps=calculation_steps[:3],
        )

        liabilities_explanation = Explanation(
            metric="liabilities",
            value=total_liabilities_paise,
            confidence=Confidence(value=confidence_bps, reason="Based on loan and card data"),
            evidence=loan_evidence + card_evidence,
            sources=loan_sources + card_sources,
            calculationSteps=calculation_steps[3:6],
        )

        net_worth_explanation = Explanation(
            metric="net_worth",
            value=net_worth_paise,
            confidence=Confidence(
                value=confidence_bps,
                reason=", ".join(confidence_reasons) if confidence_reasons else "Complete data available",
            ),
            evidence=all_evidence,
            sources=all_sources,
            calculationSteps=calculation_steps,
        )

        networth_explanation = NetWorthExplanation(
            netWorth=net_worth_explanation,
            assets=assets_explanation,
            liabilities=liabilities_explanation,
            confidenceReason=", ".join(confidence_reasons) if confidence_reasons else None,
        )

        return NetWorthResponse(
            net_worth_paise=net_worth_paise,
            assets={
                "total_paise": total_assets_paise,
                "accounts_paise": account_balance_paise,
                "investments_paise": investment_value_paise,
                "account_count": len(accounts),
                "investment_count": len(investments),
            },
            liabilities={
                "total_paise": total_liabilities_paise,
                "loans_paise": loan_outstanding_paise,
                "cards_paise": card_outstanding_paise,
                "loan_count": len(loans),
                "card_count": len(seen_cards),
            },
            is_partial=len(accounts) == 0 and len(investments) == 0,
            partial_reason=(
                "Add accounts and investments for complete net worth"
                if len(accounts) == 0
                else None
            ),
            last_updated=datetime.now().isoformat(),
            explanation=networth_explanation,
        )
