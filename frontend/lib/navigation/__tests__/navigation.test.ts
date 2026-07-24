/**
 * Navigation Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Tests for navigation utilities.
 */

import { describe, it, expect } from 'vitest';
import {
  getCategoryWorkspaceUrl,
  getCategoryWorkspaceUrlByName,
  hasCategoryNavigation,
} from '../category-navigation';
import {
  getMerchantWorkspaceUrl,
  getMerchantWorkspaceUrlByName,
  hasMerchantNavigation,
} from '../merchant-navigation';
import {
  getDateWorkspaceUrl,
  getMonthWorkspaceUrl,
  hasDateNavigation,
} from '../date-navigation';
import {
  getAccountWorkspaceUrl,
  hasAccountNavigation,
} from '../account-navigation';
import {
  getBalanceWorkspaceUrl,
  hasBalanceNavigation,
} from '../balance-navigation';
import {
  getReconciliationWorkspaceUrl,
  hasReconciliationNavigation,
} from '../reconciliation-navigation';
import {
  getImportWorkspaceUrl,
  hasImportNavigation,
} from '../import-navigation';
import {
  getAdjustmentWorkspaceUrl,
  hasAdjustmentNavigation,
} from '../adjustment-navigation';
import { parseNavigationState, buildNavigationUrl } from '../persistence';
import {
  createNavigationError,
  getNavigationErrorMessage,
  isNavigationErrorRecoverable,
} from '../error-handling';
import { isNavigationShortcut } from '../keyboard';
import type { TransactionViewModel } from '@/types/transaction-view-model';

const mockTransaction: TransactionViewModel = {
  id: '1',
  date: '2024-01-15',
  date_formatted: 'Jan 15, 2024',
  description: 'Test transaction',
  amount: { paise: 10000, rupees: 100 },
  transaction_type: 'debit',
  category_id: 'cat1',
  category_name: 'Food',
  merchant_id: 'merch1',
  merchant_name: 'Test Merchant',
  account_id: 'acc1',
  account_name: 'Test Account',
  bank: 'Test Bank',
  evidence: [],
  import_lineage: { file_id: '1', filename: 'test.pdf', import_date: '2024-01-15', source_type: 'pdf', bank: 'Test Bank' },
};

describe('Category Navigation', () => {
  it('generates correct URL for transaction', () => {
    const url = getCategoryWorkspaceUrl(mockTransaction);
    expect(url).toBe('/transactions?category=cat1');
  });

  it('generates correct URL for category name', () => {
    const url = getCategoryWorkspaceUrlByName('Food');
    expect(url).toBe('/transactions?category=Food');
  });

  it('detects category navigation availability', () => {
    expect(hasCategoryNavigation(mockTransaction)).toBe(true);
  });

  it('returns false when no category', () => {
    const txWithoutCategory = { ...mockTransaction, category_id: undefined, category_name: undefined };
    expect(hasCategoryNavigation(txWithoutCategory)).toBe(false);
  });
});

describe('Merchant Navigation', () => {
  it('generates correct URL for transaction', () => {
    const url = getMerchantWorkspaceUrl(mockTransaction);
    expect(url).toBe('/transactions?merchant=merch1');
  });

  it('generates correct URL for merchant name', () => {
    const url = getMerchantWorkspaceUrlByName('Test Merchant');
    expect(url).toBe('/transactions?merchant=Test%20Merchant');
  });

  it('detects merchant navigation availability', () => {
    expect(hasMerchantNavigation(mockTransaction)).toBe(true);
  });
});

describe('Date Navigation', () => {
  it('generates correct URL for transaction', () => {
    const url = getDateWorkspaceUrl(mockTransaction);
    expect(url).toBe('/transactions?date=2024-01-15');
  });

  it('generates correct URL for month', () => {
    const txWithMonth = { ...mockTransaction, month_key: '2024-01' };
    const url = getMonthWorkspaceUrl(txWithMonth);
    expect(url).toBe('/transactions?month=2024-01');
  });

  it('detects date navigation availability', () => {
    expect(hasDateNavigation(mockTransaction)).toBe(true);
  });
});

describe('Account Navigation', () => {
  it('generates correct URL for transaction', () => {
    const url = getAccountWorkspaceUrl(mockTransaction);
    expect(url).toBe('/accounts/acc1/transactions');
  });

  it('detects account navigation availability', () => {
    expect(hasAccountNavigation(mockTransaction)).toBe(true);
  });
});

describe('Balance Navigation', () => {
  it('generates correct URL for transaction', () => {
    const url = getBalanceWorkspaceUrl(mockTransaction);
    expect(url).toBe('/accounts/acc1/balance');
  });

  it('detects balance navigation availability', () => {
    const txWithBalance = { ...mockTransaction, balance: { paise: 10000, rupees: 100 } };
    expect(hasBalanceNavigation(txWithBalance)).toBe(true);
  });
});

describe('Reconciliation Navigation', () => {
  it('generates correct URL for transaction', () => {
    const txWithReconciliation = { ...mockTransaction, reconciliation_id: 'rec1' };
    const url = getReconciliationWorkspaceUrl(txWithReconciliation);
    expect(url).toBe('/reconciliation/rec1');
  });

  it('detects reconciliation navigation availability', () => {
    const txWithReconciliation = { ...mockTransaction, reconciliation_id: 'rec1' };
    expect(hasReconciliationNavigation(txWithReconciliation)).toBe(true);
  });
});

describe('Import Navigation', () => {
  it('generates correct URL for transaction', () => {
    const url = getImportWorkspaceUrl(mockTransaction);
    expect(url).toBe('/import/1/transactions');
  });

  it('detects import navigation availability', () => {
    expect(hasImportNavigation(mockTransaction)).toBe(true);
  });
});

describe('Adjustment Navigation', () => {
  it('generates correct URL for transaction', () => {
    const txWithAdjustment = { ...mockTransaction, adjustment_id: 'adj1' };
    const url = getAdjustmentWorkspaceUrl(txWithAdjustment);
    expect(url).toBe('/adjustments/adj1/transactions');
  });

  it('detects adjustment navigation availability', () => {
    const txWithAdjustment = { ...mockTransaction, is_adjusted: true };
    expect(hasAdjustmentNavigation(txWithAdjustment)).toBe(true);
  });
});

describe('Navigation State Persistence', () => {
  it('parses navigation state from URL', () => {
    const state = parseNavigationState('/transactions?category=food&date=2024-01-15');
    expect(state.category).toBe('food');
    expect(state.date).toBe('2024-01-15');
  });

  it('parses empty state from URL without params', () => {
    const state = parseNavigationState('/transactions');
    expect(state.category).toBeUndefined();
    expect(state.date).toBeUndefined();
  });

  it('builds navigation URL with state', () => {
    const url = buildNavigationUrl('/transactions', { category: 'food', date: '2024-01-15' });
    expect(url).toContain('category=food');
    expect(url).toContain('date=2024-01-15');
  });

  it('builds URL without state', () => {
    const url = buildNavigationUrl('/transactions', {});
    expect(url).toBe('/transactions');
  });
});

describe('Navigation Error Handling', () => {
  it('creates navigation error with correct structure', () => {
    const error = createNavigationError('invalid_route', 'Test error', '/test');
    expect(error.type).toBe('invalid_route');
    expect(error.message).toBe('Test error');
    expect(error.originalPath).toBe('/test');
  });

  it('returns correct error message for invalid_route', () => {
    const error = createNavigationError('invalid_route', 'Test');
    expect(getNavigationErrorMessage(error)).toBe('The page you are trying to navigate to does not exist.');
  });

  it('returns correct error message for missing_params', () => {
    const error = createNavigationError('missing_params', 'Test');
    expect(getNavigationErrorMessage(error)).toBe('Some required information is missing for navigation.');
  });

  it('returns correct error message for unauthorized', () => {
    const error = createNavigationError('unauthorized', 'Test');
    expect(getNavigationErrorMessage(error)).toBe('You do not have permission to access this page.');
  });

  it('returns correct error message for not_found', () => {
    const error = createNavigationError('not_found', 'Test');
    expect(getNavigationErrorMessage(error)).toBe('The requested page could not be found.');
  });

  it('returns correct error message for server_error', () => {
    const error = createNavigationError('server_error', 'Test');
    expect(getNavigationErrorMessage(error)).toBe('A server error occurred while navigating.');
  });

  it('detects recoverable errors', () => {
    const error = createNavigationError('invalid_route', 'Test');
    expect(isNavigationErrorRecoverable(error)).toBe(true);
  });

  it('detects non-recoverable errors', () => {
    const error = createNavigationError('unauthorized', 'Test');
    expect(isNavigationErrorRecoverable(error)).toBe(false);
  });
});

describe('Navigation Keyboard Shortcuts', () => {
  it('detects Alt+ArrowLeft as navigation shortcut', () => {
    const event = new KeyboardEvent('keydown', { altKey: true, key: 'ArrowLeft' });
    expect(isNavigationShortcut(event)).toBe(true);
  });

  it('detects Alt+ArrowRight as navigation shortcut', () => {
    const event = new KeyboardEvent('keydown', { altKey: true, key: 'ArrowRight' });
    expect(isNavigationShortcut(event)).toBe(true);
  });

  it('detects Alt+ArrowUp as navigation shortcut', () => {
    const event = new KeyboardEvent('keydown', { altKey: true, key: 'ArrowUp' });
    expect(isNavigationShortcut(event)).toBe(true);
  });

  it('detects Alt+ArrowDown as navigation shortcut', () => {
    const event = new KeyboardEvent('keydown', { altKey: true, key: 'ArrowDown' });
    expect(isNavigationShortcut(event)).toBe(true);
  });

  it('returns false for non-navigation shortcuts', () => {
    const event = new KeyboardEvent('keydown', { altKey: false, key: 'ArrowLeft' });
    expect(isNavigationShortcut(event)).toBe(false);
  });
});
