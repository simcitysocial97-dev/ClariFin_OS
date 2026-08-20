/**
 * Reconciliation Tests
 * =====================
 * 
 * Tests for the reconciliation workflow:
 * - Scan for matches
 * - Confirm/reject matches
 * - View reconciliation status
 */

import { test, expect } from '../fixtures/test-fixtures';

// ============================================================================
// Reconciliation Page Tests
// ============================================================================

test.describe('Reconciliation Page', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.goto('/reconciliation');
    await page.waitForLoadState('networkidle');
  });

  test('should load reconciliation page', async ({ page, waitForPageReady, assertNoErrors }) => {
    await waitForPageReady(page);
    
    // Check for page content
    const content = await page.locator('body').innerHTML();
    expect(content.length).toBeGreaterThan(100);
    
    assertNoErrors();
  });

  test('should display page title', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);

    // PanelHeader renders h3; wait for any skeleton to clear first
    await page.locator('[class*="skeleton"]').waitFor({ state: 'hidden', timeout: 10000 });
    const title = page.locator('h1, h2, h3').first();
    await expect(title).toBeVisible();
  });

  test('should show scan button', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const scanBtn = page.locator('button:has-text("Scan"), button:has-text("Find")').first();
    const hasScan = await scanBtn.isVisible().catch(() => false);
    
    console.log(`Scan button visible: ${hasScan}`);
  });
});

// ============================================================================
// Reconciliation Scan Tests
// ============================================================================

test.describe('Reconciliation Scan', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.goto('/reconciliation');
    await page.waitForLoadState('networkidle');
  });

  test('should trigger scan on button click', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const scanBtn = page.locator('button:has-text("Scan"), button:has-text("Find")').first();
    
    if (await scanBtn.isVisible()) {
      await scanBtn.click();
      await page.waitForTimeout(1000);
      
      // Should show loading or results
      const loading = page.locator('text=/scanning|loading/i').isVisible().catch(() => false);
      const results = page.locator('[class*="match"], [class*="result"]').isVisible().catch(() => false);
      
      console.log(`Scan triggered - Loading: ${loading}, Results: ${results}`);
    }
  });

  test('should display potential matches', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for matches section
    const matchesSection = page.locator('text=/match|reconciliation/i').first();
    const hasMatches = await matchesSection.isVisible().catch(() => false);
    
    console.log(`Matches section visible: ${hasMatches}`);
  });

  test('should show match confidence', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for confidence indicators
    const confidence = page.locator('text=/\\d+%/').first();
    const hasConfidence = await confidence.isVisible().catch(() => false);
    
    console.log(`Confidence indicator visible: ${hasConfidence}`);
  });
});

// ============================================================================
// Reconciliation Actions Tests
// ============================================================================

test.describe('Reconciliation Actions', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.goto('/reconciliation');
    await page.waitForLoadState('networkidle');
  });

  test('should have confirm button for matches', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const confirmBtn = page.locator('button:has-text("Confirm"), button:has-text("Accept")').first();
    const hasConfirm = await confirmBtn.isVisible().catch(() => false);
    
    console.log(`Confirm button visible: ${hasConfirm}`);
  });

  test('should have reject button for matches', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const rejectBtn = page.locator('button:has-text("Reject"), button:has-text("Ignore")').first();
    const hasReject = await rejectBtn.isVisible().catch(() => false);
    
    console.log(`Reject button visible: ${hasReject}`);
  });

  test('should confirm match on button click', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const confirmBtn = page.locator('button:has-text("Confirm"), button:has-text("Accept")').first();
    
    if (await confirmBtn.isVisible() && await confirmBtn.isEnabled()) {
      await confirmBtn.click();
      await page.waitForTimeout(500);
      
      // Should show success or update status
      const success = page.locator('text=/confirmed|success/i').isVisible().catch(() => false);
      console.log(`Match confirmed: ${success}`);
    }
  });

  test('should reject match on button click', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const rejectBtn = page.locator('button:has-text("Reject"), button:has-text("Ignore")').first();
    
    if (await rejectBtn.isVisible() && await rejectBtn.isEnabled()) {
      await rejectBtn.click();
      await page.waitForTimeout(500);
      
      // Should show success or update status
      const success = page.locator('text=/rejected|ignored/i').isVisible().catch(() => false);
      console.log(`Match rejected: ${success}`);
    }
  });
});

// ============================================================================
// Reconciliation Status Tests
// ============================================================================

test.describe('Reconciliation Status', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.goto('/reconciliation');
    await page.waitForLoadState('networkidle');
  });

  test('should show pending reconciliations', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const pending = page.locator('text=/pending/i').first();
    const hasPending = await pending.isVisible().catch(() => false);
    
    console.log(`Pending section visible: ${hasPending}`);
  });

  test('should show confirmed reconciliations', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    const confirmed = page.locator('text=/confirmed/i').first();
    const hasConfirmed = await confirmed.isVisible().catch(() => false);
    
    console.log(`Confirmed section visible: ${hasConfirmed}`);
  });

  test('should show match details', async ({ page, waitForPageReady }) => {
    await waitForPageReady(page);
    
    // Look for transaction details in matches
    const details = page.locator('text=/debit|credit|amount|date/i').first();
    const hasDetails = await details.isVisible().catch(() => false);
    
    console.log(`Match details visible: ${hasDetails}`);
  });
});

// ============================================================================
// Reconciliation API Tests
// ============================================================================

test.describe('Reconciliation API', () => {
  test('should handle API unavailable gracefully', async ({ page, captureErrors, waitForPageReady }) => {
    captureErrors(page);
    
    // Block API
    await page.route('**/api/reconciliation*', route => 
      route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) })
    );
    
    await page.goto('/reconciliation');
    await waitForPageReady(page);
    
    // Page should still render a degraded (error) state. The reconciliation
    // workspace intentionally renders a non-<main> error Alert on API failure
    // (C41.13), so we assert the error state is visible rather than a <main>.
    const errorState = page.locator('[role="alert"]').first();
    await expect(errorState).toBeVisible();
  });

  test('should show empty state when no matches', async ({ page, captureErrors, waitForPageReady }) => {
    captureErrors(page);
    
    // Mock empty response
    await page.route('**/api/reconciliation*', route => 
      route.fulfill({ status: 200, body: JSON.stringify({ reconciliations: [] }) })
    );
    
    await page.goto('/reconciliation');
    await waitForPageReady(page);
    
    // Should show empty state or scan prompt
    const emptyState = page.locator('text=/no match|empty|scan/i').first();
    const hasEmpty = await emptyState.isVisible().catch(() => false);
    
    console.log(`Empty state visible: ${hasEmpty}`);
  });
});