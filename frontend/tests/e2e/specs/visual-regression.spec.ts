/**
 * Visual Regression Tests
 * ========================
 * 
 * Screenshot comparison tests for UI consistency:
 * - Page snapshots
 * - Component snapshots
 * - Diff threshold: 0.1%
 */

import { test, expect } from '../fixtures/test-fixtures';


// ============================================================================
// Configuration
// ============================================================================

// CI environments have rendering differences (font rendering, antialiasing, etc.)
// Use a more tolerant threshold for CI, strict for local development
const IS_CI = !!process.env.CI;
const DIFF_THRESHOLD = IS_CI ? 0.01 : 0.001; // 1% in CI, 0.1% locally
const MAX_DIFF_PIXELS = IS_CI ? 500 : 100;

// Pages to snapshot
const PAGES = [
  { path: '/', name: 'home' },
  { path: '/dashboard', name: 'dashboard' },
  { path: '/transactions', name: 'transactions' },
  { path: '/categories', name: 'categories' },
  { path: '/analytics', name: 'analytics' },
  { path: '/cards', name: 'cards' },
  { path: '/import', name: 'import' },
  { path: '/settings', name: 'settings' },
  { path: '/behaviour', name: 'behavior' },
  { path: '/reconciliation', name: 'reconciliation' },
];

// ============================================================================
// Full Page Screenshots
// ============================================================================

test.describe('Visual Regression - Full Pages', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    // Set consistent viewport
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  for (const pageConfig of PAGES) {
    test(`should match ${pageConfig.name} page snapshot`, async ({ page, waitForPageReady }) => {
      await page.goto(pageConfig.path);
      await waitForPageReady(page);
      
      // Take full page screenshot
      await expect(page).toHaveScreenshot(`${pageConfig.name}-page.png`, {
        maxDiffPixels: MAX_DIFF_PIXELS,
        threshold: DIFF_THRESHOLD,
        fullPage: true,
      });
    });
  }
});

// ============================================================================
// Component Screenshots
// ============================================================================

test.describe('Visual Regression - Components', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('should match sidebar snapshot', async ({ page, waitForPageReady }) => {
    await page.goto('/');
    await waitForPageReady(page);
    
    const sidebar = page.locator('aside').first();
    
    if (await sidebar.isVisible()) {
      await expect(sidebar).toHaveScreenshot('sidebar.png', {
        maxDiffPixels: MAX_DIFF_PIXELS,
        threshold: DIFF_THRESHOLD,
      });
    }
  });

  test('should match header snapshot', async ({ page, waitForPageReady }) => {
    await page.goto('/');
    await waitForPageReady(page);
    
    // Find header area
    const header = page.locator('header, [class*="header"]').first();
    const hasHeader = await header.isVisible().catch(() => false);
    
    if (hasHeader) {
      await expect(header).toHaveScreenshot('header.png', {
        maxDiffPixels: MAX_DIFF_PIXELS,
        threshold: DIFF_THRESHOLD,
      });
    }
  });

  test('should match upload button snapshot', async ({ page, waitForPageReady }) => {
    await page.goto('/');
    await waitForPageReady(page);
    
    const uploadBtn = page.locator('button:has-text("Upload")').first();
    
    if (await uploadBtn.isVisible()) {
      await expect(uploadBtn).toHaveScreenshot('upload-button.png', {
        maxDiffPixels: MAX_DIFF_PIXELS,
        threshold: DIFF_THRESHOLD,
      });
    }
  });

  test('should match mode toggle snapshot', async ({ page, waitForPageReady }) => {
    await page.goto('/dashboard');
    await waitForPageReady(page);
    
    // Find mode toggle container
    const modeToggle = page.locator('button:has-text("Personal")').first().locator('..');
    const isVisible = await modeToggle.isVisible().catch(() => false);
    
    if (isVisible) {
      await expect(modeToggle).toHaveScreenshot('mode-toggle.png', {
        maxDiffPixels: MAX_DIFF_PIXELS,
        threshold: DIFF_THRESHOLD,
      });
    }
  });
});

// ============================================================================
// Mobile Screenshots
// ============================================================================

test.describe('Visual Regression - Mobile', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.setViewportSize({ width: 375, height: 667 });
  });

  for (const pageConfig of PAGES.slice(0, 5)) { // Test first 5 pages on mobile
    test(`should match ${pageConfig.name} mobile snapshot`, async ({ page, waitForPageReady }) => {
      await page.goto(pageConfig.path);
      await waitForPageReady(page);
      
      await expect(page).toHaveScreenshot(`${pageConfig.name}-mobile.png`, {
        maxDiffPixels: MAX_DIFF_PIXELS,
        threshold: DIFF_THRESHOLD,
        fullPage: true,
      });
    });
  }
});

// ============================================================================
// State-Specific Screenshots
// ============================================================================

test.describe('Visual Regression - States', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('should match empty state snapshot', async ({ page, waitForPageReady }) => {
    await page.goto('/');
    await waitForPageReady(page);
    
    // Clear all data (must navigate first to establish valid origin)
    await page.evaluate(() => localStorage.clear());
    await page.reload();
    await waitForPageReady(page);
    
    // Look for empty state
    const emptyState = page.locator('text=/Welcome|Get started|No data/i').first();
    const hasEmpty = await emptyState.isVisible().catch(() => false);
    
    if (hasEmpty) {
      await expect(page).toHaveScreenshot('empty-state.png', {
        maxDiffPixels: MAX_DIFF_PIXELS,
        threshold: DIFF_THRESHOLD,
      });
    }
  });

  test('should match modal open state', async ({ page, waitForPageReady }) => {
    await page.goto('/');
    await waitForPageReady(page);
    
    // Open upload modal
    const uploadBtn = page.locator('button:has-text("Upload")').first();
    await uploadBtn.click();
    await page.waitForTimeout(500);
    
    const modal = page.locator('[role="dialog"]').first();
    const isVisible = await modal.isVisible().catch(() => false);
    
    if (isVisible) {
      await expect(modal).toHaveScreenshot('upload-modal.png', {
        maxDiffPixels: MAX_DIFF_PIXELS,
        threshold: DIFF_THRESHOLD,
      });
    }
  });

  test('should match personal mode snapshot', async ({ page, waitForPageReady }) => {
    await page.goto('/dashboard');
    await waitForPageReady(page);
    
    // Set personal mode
    await page.evaluate(() => {
      localStorage.setItem('clariFin_dashboard_mode', 'personal');
    });
    await page.reload();
    await waitForPageReady(page);
    
    await expect(page).toHaveScreenshot('personal-mode.png', {
      maxDiffPixels: MAX_DIFF_PIXELS,
      threshold: DIFF_THRESHOLD,
      fullPage: true,
    });
  });

  test('should match family mode snapshot', async ({ page, waitForPageReady }) => {
    await page.goto('/dashboard');
    await waitForPageReady(page);
    
    // Set family mode
    await page.evaluate(() => {
      localStorage.setItem('clariFin_dashboard_mode', 'family');
    });
    await page.reload();
    await waitForPageReady(page);
    
    await expect(page).toHaveScreenshot('family-mode.png', {
      maxDiffPixels: MAX_DIFF_PIXELS,
      threshold: DIFF_THRESHOLD,
      fullPage: true,
    });
  });
});

// ============================================================================
// Dark Mode Screenshots
// ============================================================================

test.describe('Visual Regression - Dark Mode', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    await page.setViewportSize({ width: 1280, height: 720 });
    // Ensure dark mode
    await page.evaluate(() => {
      document.documentElement.classList.add('dark');
    });
  });

  test('should match dark mode dashboard', async ({ page, waitForPageReady }) => {
    await page.goto('/');
    await waitForPageReady(page);
    
    await expect(page).toHaveScreenshot('dark-mode-dashboard.png', {
      maxDiffPixels: MAX_DIFF_PIXELS,
      threshold: DIFF_THRESHOLD,
      fullPage: true,
    });
  });
});