"""Golden characterization tests for behaviour_engine (financial_events / wellness / profile groups).

Characterization tests that lock the exact outputs of the engine's pure
financial-events / wellness / personality functions for fixed inputs, so that
any behavior-changing mutation is detected. Values computed from the canonical
implementation; inputs use Decimal where the functions require it.
"""
from __future__ import annotations

from decimal import Decimal

from engines.behaviour_engine.credit_dependency import (
    artificial_income_flag,
    household_divergence,
    liquidity_extraction_frequency,
    revolver_ratio,
    transactor_vs_revolver,
)
from engines.behaviour_engine.profile import (
    _build_explanation,
    classify_financial_personality,
)
from engines.behaviour_engine.wellness import (
    classify_wellness_band,
    compute_wellness_score,
)


def tvr_call(events):
    return transactor_vs_revolver(events, "card_1")


def cws_call(args):
    return compute_wellness_score(*args)


def cfp_call(args):
    return classify_financial_personality(*args)


def be_call(args):
    return _build_explanation(*args)


artificialincomeflag_rich_IN = \
[{'id': 1,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'cash_advance',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-05',
  'amount_paise': 10000,
  'liability_change_paise': 10000,
  'links': []},
 {'id': 2,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'credit_card_cash_advance',
  'lifecycle_state': 'rolls_over',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-20',
  'amount_paise': 20000,
  'liability_change_paise': 20000,
  'links': []},
 {'id': 3,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'liability_increase',
  'lifecycle_state': 'settled',
  'month_bucket': '2024-02',
  'date_iso': '2024-02-10',
  'amount_paise': 50000,
  'liability_change_paise': 0,
  'links': []},
 {'id': 4,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'credit_card_cash_advance',
  'lifecycle_state': 'partially_settled',
  'month_bucket': '2024-02',
  'date_iso': '2024-02-15',
  'amount_paise': 15000,
  'liability_change_paise': 15000,
  'links': []},
 {'id': 5,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'liability_increase',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-01',
  'amount_paise': 0,
  'liability_change_paise': 0,
  'links': [{'link_type': 'funds', 'linked_event_id': 6}]},
 {'id': 6,
  'account_id': 'card_2',
  'owner_id': 'spouse',
  'household_id': 'primary',
  'event_type': '',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-01',
  'amount_paise': 0,
  'liability_change_paise': 0,
  'links': []}]
artificialincomeflag_rich_OUT = \
{'flag': True,
 'artificial_income_paise': 95000,
 'excluded_event_ids': [1, 2, 3, 4],
 'explanation': 'Found 4 artificial income events totaling ₹950.00'}

def test_golden_artificialincomeflag_rich():
    assert artificial_income_flag(artificialincomeflag_rich_IN) == artificialincomeflag_rich_OUT

artificialincomeflag_empty_IN = \
[]
artificialincomeflag_empty_OUT = \
{'flag': False,
 'artificial_income_paise': 0,
 'excluded_event_ids': [],
 'explanation': 'No artificial income detected'}

def test_golden_artificialincomeflag_empty():
    assert artificial_income_flag(artificialincomeflag_empty_IN) == artificialincomeflag_empty_OUT

tvrcall_rich_IN = \
[{'id': 1,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'cash_advance',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-05',
  'amount_paise': 10000,
  'liability_change_paise': 10000,
  'links': []},
 {'id': 2,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'credit_card_cash_advance',
  'lifecycle_state': 'rolls_over',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-20',
  'amount_paise': 20000,
  'liability_change_paise': 20000,
  'links': []},
 {'id': 3,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'liability_increase',
  'lifecycle_state': 'settled',
  'month_bucket': '2024-02',
  'date_iso': '2024-02-10',
  'amount_paise': 50000,
  'liability_change_paise': 0,
  'links': []},
 {'id': 4,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'credit_card_cash_advance',
  'lifecycle_state': 'partially_settled',
  'month_bucket': '2024-02',
  'date_iso': '2024-02-15',
  'amount_paise': 15000,
  'liability_change_paise': 15000,
  'links': []},
 {'id': 5,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'liability_increase',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-01',
  'amount_paise': 0,
  'liability_change_paise': 0,
  'links': [{'link_type': 'funds', 'linked_event_id': 6}]},
 {'id': 6,
  'account_id': 'card_2',
  'owner_id': 'spouse',
  'household_id': 'primary',
  'event_type': '',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-01',
  'amount_paise': 0,
  'liability_change_paise': 0,
  'links': []}]
tvrcall_rich_OUT = \
{'type': 'revolver', 'confidence': Decimal('0.75'), 'settled_count': 1, 'revolving_count': 3}

def test_golden_tvrcall_rich():
    assert tvr_call(tvrcall_rich_IN) == tvrcall_rich_OUT

tvrcall_empty_IN = \
[]
tvrcall_empty_OUT = \
{'type': 'transactor', 'confidence': Decimal('0'), 'settled_count': 0, 'revolving_count': 0}

def test_golden_tvrcall_empty():
    assert tvr_call(tvrcall_empty_IN) == tvrcall_empty_OUT

revolverratio_rich_IN = \
[{'id': 1,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'cash_advance',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-05',
  'amount_paise': 10000,
  'liability_change_paise': 10000,
  'links': []},
 {'id': 2,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'credit_card_cash_advance',
  'lifecycle_state': 'rolls_over',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-20',
  'amount_paise': 20000,
  'liability_change_paise': 20000,
  'links': []},
 {'id': 3,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'liability_increase',
  'lifecycle_state': 'settled',
  'month_bucket': '2024-02',
  'date_iso': '2024-02-10',
  'amount_paise': 50000,
  'liability_change_paise': 0,
  'links': []},
 {'id': 4,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'credit_card_cash_advance',
  'lifecycle_state': 'partially_settled',
  'month_bucket': '2024-02',
  'date_iso': '2024-02-15',
  'amount_paise': 15000,
  'liability_change_paise': 15000,
  'links': []},
 {'id': 5,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'liability_increase',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-01',
  'amount_paise': 0,
  'liability_change_paise': 0,
  'links': [{'link_type': 'funds', 'linked_event_id': 6}]},
 {'id': 6,
  'account_id': 'card_2',
  'owner_id': 'spouse',
  'household_id': 'primary',
  'event_type': '',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-01',
  'amount_paise': 0,
  'liability_change_paise': 0,
  'links': []}]
revolverratio_rich_OUT = \
Decimal('1.0')

def test_golden_revolverratio_rich():
    assert revolver_ratio(revolverratio_rich_IN) == revolverratio_rich_OUT

revolverratio_empty_IN = \
[]
revolverratio_empty_OUT = \
Decimal('0')

def test_golden_revolverratio_empty():
    assert revolver_ratio(revolverratio_empty_IN) == revolverratio_empty_OUT

liquidityextractionfrequency_rich_IN = \
[{'id': 1,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'cash_advance',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-05',
  'amount_paise': 10000,
  'liability_change_paise': 10000,
  'links': []},
 {'id': 2,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'credit_card_cash_advance',
  'lifecycle_state': 'rolls_over',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-20',
  'amount_paise': 20000,
  'liability_change_paise': 20000,
  'links': []},
 {'id': 3,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'liability_increase',
  'lifecycle_state': 'settled',
  'month_bucket': '2024-02',
  'date_iso': '2024-02-10',
  'amount_paise': 50000,
  'liability_change_paise': 0,
  'links': []},
 {'id': 4,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'credit_card_cash_advance',
  'lifecycle_state': 'partially_settled',
  'month_bucket': '2024-02',
  'date_iso': '2024-02-15',
  'amount_paise': 15000,
  'liability_change_paise': 15000,
  'links': []},
 {'id': 5,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'liability_increase',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-01',
  'amount_paise': 0,
  'liability_change_paise': 0,
  'links': [{'link_type': 'funds', 'linked_event_id': 6}]},
 {'id': 6,
  'account_id': 'card_2',
  'owner_id': 'spouse',
  'household_id': 'primary',
  'event_type': '',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-01',
  'amount_paise': 0,
  'liability_change_paise': 0,
  'links': []}]
liquidityextractionfrequency_rich_OUT = \
{'count': 3, 'total_paise': 90000, 'avg_days_between': 13}

def test_golden_liquidityextractionfrequency_rich():
    assert liquidity_extraction_frequency(liquidityextractionfrequency_rich_IN) == liquidityextractionfrequency_rich_OUT

liquidityextractionfrequency_empty_IN = \
[]
liquidityextractionfrequency_empty_OUT = \
{'count': 0, 'total_paise': 0, 'avg_days_between': None}

def test_golden_liquidityextractionfrequency_empty():
    assert liquidity_extraction_frequency(liquidityextractionfrequency_empty_IN) == liquidityextractionfrequency_empty_OUT

householddivergence_rich_IN = \
[{'id': 1,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'cash_advance',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-05',
  'amount_paise': 10000,
  'liability_change_paise': 10000,
  'links': []},
 {'id': 2,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'credit_card_cash_advance',
  'lifecycle_state': 'rolls_over',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-20',
  'amount_paise': 20000,
  'liability_change_paise': 20000,
  'links': []},
 {'id': 3,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'liability_increase',
  'lifecycle_state': 'settled',
  'month_bucket': '2024-02',
  'date_iso': '2024-02-10',
  'amount_paise': 50000,
  'liability_change_paise': 0,
  'links': []},
 {'id': 4,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'credit_card_cash_advance',
  'lifecycle_state': 'partially_settled',
  'month_bucket': '2024-02',
  'date_iso': '2024-02-15',
  'amount_paise': 15000,
  'liability_change_paise': 15000,
  'links': []},
 {'id': 5,
  'account_id': 'card_1',
  'owner_id': 'self',
  'household_id': 'primary',
  'event_type': 'liability_increase',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-01',
  'amount_paise': 0,
  'liability_change_paise': 0,
  'links': [{'link_type': 'funds', 'linked_event_id': 6}]},
 {'id': 6,
  'account_id': 'card_2',
  'owner_id': 'spouse',
  'household_id': 'primary',
  'event_type': '',
  'lifecycle_state': 'open',
  'month_bucket': '2024-01',
  'date_iso': '2024-01-01',
  'amount_paise': 0,
  'liability_change_paise': 0,
  'links': []}]
householddivergence_rich_OUT = \
{'flag': True,
 'divergent_links': [{'from_owner': 'self',
                      'to_owner': 'spouse',
                      'link_type': 'funds',
                      'event_id': 5,
                      'linked_event_id': 6,
                      'household_id': 'primary'}],
 'count': 1}

def test_golden_householddivergence_rich():
    assert household_divergence(householddivergence_rich_IN) == householddivergence_rich_OUT

householddivergence_empty_IN = \
[]
householddivergence_empty_OUT = \
{'flag': False, 'divergent_links': [], 'count': 0}

def test_golden_householddivergence_empty():
    assert household_divergence(householddivergence_empty_IN) == householddivergence_empty_OUT

cwscall_mid_IN = \
(Decimal('0.6'), 30, Decimal('0.15'), Decimal('0.7'), Decimal('0.1'), Decimal('0.2'), Decimal('0.3'))
cwscall_mid_OUT = \
Decimal('61.0000')

def test_golden_cwscall_mid():
    assert cws_call(cwscall_mid_IN) == cwscall_mid_OUT

cwscall_zero_IN = \
(Decimal('0'), 0, Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0'), Decimal('0'))
cwscall_zero_OUT = \
Decimal('35.000')

def test_golden_cwscall_zero():
    assert cws_call(cwscall_zero_IN) == cwscall_zero_OUT

cwscall_high_IN = \
(Decimal('0.95'), 5, Decimal('0.40'), Decimal('0.9'), Decimal('0.05'), Decimal('0.05'), Decimal('0.1'))
cwscall_high_OUT = \
Decimal('85.62500')

def test_golden_cwscall_high():
    assert cws_call(cwscall_high_IN) == cwscall_high_OUT

classifywellnessband_excellent_IN = \
Decimal('92')
classifywellnessband_excellent_OUT = \
'Excellent'

def test_golden_classifywellnessband_excellent():
    assert classify_wellness_band(classifywellnessband_excellent_IN) == classifywellnessband_excellent_OUT

classifywellnessband_healthy_IN = \
Decimal('80')
classifywellnessband_healthy_OUT = \
'Healthy'

def test_golden_classifywellnessband_healthy():
    assert classify_wellness_band(classifywellnessband_healthy_IN) == classifywellnessband_healthy_OUT

classifywellnessband_developing_IN = \
Decimal('60')
classifywellnessband_developing_OUT = \
'Developing'

def test_golden_classifywellnessband_developing():
    assert classify_wellness_band(classifywellnessband_developing_IN) == classifywellnessband_developing_OUT

classifywellnessband_risk_IN = \
Decimal('40')
classifywellnessband_risk_OUT = \
'Risk'

def test_golden_classifywellnessband_risk():
    assert classify_wellness_band(classifywellnessband_risk_IN) == classifywellnessband_risk_OUT

classifywellnessband_critical_IN = \
Decimal('10')
classifywellnessband_critical_OUT = \
'Critical'

def test_golden_classifywellnessband_critical():
    assert classify_wellness_band(classifywellnessband_critical_IN) == classifywellnessband_critical_OUT

cfpcall_saver_IN = \
(Decimal('0.30'), Decimal('0.05'), Decimal('0.10'), Decimal('0.20'), Decimal('0.10'), Decimal('0.10'), 200)
cfpcall_saver_OUT = \
('SAVER',
 Decimal('0.75'),
 'You are classified as SAVER because your savings rate is 30.0% (above 20% threshold) and you do not rely '
 'on credit for lifestyle expenses (borrowed lifestyle ratio 5.0%).')

def test_golden_cfpcall_saver():
    assert cfp_call(cfpcall_saver_IN) == cfpcall_saver_OUT

cfpcall_debt_dependent_IN = \
(Decimal('0.05'), Decimal('0.30'), Decimal('0.60'), Decimal('0.20'), Decimal('0.10'), Decimal('0.10'), 200)
cfpcall_debt_dependent_OUT = \
('DEBT_DEPENDENT',
 Decimal('0.70'),
 'You are classified as DEBT_DEPENDENT because your borrowed lifestyle ratio is 30.0% (above 20% threshold), '
 'indicating significant reliance on credit for daily expenses.')

def test_golden_cfpcall_debt_dependent():
    assert cfp_call(cfpcall_debt_dependent_IN) == cfpcall_debt_dependent_OUT

cfpcall_spender_IN = \
(Decimal('0.10'), Decimal('0.05'), Decimal('0.10'), Decimal('0.50'), Decimal('0.40'), Decimal('0.60'), 200)
cfpcall_spender_OUT = \
('DEBT_OPTIMIZER',
 Decimal('0.70'),
 'You are classified as DEBT_OPTIMIZER because you use credit responsibly (revolver ratio 10.0%, indicating '
 'primarily on-time payments) while maintaining positive savings (10.0%).')

def test_golden_cfpcall_spender():
    assert cfp_call(cfpcall_spender_IN) == cfpcall_spender_OUT

cfpcall_balanced_IN = \
(Decimal('0.15'), Decimal('0.05'), Decimal('0.10'), Decimal('0.20'), Decimal('0.10'), Decimal('0.10'), 200)
cfpcall_balanced_OUT = \
('DEBT_OPTIMIZER',
 Decimal('0.70'),
 'You are classified as DEBT_OPTIMIZER because you use credit responsibly (revolver ratio 10.0%, indicating '
 'primarily on-time payments) while maintaining positive savings (15.0%).')

def test_golden_cfpcall_balanced():
    assert cfp_call(cfpcall_balanced_IN) == cfpcall_balanced_OUT

cfpcall_debt_optimizer_IN = \
(Decimal('0.20'), Decimal('0.05'), Decimal('0.10'), Decimal('0.20'), Decimal('0.10'), Decimal('0.10'), 200)
cfpcall_debt_optimizer_OUT = \
('DEBT_OPTIMIZER',
 Decimal('0.70'),
 'You are classified as DEBT_OPTIMIZER because you use credit responsibly (revolver ratio 10.0%, indicating '
 'primarily on-time payments) while maintaining positive savings (20.0%).')

def test_golden_cfpcall_debt_optimizer():
    assert cfp_call(cfpcall_debt_optimizer_IN) == cfpcall_debt_optimizer_OUT

# SKIP _is_debt_dependent[true] -> TypeError("_is_debt_dependent() missing 2 required positional arguments: 'credit_revolver_ratio' and 'savings_rate'")
# SKIP _is_debt_dependent[false] -> TypeError("_is_debt_dependent() missing 2 required positional arguments: 'credit_revolver_ratio' and 'savings_rate'")
# SKIP _is_saver[true] -> TypeError("_is_saver() missing 2 required positional arguments: 'borrowed_lifestyle_ratio' and 'credit_revolver_ratio'")
# SKIP _is_saver[false] -> TypeError("_is_saver() missing 2 required positional arguments: 'borrowed_lifestyle_ratio' and 'credit_revolver_ratio'")
# SKIP _is_debt_optimizer[true] -> TypeError("_is_debt_optimizer() missing 1 required positional argument: 'credit_revolver_ratio'")
# SKIP _is_debt_optimizer[false] -> TypeError("_is_debt_optimizer() missing 1 required positional argument: 'credit_revolver_ratio'")
# SKIP _is_spender[true] -> TypeError("_is_spender() missing 2 required positional arguments: 'impulse_transaction_ratio' and 'lifestyle_creep_index'")
# SKIP _is_spender[false] -> TypeError("_is_spender() missing 2 required positional arguments: 'impulse_transaction_ratio' and 'lifestyle_creep_index'")
becall_saver_IN = \
('SAVER', Decimal('0.25'), Decimal('0.05'), Decimal('0.10'))
becall_saver_OUT = \
('You are classified as SAVER because your savings rate is 25.0% (above 20% threshold) and you do not rely '
 'on credit for lifestyle expenses (borrowed lifestyle ratio 5.0%).')

def test_golden_becall_saver():
    assert be_call(becall_saver_IN) == becall_saver_OUT

becall_debt_dependent_IN = \
('DEBT_DEPENDENT', Decimal('0.05'), Decimal('0.30'), Decimal('0.60'))
becall_debt_dependent_OUT = \
('You are classified as DEBT_DEPENDENT because your borrowed lifestyle ratio is 30.0% (above 20% threshold), '
 'indicating significant reliance on credit for daily expenses.')

def test_golden_becall_debt_dependent():
    assert be_call(becall_debt_dependent_IN) == becall_debt_dependent_OUT
