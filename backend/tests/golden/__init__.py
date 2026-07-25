"""Golden datasets package."""
from tests.golden.builders.credit_card_revolver import load_credit_card_revolver
from tests.golden.builders.high_debt_household import load_high_debt_household
from tests.golden.builders.irregular_income import load_irregular_income
from tests.golden.builders.normal_household import load_normal_household
from tests.golden.builders.salary_plus_loan import load_salary_plus_loan

__all__ = [
    "load_normal_household",
    "load_salary_plus_loan",
    "load_credit_card_revolver",
    "load_high_debt_household",
    "load_irregular_income",
]
