"""Loan Scenario Repository."""


from src.models.loan_scenario import LoanScenario, LoanScenarioCreate
from src.repositories.base import BaseRepository


class LoanScenarioRepository(BaseRepository):
    """Repository for loan scenario operations."""

    def get_by_loan_id(self, loan_id: int) -> list[LoanScenario]:
        """Get all scenarios for a loan."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT id, loan_id, scenario_name, prepayment_paise,
                       prepayment_date, new_tenure_months, new_emi_paise,
                       interest_saved_paise, months_saved, created_at
                FROM loan_scenarios
                WHERE loan_id = ?
                ORDER BY created_at DESC
                """,
                (loan_id,),
            ).fetchall()
        return [LoanScenario.from_db_row(dict(r)) for r in rows]

    def create(self, scenario: LoanScenarioCreate) -> int:
        """Create a new loan scenario record."""
        with self._get_conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO loan_scenarios (
                    loan_id, scenario_name, prepayment_paise,
                    prepayment_date, new_tenure_months, new_emi_paise,
                    interest_saved_paise, months_saved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scenario.loan_id,
                    scenario.scenario_name,
                    scenario.prepayment_paise,
                    scenario.prepayment_date,
                    scenario.new_tenure_months,
                    scenario.new_emi_paise,
                    scenario.interest_saved_paise,
                    scenario.months_saved,
                ),
            )
            conn.commit()
        return cur.lastrowid or 0

    def delete(self, scenario_id: int) -> bool:
        """Delete a scenario."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM loan_scenarios WHERE id = ?", (scenario_id,))
            conn.commit()
            changes = conn.execute("SELECT changes()").fetchone()
        return bool(changes[0]) if changes else False

    def delete_all_for_loan(self, loan_id: int) -> int:
        """Delete all scenarios for a loan. Returns count deleted."""
        with self._get_conn() as conn:
            cur = conn.execute(
                "DELETE FROM loan_scenarios WHERE loan_id = ?",
                (loan_id,),
            )
            conn.commit()
        return cur.rowcount
