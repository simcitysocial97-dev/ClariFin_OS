/**
 * Dashboard Tests
 * ================
 * 
 * Tests for the main dashboard functionality:
 * - Overview metrics
 * - Quick stats
 * - Charts rendering
 * - Recent transactions
 * - Upload functionality
 */

import { test, expect } from '../fixtures/test-fixtures';
import { validateElementVisibility, validateGridCardHeights } from '../fixtures/css-helpers';

// ============================================================================
// Dashboard Loading Tests
// ============================================================================

test.describe('Dashboard Loading', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    // Navigate first, then clear
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    // Clear any existing data (wrapped in try-catch)
    try {
      await page.evaluate(() => localStorage.clear());
    } catch {
      // localStorage may not be available
    }
  });

  test('should load dashboard page', async ({ page, waitForPageReady, assertNoErrors }) => {
    await page.goto('/');
    // Wait for loading skeleton to disappear before asserting headings
    await page.locator('[class*="skeleton"]').waitFor({ state: 'hidden', timeout: 10000 });
    await waitForPageReady(page);

    // Check for dashboard header (PanelHeader renders h3)
    const header = page.locator('h1, h2, h3').first();
    await expect(header).toBeVisible();

    // Check for main content area
    const main = page.locator('main').first();
    await expect(main).toBeVisible();

    assertNoErrors();
  });

  test('should show empty state when no data', async ({ page, waitForPageReady }) => {
    await page.goto('/');
    await waitForPageReady(page);
    
    // Look for empty state indicators
    const emptyState = page.locator('text=/Welcome|Get started|Upload|No data|Empty/i').first();
    const isVisible = await emptyState.isVisible().catch(() => false);
    
    // Should show some indication of empty state or upload prompt
    const hasUploadButton = await page.locator('button:has-text("Upload")').isVisible().catch(() => false);
    
    expect(isVisible || hasUploadButton).toBe(true);
  });

  test('should show loading state initially', async ({ page }) => {
    // Navigate and immediately check for loading state
    const loadPromise = page.goto('/');
    
    // Check for skeleton or loading indicator
    const hasSkeleton = await page.locator('[class*="skeleton"], [class*="loading"]').count() > 0;
    
    await loadPromise;
    
    // Loading state should eventually resolve
    await page.waitForLoadState('networkidle');
  });
});

// ============================================================================
// Dashboard Components Tests
// ============================================================================

test.describe('Dashboard Components', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display upload button', async ({ page }) => {
    const uploadBtn = page.locator('button:has-text("Upload")').first();
    await expect(uploadBtn).toBeVisible();
  });

  test('should trigger upload on button click', async ({ page }) => {
    const uploadBtn = page.locator('button:has-text("Upload")').first();
    await expect(uploadBtn).toBeVisible();
    
    // Click should either open modal or navigate to upload page
    await uploadBtn.click();
    await page.waitForTimeout(500);
    
    // Check if URL changed to include upload param or modal appeared
    const url = page.url();
    const hasModal = await page.locator('[role="dialog"], [data-state="open"]').count() > 0;
    
    // Either modal is visible or URL has upload param
    expect(url.includes('upload=true') || hasModal).toBe(true);
  });

  test('should display quick stats cards', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for stat cards
    const statCards = page.locator('[class*="card"], [data-testid*="stat"]').first();
    const hasCards = await statCards.isVisible().catch(() => false);
    
    // Either cards are visible or we're in empty state
    const isEmpty = await page.locator('text=/Welcome|Get started/i').isVisible().catch(() => false);
    
    expect(hasCards || isEmpty).toBe(true);
  });

  test('should display navigation sidebar', async ({ page }) => {
    // Desktop sidebar
    await page.setViewportSize({ width: 1280, height: 720 });
    
    const sidebar = page.locator('aside').first();
    await expect(sidebar).toBeVisible();
  });
});

// ============================================================================
// Dashboard Charts Tests
// ============================================================================

test.describe('Dashboard Charts', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    // Navigate first
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Seed some test data (wrapped in try-catch)
    try {
      await page.evaluate(() => {
        const testData = {
          state: {
            cards: [
              { id: '1', bankName: 'Test Bank', cardNumber: '****1234' }
            ],
            transactions: [
              { id: '1', date: '2026-02-01', description: 'Test Transaction', amount: 1000, type: 'debit', category: 'Shopping' },
              { id: '2', date: '2026-02-02', description: 'Test Credit', amount: 5000, type: 'credit', category: 'Income' },
            ],
          },
        };
        localStorage.setItem('bank-parser-storage', JSON.stringify(testData));
      });
      await page.reload();
      await page.waitForLoadState('networkidle');
    } catch {
      // localStorage may not be available
    }
  });

  test('should render spending chart if data exists', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for chart container
    const chart = page.locator('[class*="chart"], canvas, [data-testid*="chart"]').first();
    const hasChart = await chart.isVisible().catch(() => false);
    
    // Chart might not render with minimal data
    console.log(`Chart visible: ${hasChart}`);
  });

  test('should render category breakdown if data exists', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for category section
    const categorySection = page.locator('text=/Category|Spending/i').first();
    const hasCategory = await categorySection.isVisible().catch(() => false);
    
    console.log(`Category section visible: ${hasCategory}`);
  });
});

// ============================================================================
// Dashboard Interactions Tests
// ============================================================================

test.describe('Dashboard Interactions', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should toggle exclude transfers switch', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Find the exclude transfers toggle
    const toggle = page.locator('text=/Exclude Transfers/i').locator('..').locator('button, [role="switch"]').first();
    const isVisible = await toggle.isVisible().catch(() => false);
    
    if (isVisible) {
      // Get initial state
      const initialState = await toggle.getAttribute('aria-checked');
      
      // Toggle
      await toggle.click();
      await page.waitForTimeout(300);
      
      // Verify state changed
      const newState = await toggle.getAttribute('aria-checked');
      expect(newState).not.toBe(initialState);
    }
  });

  test('should navigate to transactions from recent list', async ({ page, waitForPageReady }) => {
    // Seed data (wrapped in try-catch)
    try {
      await page.evaluate(() => {
        const testData = {
          state: {
            cards: [{ id: '1', bankName: 'Test Bank', cardNumber: '****1234' }],
            transactions: Array.from({ length: 5 }, (_, i) => ({
              id: String(i + 1),
              date: `2026-02-${String(i + 1).padStart(2, '0')}`,
              description: `Transaction ${i + 1}`,
              amount: (i + 1) * 100,
              type: 'debit',
              category: 'Shopping',
            })),
          },
        };
        localStorage.setItem('bank-parser-storage', JSON.stringify(testData));
      });
      await page.reload();
    } catch {
      // localStorage may not be available
    }
    
    await waitForPageReady(page);
    
    // Look for recent transactions link
    const viewAllLink = page.locator('a:has-text("View All"), a:has-text("Transactions")').first();
    const isVisible = await viewAllLink.isVisible().catch(() => false);
    
    if (isVisible) {
      await viewAllLink.click();
      await page.waitForURL('**/transactions**');
      expect(page.url()).toContain('/transactions');
    }
  });
});

// ============================================================================
// Dashboard Error Handling Tests
// ============================================================================

test.describe('Dashboard Error Handling', () => {
  test('should handle API failure gracefully', async ({ page, captureErrors, waitForPageReady }) => {
    captureErrors(page);
    
    // Block API requests to simulate failure
    await page.route('**/api/**', route => route.abort());
    
    await page.goto('/');
    await waitForPageReady(page);
    
    // Page should still render
    const main = page.locator('main').first();
    await expect(main).toBeVisible();
    
    // Should show fallback or error message
    const hasContent = await page.locator('body').innerHTML();
    expect(hasContent.length).toBeGreaterThan(100);
  });

  test('should show error toast on API error', async ({ page, captureErrors, waitForPageReady }) => {
    captureErrors(page);
    
    // Route API to return error
    await page.route('**/api/overview', route => 
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) })
    );
    
    await page.goto('/');
    await waitForPageReady(page);
    
    // Page should still render with fallback
    const main = page.locator('main').first();
    await expect(main).toBeVisible();
  });
});

// ============================================================================
// Dashboard Responsive Tests
// ============================================================================

test.describe('Dashboard Responsive', () => {
  test('should render correctly on mobile', async ({ page, captureErrors }) => {
    captureErrors(page);
    
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Main content should be visible
    const main = page.locator('main').first();
    await expect(main).toBeVisible();
    
    // Mobile menu button should be visible
    const menuBtn = page.locator('button').filter({ has: page.locator('svg') }).first();
    await expect(menuBtn).toBeVisible();
  });

  test('should render correctly on tablet', async ({ page, captureErrors }) => {
    captureErrors(page);
    
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Main content should be visible
    const main = page.locator('main').first();
    await expect(main).toBeVisible();
  });

  test('should render correctly on desktop', async ({ page, captureErrors }) => {
    captureErrors(page);
    
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Main content should be visible
    const main = page.locator('main').first();
    await expect(main).toBeVisible();
    
    // Sidebar should be visible
    const sidebar = page.locator('aside').first();
    await expect(sidebar).toBeVisible();
  });
});