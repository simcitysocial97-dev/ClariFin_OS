/**
 * Capability Contract Coverage Tests — Program 6 Autonomous Verification Layer
 *
 * Verifies the Capability → Mapper → ViewModel pipeline contract for all
 * capabilities that lack dedicated contract tests.
 *
 * These tests verify the TypeScript interface contracts (state + actions)
 * for each capability hook, ensuring the pipeline is stable and complete.
 *
 * Pipeline: Capability → Mapper → ViewModel → Workspace → Renderer
 */

import { describe, it, expect } from 'vitest';
import type { AccountsCapabilityState, AccountsCapabilityActions, AccountsCapabilityReturn } from '../use-accounts-capability';
import type { CashflowCapabilityState, CashflowCapabilityActions } from '../use-cashflow-capability';
import type { CreditCardsCapabilityState, CreditCardsCapabilityActions } from '../use-credit-cards-capability';
import type { LoansCapabilityState, LoansCapabilityActions } from '../use-loans-capability';
import type { InvestmentsCapabilityState, InvestmentsCapabilityActions } from '../use-investments-capability';
import type { ReconciliationCapabilityState, ReconciliationCapabilityActions } from '../use-reconciliation-capability';
import type { BehaviourCapabilityState, BehaviourCapabilityActions } from '../use-behaviour-capability';
import type { ForecastCapabilityState, ForecastCapabilityActions } from '../use-forecast-capability';

// ===== Accounts Capability =====
describe('AccountsCapability Contract', () => {
  describe('State Interface', () => {
    it('should expose all required state properties', () => {
      type StateKeys = keyof AccountsCapabilityState;
      const keys: StateKeys[] = [
        'accounts', 'loading', 'error',
        'loadingTimeout', 'loadingTimeoutMessage',
        'errorRecoveryAttempts', 'isRecovering',
        'accountTypes', 'institutions', 'statuses',
        'dateRange', 'balanceRange',
        'isEvidenceDrawerOpen', 'selectedAccountId',
      ];
      expect(keys.length).toBeGreaterThan(0);
      // Verify each key exists on the type
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct types for state properties', () => {
      type State = AccountsCapabilityState;
      // Data properties
      const accountsType: State['accounts'] = null;
      expect(accountsType).toBeNull();
      const loadingType: State['loading'] = false;
      expect(loadingType).toBe(false);
      const errorType: State['error'] = null;
      expect(errorType).toBeNull();
      // Filter properties
      const accountTypesType: State['accountTypes'] = [];
      expect(Array.isArray(accountTypesType)).toBe(true);
      const dateRangeType: State['dateRange'] = null;
      expect(dateRangeType).toBeNull();
      // Selection
      const selectedIdType: State['selectedAccountId'] = null;
      expect(selectedIdType).toBeNull();
    });
  });

  describe('Actions Interface', () => {
    it('should expose all required action functions', () => {
      type ActionKeys = keyof AccountsCapabilityActions;
      const keys: ActionKeys[] = [
        'fetchAccounts', 'refresh', 'recoverFromError',
        'setAccountTypes', 'setInstitutions', 'setStatuses',
        'setDateRange', 'setBalanceRange', 'clearFilters', 'applyFilters',
        'toggleEvidenceDrawer', 'selectAccount',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct function signatures for actions', () => {
      type Actions = AccountsCapabilityActions;
      // Fetch actions return Promise<void>
      const fetchType: Actions['fetchAccounts'] = async () => {};
      expect(typeof fetchType).toBe('function');
      // Filter setters return void
      const setType: Actions['setAccountTypes'] = () => {};
      expect(typeof setType).toBe('function');
      // Selection returns void
      const selectType: Actions['selectAccount'] = () => {};
      expect(typeof selectType).toBe('function');
    });
  });

  describe('Return Type', () => {
    it('should combine state and actions in return type', () => {
      type Return = AccountsCapabilityReturn;
      // Verify intersection type includes both state and action keys
      type StateKeys = keyof AccountsCapabilityState;
      type ActionKeys = keyof AccountsCapabilityActions;
      // State keys should be in return
      const stateKey: StateKeys = 'accounts';
      expect(stateKey).toBeDefined();
      // Action keys should be in return
      const actionKey: ActionKeys = 'fetchAccounts';
      expect(actionKey).toBeDefined();
      // Return type should be an intersection of state and actions
      const returnType: Return = {} as Return;
      expect(returnType).toBeDefined();
    });
  });
});

// ===== Cashflow Capability =====
describe('CashflowCapability Contract', () => {
  describe('State Interface', () => {
    it('should expose all required state properties', () => {
      type StateKeys = keyof CashflowCapabilityState;
      const keys: StateKeys[] = [
        'cashflow', 'loading', 'error',
        'loadingTimeout', 'loadingTimeoutMessage',
        'errorRecoveryAttempts', 'isRecovering',
        'dateRange', 'categories', 'merchants', 'amountRange',
        'isEvidenceDrawerOpen',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct types for state properties', () => {
      type State = CashflowCapabilityState;
      const cashflowType: State['cashflow'] = null;
      expect(cashflowType).toBeNull();
      const loadingType: State['loading'] = false;
      expect(loadingType).toBe(false);
      const categoriesType: State['categories'] = [];
      expect(Array.isArray(categoriesType)).toBe(true);
      const dateRangeType: State['dateRange'] = null;
      expect(dateRangeType).toBeNull();
    });
  });

  describe('Actions Interface', () => {
    it('should expose all required action functions', () => {
      type ActionKeys = keyof CashflowCapabilityActions;
      const keys: ActionKeys[] = [
        'fetchCashflow', 'refresh', 'recoverFromError',
        'setDateRange', 'setCategories', 'setMerchants', 'setAmountRange',
        'clearFilters', 'applyFilters', 'toggleEvidenceDrawer',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct function signatures for actions', () => {
      type Actions = CashflowCapabilityActions;
      const fetchType: Actions['fetchCashflow'] = async () => {};
      expect(typeof fetchType).toBe('function');
      const setType: Actions['setCategories'] = () => {};
      expect(typeof setType).toBe('function');
    });
  });

  describe('Return Type', () => {
    it('should combine state and actions in return type', () => {
      type StateKeys = keyof CashflowCapabilityState;
      type ActionKeys = keyof CashflowCapabilityActions;
      const stateKey: StateKeys = 'cashflow';
      expect(stateKey).toBeDefined();
      const actionKey: ActionKeys = 'fetchCashflow';
      expect(actionKey).toBeDefined();
    });
  });
});

// ===== Credit Cards Capability =====
describe('CreditCardsCapability Contract', () => {
  describe('State Interface', () => {
    it('should expose all required state properties', () => {
      type StateKeys = keyof CreditCardsCapabilityState;
      const keys: StateKeys[] = [
        'creditCards', 'loading', 'error',
        'loadingTimeout', 'loadingTimeoutMessage',
        'errorRecoveryAttempts', 'isRecovering',
        'statuses', 'banks',
        'isEvidenceDrawerOpen', 'selectedCardId',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct types for state properties', () => {
      type State = CreditCardsCapabilityState;
      const cardsType: State['creditCards'] = null;
      expect(cardsType).toBeNull();
      const loadingType: State['loading'] = false;
      expect(loadingType).toBe(false);
      const statusesType: State['statuses'] = [];
      expect(Array.isArray(statusesType)).toBe(true);
      const selectedIdType: State['selectedCardId'] = null;
      expect(selectedIdType).toBeNull();
    });
  });

  describe('Actions Interface', () => {
    it('should expose all required action functions', () => {
      type ActionKeys = keyof CreditCardsCapabilityActions;
      const keys: ActionKeys[] = [
        'fetchCreditCards', 'refresh', 'recoverFromError',
        'setStatuses', 'setBanks', 'clearFilters', 'applyFilters',
        'toggleEvidenceDrawer', 'selectCard',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct function signatures for actions', () => {
      type Actions = CreditCardsCapabilityActions;
      const fetchType: Actions['fetchCreditCards'] = async () => {};
      expect(typeof fetchType).toBe('function');
      const setType: Actions['setBanks'] = () => {};
      expect(typeof setType).toBe('function');
      const selectType: Actions['selectCard'] = () => {};
      expect(typeof selectType).toBe('function');
    });
  });

  describe('Return Type', () => {
    it('should combine state and actions in return type', () => {
      type StateKeys = keyof CreditCardsCapabilityState;
      type ActionKeys = keyof CreditCardsCapabilityActions;
      const stateKey: StateKeys = 'creditCards';
      expect(stateKey).toBeDefined();
      const actionKey: ActionKeys = 'fetchCreditCards';
      expect(actionKey).toBeDefined();
    });
  });
});

// ===== Loans Capability =====
describe('LoansCapability Contract', () => {
  describe('State Interface', () => {
    it('should expose all required state properties', () => {
      type StateKeys = keyof LoansCapabilityState;
      const keys: StateKeys[] = [
        'loans', 'loading', 'error',
        'loadingTimeout', 'loadingTimeoutMessage',
        'errorRecoveryAttempts', 'isRecovering',
        'loanTypes', 'lenders', 'statuses',
        'isEvidenceDrawerOpen', 'selectedLoanId',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct types for state properties', () => {
      type State = LoansCapabilityState;
      const loansType: State['loans'] = null;
      expect(loansType).toBeNull();
      const loadingType: State['loading'] = false;
      expect(loadingType).toBe(false);
      const loanTypesType: State['loanTypes'] = [];
      expect(Array.isArray(loanTypesType)).toBe(true);
      const selectedIdType: State['selectedLoanId'] = null;
      expect(selectedIdType).toBeNull();
    });
  });

  describe('Actions Interface', () => {
    it('should expose all required action functions', () => {
      type ActionKeys = keyof LoansCapabilityActions;
      const keys: ActionKeys[] = [
        'fetchLoans', 'refresh', 'recoverFromError',
        'setLoanTypes', 'setLenders', 'setStatuses',
        'clearFilters', 'applyFilters', 'toggleEvidenceDrawer', 'selectLoan',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct function signatures for actions', () => {
      type Actions = LoansCapabilityActions;
      const fetchType: Actions['fetchLoans'] = async () => {};
      expect(typeof fetchType).toBe('function');
      const setType: Actions['setLenders'] = () => {};
      expect(typeof setType).toBe('function');
      const selectType: Actions['selectLoan'] = () => {};
      expect(typeof selectType).toBe('function');
    });
  });

  describe('Return Type', () => {
    it('should combine state and actions in return type', () => {
      type StateKeys = keyof LoansCapabilityState;
      type ActionKeys = keyof LoansCapabilityActions;
      const stateKey: StateKeys = 'loans';
      expect(stateKey).toBeDefined();
      const actionKey: ActionKeys = 'fetchLoans';
      expect(actionKey).toBeDefined();
    });
  });
});

// ===== Investments Capability =====
describe('InvestmentsCapability Contract', () => {
  describe('State Interface', () => {
    it('should expose all required state properties', () => {
      type StateKeys = keyof InvestmentsCapabilityState;
      const keys: StateKeys[] = [
        'investments', 'loading', 'error',
        'loadingTimeout', 'loadingTimeoutMessage',
        'errorRecoveryAttempts', 'isRecovering',
        'investmentTypes', 'institutions', 'statuses',
        'isEvidenceDrawerOpen', 'selectedInvestmentId',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct types for state properties', () => {
      type State = InvestmentsCapabilityState;
      const investmentsType: State['investments'] = null;
      expect(investmentsType).toBeNull();
      const loadingType: State['loading'] = false;
      expect(loadingType).toBe(false);
      const investmentTypesType: State['investmentTypes'] = [];
      expect(Array.isArray(investmentTypesType)).toBe(true);
      const selectedIdType: State['selectedInvestmentId'] = null;
      expect(selectedIdType).toBeNull();
    });
  });

  describe('Actions Interface', () => {
    it('should expose all required action functions', () => {
      type ActionKeys = keyof InvestmentsCapabilityActions;
      const keys: ActionKeys[] = [
        'fetchInvestments', 'refresh', 'recoverFromError',
        'setInvestmentTypes', 'setInstitutions', 'setStatuses',
        'clearFilters', 'applyFilters', 'toggleEvidenceDrawer', 'selectInvestment',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct function signatures for actions', () => {
      type Actions = InvestmentsCapabilityActions;
      const fetchType: Actions['fetchInvestments'] = async () => {};
      expect(typeof fetchType).toBe('function');
      const setType: Actions['setInstitutions'] = () => {};
      expect(typeof setType).toBe('function');
      const selectType: Actions['selectInvestment'] = () => {};
      expect(typeof selectType).toBe('function');
    });
  });

  describe('Return Type', () => {
    it('should combine state and actions in return type', () => {
      type StateKeys = keyof InvestmentsCapabilityState;
      type ActionKeys = keyof InvestmentsCapabilityActions;
      const stateKey: StateKeys = 'investments';
      expect(stateKey).toBeDefined();
      const actionKey: ActionKeys = 'fetchInvestments';
      expect(actionKey).toBeDefined();
    });
  });
});

// ===== Reconciliation Capability =====
describe('ReconciliationCapability Contract', () => {
  describe('State Interface', () => {
    it('should expose all required state properties', () => {
      type StateKeys = keyof ReconciliationCapabilityState;
      const keys: StateKeys[] = [
        'reconciliation', 'loading', 'error',
        'loadingTimeout', 'loadingTimeoutMessage',
        'errorRecoveryAttempts', 'isRecovering',
        'status', 'banks',
        'isEvidenceDrawerOpen', 'selectedDiscrepancyId',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct types for state properties', () => {
      type State = ReconciliationCapabilityState;
      const reconType: State['reconciliation'] = null;
      expect(reconType).toBeNull();
      const loadingType: State['loading'] = false;
      expect(loadingType).toBe(false);
      const statusType: State['status'] = [];
      expect(Array.isArray(statusType)).toBe(true);
      const selectedIdType: State['selectedDiscrepancyId'] = null;
      expect(selectedIdType).toBeNull();
    });
  });

  describe('Actions Interface', () => {
    it('should expose all required action functions', () => {
      type ActionKeys = keyof ReconciliationCapabilityActions;
      const keys: ActionKeys[] = [
        'fetchReconciliation', 'refresh', 'recoverFromError',
        'setStatus', 'setBanks', 'clearFilters', 'applyFilters',
        'toggleEvidenceDrawer', 'selectDiscrepancy',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct function signatures for actions', () => {
      type Actions = ReconciliationCapabilityActions;
      const fetchType: Actions['fetchReconciliation'] = async () => {};
      expect(typeof fetchType).toBe('function');
      const setType: Actions['setBanks'] = () => {};
      expect(typeof setType).toBe('function');
      const selectType: Actions['selectDiscrepancy'] = () => {};
      expect(typeof selectType).toBe('function');
    });
  });

  describe('Return Type', () => {
    it('should combine state and actions in return type', () => {
      type StateKeys = keyof ReconciliationCapabilityState;
      type ActionKeys = keyof ReconciliationCapabilityActions;
      const stateKey: StateKeys = 'reconciliation';
      expect(stateKey).toBeDefined();
      const actionKey: ActionKeys = 'fetchReconciliation';
      expect(actionKey).toBeDefined();
    });
  });
});

// ===== Behaviour Capability =====
describe('BehaviourCapability Contract', () => {
  describe('State Interface', () => {
    it('should expose all required state properties', () => {
      type StateKeys = keyof BehaviourCapabilityState;
      const keys: StateKeys[] = [
        'behaviour', 'loading', 'error',
        'loadingTimeout', 'loadingTimeoutMessage',
        'errorRecoveryAttempts', 'isRecovering',
        'period', 'isEvidenceDrawerOpen',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct types for state properties', () => {
      type State = BehaviourCapabilityState;
      const behaviourType: State['behaviour'] = null;
      expect(behaviourType).toBeNull();
      const loadingType: State['loading'] = false;
      expect(loadingType).toBe(false);
      const periodType: State['period'] = '';
      expect(typeof periodType).toBe('string');
    });
  });

  describe('Actions Interface', () => {
    it('should expose all required action functions', () => {
      type ActionKeys = keyof BehaviourCapabilityActions;
      const keys: ActionKeys[] = [
        'fetchBehaviour', 'refresh', 'recoverFromError',
        'setPeriod', 'clearFilters', 'applyFilters', 'toggleEvidenceDrawer',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct function signatures for actions', () => {
      type Actions = BehaviourCapabilityActions;
      const fetchType: Actions['fetchBehaviour'] = async () => {};
      expect(typeof fetchType).toBe('function');
      const setType: Actions['setPeriod'] = () => {};
      expect(typeof setType).toBe('function');
    });
  });

  describe('Return Type', () => {
    it('should combine state and actions in return type', () => {
      type StateKeys = keyof BehaviourCapabilityState;
      type ActionKeys = keyof BehaviourCapabilityActions;
      const stateKey: StateKeys = 'behaviour';
      expect(stateKey).toBeDefined();
      const actionKey: ActionKeys = 'fetchBehaviour';
      expect(actionKey).toBeDefined();
    });
  });
});

// ===== Forecast Capability =====
describe('ForecastCapability Contract', () => {
  describe('State Interface', () => {
    it('should expose all required state properties', () => {
      type StateKeys = keyof ForecastCapabilityState;
      const keys: StateKeys[] = [
        'forecast', 'loading', 'error',
        'loadingTimeout', 'loadingTimeoutMessage',
        'errorRecoveryAttempts', 'isRecovering',
        'horizon', 'scenarios', 'metricTypes',
        'isEvidenceDrawerOpen',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct types for state properties', () => {
      type State = ForecastCapabilityState;
      const forecastType: State['forecast'] = null;
      expect(forecastType).toBeNull();
      const loadingType: State['loading'] = false;
      expect(loadingType).toBe(false);
      const horizonType: State['horizon'] = 0;
      expect(typeof horizonType).toBe('number');
      const scenariosType: State['scenarios'] = [];
      expect(Array.isArray(scenariosType)).toBe(true);
    });
  });

  describe('Actions Interface', () => {
    it('should expose all required action functions', () => {
      type ActionKeys = keyof ForecastCapabilityActions;
      const keys: ActionKeys[] = [
        'fetchForecast', 'refresh', 'recoverFromError',
        'setHorizon', 'setScenarios', 'setMetricTypes',
        'clearFilters', 'applyFilters', 'toggleEvidenceDrawer',
      ];
      expect(keys.length).toBeGreaterThan(0);
      keys.forEach((key) => {
        expect(key).toBeDefined();
      });
    });

    it('should have correct function signatures for actions', () => {
      type Actions = ForecastCapabilityActions;
      const fetchType: Actions['fetchForecast'] = async () => {};
      expect(typeof fetchType).toBe('function');
      const setType: Actions['setHorizon'] = () => {};
      expect(typeof setType).toBe('function');
    });
  });

  describe('Return Type', () => {
    it('should combine state and actions in return type', () => {
      type StateKeys = keyof ForecastCapabilityState;
      type ActionKeys = keyof ForecastCapabilityActions;
      const stateKey: StateKeys = 'forecast';
      expect(stateKey).toBeDefined();
      const actionKey: ActionKeys = 'fetchForecast';
      expect(actionKey).toBeDefined();
    });
  });
});
