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
