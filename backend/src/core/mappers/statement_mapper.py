"""
Statement Mapper
================

Transforms statement domain objects into StatementDTO instances.
This is the ONLY location where statement API responses are constructed.
"""

from typing import Any

from src.core.dtos.statement_dto import StatementDTO


def _format_inr(paise: int) -> str:
    """Format paise to Indian Rupee string with lakh/crore grouping."""
    if paise is None:
        return "₹0.00"
    negative = paise < 0
    paise = abs(paise)
    integer_part = paise // 100
    decimal_part = f"{(paise % 100):02d}"
    s = str(integer_part)
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        remaining = s[:-3]
        groups = []
        while remaining:
            groups.append(remaining[-2:] if len(remaining) >= 2 else remaining)
            remaining = remaining[:-2]
        groups.reverse()
        formatted = ",".join(groups) + "," + last3
    result = f"₹{formatted}.{decimal_part}"
    return f"-{result}" if negative else result


class StatementMapper:
    """
    Mapper for statement domain objects to DTOs.

    Responsibilities:
    - Transform statement data to StatementDTO
    - Convert rupee amounts to paise canonical form
    - Generate display fields
    """

    @staticmethod
    def to_dto(stmt: dict[str, Any]) -> StatementDTO:
        """
        Convert a statement record to StatementDTO.

        Args:
            stmt: Statement dict from database

        Returns:
            StatementDTO instance
        """
        # Extract and convert monetary values to paise
        total_debit_rupees = float(stmt.get("total_debit") or 0)
        total_credit_rupees = float(stmt.get("total_credit") or 0)
        total_due_rupees = float(stmt.get("total_amount_due") or 0)
        min_due_rupees = float(stmt.get("minimum_amount_due") or 0)
        diff_rupees = float(stmt.get("validation_difference") or 0)

        total_debit_paise = int(round(total_debit_rupees * 100))
        total_credit_paise = int(round(total_credit_rupees * 100))
        total_due_paise = int(round(total_due_rupees * 100))
        min_due_paise = int(round(min_due_rupees * 100))
        diff_paise = int(round(diff_rupees * 100))
        extracted_net_paise = total_debit_paise - total_credit_paise

        # Validation badge
        validation_status = stmt.get("validation_status") or "pending"
        badge_text = (
            "✅ Exact Match"
            if validation_status == "exact_match"
            else (
                f"⚠️ Close (₹{diff_rupees:,.0f} off)"
                if validation_status == "close_match"
                else (
                    f"❌ Mismatch (₹{diff_rupees:,.0f})"
                    if validation_status == "mismatch"
                    else (
                        "— No Data"
                        if validation_status == "no_metadata"
                        else "⏳ Pending"
                    )
                )
            )
        )
        badge_color = (
            "green"
            if validation_status == "exact_match"
            else (
                "amber"
                if validation_status == "close_match"
                else "red"
                if validation_status == "mismatch"
                else "gray"
            )
        )

        card_last4 = stmt.get("card_last4") or ""

        return StatementDTO(
            id=stmt.get("id") or 0,
            bank=stmt.get("bank") or "",
            file_name=stmt.get("file_name") or "",
            card_last4=card_last4,
            card_display=f"****{card_last4}" if card_last4 else "",
            period_from=stmt.get("statement_period_from") or "",
            period_to=stmt.get("statement_period_to") or "",
            period_display=(
                f"{stmt.get('statement_period_from')} – {stmt.get('statement_period_to')}"
                if stmt.get("statement_period_from")
                else ""
            ),
            transaction_count=stmt.get("transaction_count", 0),
            total_debit_paise=total_debit_paise,
            total_credit_paise=total_credit_paise,
            total_due_paise=total_due_paise,
            min_due_paise=min_due_paise,
            extracted_net_paise=extracted_net_paise,
            validation_difference_paise=diff_paise,
            total_debit_display=_format_inr(total_debit_paise),
            total_credit_display=_format_inr(total_credit_paise),
            total_due_display=_format_inr(total_due_paise) if total_due_paise else "—",
            extracted_net_display=_format_inr(extracted_net_paise),
            min_due_display=_format_inr(min_due_paise) if min_due_paise else "",
            due_date=stmt.get("payment_due_date") or "",
            validation_status=validation_status,
            badge_text=badge_text,
            badge_color=badge_color,
        )
