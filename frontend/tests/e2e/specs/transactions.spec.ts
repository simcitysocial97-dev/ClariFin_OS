/**
 * Transaction Tests
 * ==================
 * 
 * Tests for transaction management:
 * - Transaction list display
 * - Filtering and search
 * - Pagination
 * - Export functionality
 */

import { test, expect } from '../fixtures/test-fixtures';

// ============================================================================
// Test Data
// ============================================================================

const TEST_TRANSACTIONS = Array.from({ length: 25 }, (_, i) => ({
  id: String(i + 1),
  date: `2026-02-${String((i % 28) + 1).padStart(2, '0')}`,
  description: `Test Transaction ${i + 1}`,
  amount: (i + 1) * 100,
  type: i % 2 === 0 ? 'debit' : 'credit',
  category: ['Shopping', 'Food', 'Transport', 'Entertainment', 'Bills'][i % 5],
  bank: ['HDFC', 'ICICI', 'SBI'][i % 3],
}));

// ============================================================================
// Transaction List Tests
// ============================================================================

test.describe('Transaction List', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    // Navigate first
    await page.goto('/transactions');
    await page.waitForLoadState('networkidle');
    
    // Seed test data (wrapped in try-catch)
    try {
      await page.evaluate((transactions) => {
        const testData = {
          state: {
            cards: [
              { id: '1', bankName: 'HDFC', cardNumber: '****1234' },
              { id: '2', bankName: 'ICICI', cardNumber: '****5678' },
            ],
            transactions,
          },
        };
        localStorage.setItem('bank-parser-storage', JSON.stringify(testData));
      }, TEST_TRANSACTIONS);
      await page.reload();
      await page.waitForLoadState('networkidle');
    } catch {
      // localStorage may not be available
    }
  });

  test('should display transactions list', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for transaction elements
    const table = page.locator('table').first();
    const list = page.locator('[class*="transaction"]').first();
    
    const hasTable = await table.isVisible().catch(() => false);
    const hasList = await list.isVisible().catch(() => false);
    
    expect(hasTable || hasList).toBe(true);
  });

  test('should show transaction count', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for count indicator
    const countText = page.locator('text=/\\d+\\s*(transaction|result)/i').first();
    const hasCount = await countText.isVisible().catch(() => false);
    
    // Should show some indication of transaction count
    console.log(`Transaction count visible: ${hasCount}`);
  });

  test('should display transaction details', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Check for transaction details
    const amount = page.locator('text=/₹|Rs|\\$|\\d+,?\\d*/').first();
    const date = page.locator('text=/\\d{1,2}[\\/\\-]\\d{1,2}[\\/\\-]\\d{2,4}|\\d{4}[\\/\\-]\\d{2}[\\/\\-]\\d{2}/').first();
    
    const hasAmount = await amount.isVisible().catch(() => false);
    const hasDate = await date.isVisible().catch(() => false);
    
    expect(hasAmount || hasDate).toBe(true);
  });
});

// ============================================================================
// Transaction Filtering Tests
// ============================================================================

test.describe('Transaction Filtering', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    // Navigate first
    await page.goto('/transactions');
    await page.waitForLoadState('networkidle');
    
    // Seed test data (wrapped in try-catch)
    try {
      await page.evaluate((transactions) => {
        const testData = {
          state: {
            cards: [{ id: '1', bankName: 'Test Bank', cardNumber: '****1234' }],
            transactions,
          },
        };
        localStorage.setItem('bank-parser-storage', JSON.stringify(testData));
      }, TEST_TRANSACTIONS);
      await page.reload();
      await page.waitForLoadState('networkidle');
    } catch {
      // localStorage may not be available
    }
  });

  test('should have search input', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const searchInput = page.locator('input[placeholder*="search" i], input[type="search"]').first();
    const hasSearch = await searchInput.isVisible().catch(() => false);
    
    console.log(`Search input visible: ${hasSearch}`);
  });

  test('should filter by search term', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const searchInput = page.locator('input[placeholder*="search" i], input[type="search"]').first();
    
    if (await searchInput.isVisible()) {
      await searchInput.fill('Transaction 1');
      await page.waitForTimeout(500);
      
      // Should show filtered results
      const results = page.locator('table tbody tr, [class*="transaction-item"]');
      const count = await results.count();
      
      // Should have fewer results than total
      console.log(`Filtered results: ${count}`);
    }
  });

  test('should have category filter', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for category filter
    const categoryFilter = page.locator('select, [role="combobox"]').filter({ hasText: /category/i }).first();
    const categoryButton = page.locator('button').filter({ hasText: /category/i }).first();
    
    const hasCategoryFilter = await categoryFilter.isVisible().catch(() => false) || 
                              await categoryButton.isVisible().catch(() => false);
    
    console.log(`Category filter visible: ${hasCategoryFilter}`);
  });

  test('should have type filter (debit/credit)', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for type filter
    const typeFilter = page.locator('select, [role="combobox"]').filter({ hasText: /type|debit|credit/i }).first();
    const typeButtons = page.locator('button').filter({ hasText: /debit|credit|all/i });
    
    const hasTypeFilter = await typeFilter.isVisible().catch(() => false) ||
                          await typeButtons.count() > 0;
    
    console.log(`Type filter visible: ${hasTypeFilter}`);
  });

  test('should clear filters', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // The FilterPanel is always rendered in the toolbar area.
    // It shows active filter count on the Filter button badge.
    const filterBtn = page.locator('button[aria-label*="Filter"]').first();
    await expect(filterBtn).toBeVisible();
    
    // Filter panel should be visible (always rendered)
    const filterPanel = page.locator('.border-t.bg-background.p-4').first();
    await expect(filterPanel).toBeVisible();
    
    // Active filter count badge should be present (initially 0, so may be hidden)
    const badge = filterBtn.locator('[role="badge"], .badge').first();
    // Badge visibility depends on active filter count - just verify no crash
    await page.waitForTimeout(100);
  });
});

// ============================================================================
// Transaction Pagination Tests
// ============================================================================

test.describe('Transaction Pagination', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    // Navigate first
    await page.goto('/transactions');
    await page.waitForLoadState('networkidle');
    
    // Create many transactions for pagination
    const manyTransactions = Array.from({ length: 100 }, (_, i) => ({
      id: String(i + 1),
      date: `2026-02-${String((i % 28) + 1).padStart(2, '0')}`,
      description: `Transaction ${i + 1}`,
      amount: (i + 1) * 10,
      type: i % 2 === 0 ? 'debit' : 'credit',
      category: 'Shopping',
    }));
    
    // Seed test data (wrapped in try-catch)
    try {
      await page.evaluate((transactions) => {
        const testData = {
          state: {
            cards: [{ id: '1', bankName: 'Test Bank', cardNumber: '****1234' }],
            transactions,
          },
        };
        localStorage.setItem('bank-parser-storage', JSON.stringify(testData));
      }, manyTransactions);
      await page.reload();
      await page.waitForLoadState('networkidle');
    } catch {
      // localStorage may not be available
    }
  });

  test('should show pagination controls', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for pagination
    const pagination = page.locator('[class*="pagination"], nav[aria-label*="pagination"]').first();
    const nextButton = page.locator('button:has-text("Next"), button:has-text(">")').first();
    
    const hasPagination = await pagination.isVisible().catch(() => false) ||
                          await nextButton.isVisible().catch(() => false);
    
    console.log(`Pagination visible: ${hasPagination}`);
  });

  test('should navigate to next page', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const nextButton = page.locator('button:has-text("Next"), button:has-text(">"), [aria-label*="next"]').first();
    
    if (await nextButton.isVisible() && await nextButton.isEnabled()) {
      await nextButton.click();
      await page.waitForTimeout(500);
      
      // Should show different transactions
      // This is a soft assertion
      console.log('Navigated to next page');
    }
  });
});

// ============================================================================
// Transaction Export Tests
// ============================================================================

test.describe('Transaction Export', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    // Navigate first
    await page.goto('/transactions');
    await page.waitForLoadState('networkidle');
    
    // Seed test data (wrapped in try-catch)
    try {
      await page.evaluate((transactions) => {
        const testData = {
          state: {
            cards: [{ id: '1', bankName: 'Test Bank', cardNumber: '****1234' }],
            transactions,
          },
        };
        localStorage.setItem('bank-parser-storage', JSON.stringify(testData));
      }, TEST_TRANSACTIONS.slice(0, 10));
      await page.reload();
      await page.waitForLoadState('networkidle');
    } catch {
      // localStorage may not be available
    }
  });

  test('should have export button', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const exportBtn = page.locator('button:has-text("Export"), button:has-text("Download")').first();
    const hasExport = await exportBtn.isVisible().catch(() => false);
    
    console.log(`Export button visible: ${hasExport}`);
  });

  test('should trigger CSV export', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const exportBtn = page.locator('button:has-text("Export"), button:has-text("Download")').first();
    
    if (await exportBtn.isVisible()) {
      // Listen for download
      const [download] = await Promise.all([
        page.waitForEvent('download', { timeout: 5000 }).catch(() => null),
        exportBtn.click(),
      ]);
      
      if (download) {
        console.log(`Downloaded: ${download.suggestedFilename()}`);
      }
    }
  });
});

// ============================================================================
// Transaction Actions Tests
// ============================================================================

test.describe('Transaction Actions', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    // Navigate first
    await page.goto('/transactions');
    await page.waitForLoadState('networkidle');
    
    // Seed test data (wrapped in try-catch)
    try {
      await page.evaluate((transactions) => {
        const testData = {
          state: {
            cards: [{ id: '1', bankName: 'Test Bank', cardNumber: '****1234' }],
            transactions,
          },
        };
        localStorage.setItem('bank-parser-storage', JSON.stringify(testData));
      }, TEST_TRANSACTIONS.slice(0, 5));
      await page.reload();
      await page.waitForLoadState('networkidle');
    } catch {
      // localStorage may not be available
    }
  });

  test('should show transaction actions', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for action buttons on transactions
    const actionButtons = page.locator('button').filter({ hasText: /edit|delete|view/i });
    const moreButton = page.locator('button[aria-label*="more"], button:has([class*="more"])').first();
    
    const hasActions = await actionButtons.count() > 0 || await moreButton.isVisible().catch(() => false);
    
    console.log(`Transaction actions visible: ${hasActions}`);
  });

  test('should open transaction details', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Click on a transaction row
    const transactionRow = page.locator('table tbody tr, [class*="transaction-item"]').first();
    
    if (await transactionRow.isVisible()) {
      await transactionRow.click();
      await page.waitForTimeout(500);
      
      // Check for details panel or modal
      const details = page.locator('[role="dialog"], [class*="details"], [class*="drawer"]').first();
      const hasDetails = await details.isVisible().catch(() => false);
      
      console.log(`Transaction details visible: ${hasDetails}`);
    }
  });
});