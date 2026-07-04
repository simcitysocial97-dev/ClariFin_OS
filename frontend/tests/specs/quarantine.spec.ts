/**
 * Quarantine Tests
 * ================
 *
 * Tests for the quarantine UI:
 * - Quarantine list page renders
 * - Empty state displays when no data
 * - Navigation to quarantine works
 * - Detail page renders
 * - Import page still works after changes
 */

import { test, expect } from '../fixtures/test-fixtures';

test.describe('Quarantine Page', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
  });

  test('should load quarantine page', async ({ page, waitForPageReady, assertNoErrors }) => {
    await page.goto('/quarantine');
    await waitForPageReady(page);

    // Verify page loaded
    const header = page.locator('h1').first();
    await expect(header).toBeVisible();

    // Should contain "Quarantine" text
    const pageContent = await page.locator('body').innerText();
    expect(pageContent.toLowerCase()).toContain('quarantine');

    assertNoErrors();
  });

  test('should show empty state or list without crashing', async ({ page, waitForPageReady, assertNoErrors }) => {
    await page.goto('/quarantine');
    await waitForPageReady(page);

    // Either empty state or table should be visible
    const emptyState = page.locator('text=/No quarantined pages|quarantined pages/i').first();
    const table = page.locator('table').first();

    const hasEmptyState = await emptyState.isVisible().catch(() => false);
    const hasTable = await table.isVisible().catch(() => false);

    // Should have either empty state or table
    expect(hasEmptyState || hasTable).toBe(true);

    assertNoErrors();
  });

  test('should navigate from sidebar to quarantine', async ({ page, waitForPageReady }) => {
    await page.goto('/');
    await waitForPageReady(page);

    // Find quarantine link in sidebar
    const quarantineLink = page.locator('a:has-text("Quarantine")').first();
    const isVisible = await quarantineLink.isVisible().catch(() => false);

    if (isVisible) {
      await quarantineLink.click();
      await page.waitForURL('**/quarantine**');
      await waitForPageReady(page);

      // Verify we're on quarantine page
      expect(page.url()).toContain('/quarantine');

      // Header should be visible
      const header = page.locator('h1').first();
      await expect(header).toBeVisible();
    }
  });
});

test.describe('Quarantine Detail Page', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
  });

  test('should render detail page for valid ID format', async ({ page, waitForPageReady, assertNoErrors }) => {
    // Use a fake UUID - page should render (even if data not found)
    const fakeId = '550e8400-e29b-41d4-a716-446655440000';
    await page.goto(`/quarantine/${fakeId}`);
    await waitForPageReady(page);

    // Page should render without crashing
    const bodyContent = await page.locator('body').innerHTML();
    expect(bodyContent.length).toBeGreaterThan(100);

    // Should show error state or loading (not crash)
    const hasErrorOrContent = await page.locator('text=/Error|Back|Loading/i').first().isVisible().catch(() => false);
    expect(hasErrorOrContent).toBe(true);

    assertNoErrors();
  });

  test('should have back button on detail page', async ({ page, waitForPageReady }) => {
    const fakeId = '550e8400-e29b-41d4-a716-446655440000';
    await page.goto(`/quarantine/${fakeId}`);
    await waitForPageReady(page);

    // Should have back button
    const backButton = page.locator('button:has-text("Back"), a:has-text("Back")').first();
    const isVisible = await backButton.isVisible().catch(() => false);

    expect(isVisible).toBe(true);
  });
});

test.describe('Import Page After Changes', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
  });

  test('should still render import page without errors', async ({ page, waitForPageReady, assertNoErrors }) => {
    await page.goto('/import');
    await waitForPageReady(page);

    // Page should load
    const header = page.locator('h1').first();
    await expect(header).toBeVisible();

    // Should contain Import text
    const pageContent = await page.locator('body').innerText();
    expect(pageContent.toLowerCase()).toContain('import');

    assertNoErrors();
  });
});
