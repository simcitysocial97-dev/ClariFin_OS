"""Golden datasets package."""
from tests.golden.datasets.credit_card_revolver import load_credit_card_revolver
from tests.golden.datasets.high_debt_household import load_high_debt_household
from tests.golden.datasets.irregular_income import load_irregular_income
from tests.golden.datasets.normal_household import load_normal_household
from tests.golden.datasets.salary_plus_loan import load_salary_plus_loan

__all__ = [
    "load_normal_household",
    "load_salary_plus_loan",
    "load_credit_card_revolver",
    "load_high_debt_household",
    "load_irregular_income",
]
