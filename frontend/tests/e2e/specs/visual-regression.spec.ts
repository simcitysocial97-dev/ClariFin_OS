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

// Pages to snapshot.
//
// M10-R3 (L7): `/categories`, `/analytics` and `/import` were removed. They are REDIRECT
// ALIASES, not pages — `lib/config/navigation.ts:78` maps `/analytics` to
// `/dashboard?view=analytics`, and the hub ignores the query, so the snapshot was really a
// second capture of the dashboard under a different name.
//
// Measured on chromium against the committed baselines, `analytics-page` was the single
// largest remaining difference at **209,502 pixels (23% of the frame)** — while every real
// page sat at 0.01-0.04. A 23% diff on a route that renders the dashboard is a harness
// defect asserting a dead deep link, not a product regression, and it was the loudest
// thing in the run.
//
// Their real surfaces are already covered: `categories` -> `/settings?tab=categories`,
// `import` -> `/transactions?tab=import`, both of which are snapshotted under their real
// names. Keeping the aliases bought no coverage and cost a third of a frame's worth of
// signal.
const PAGES = [
  { path: '/', name: 'home' },
  { path: '/dashboard', name: 'dashboard' },
  { path: '/transactions', name: 'transactions' },
  { path: '/cards', name: 'cards' },
  { path: '/settings', name: 'settings' },
  { path: '/behaviour', name: 'behavior' },
  { path: '/reconciliation', name: 'reconciliation' },
];

// ============================================================================
// Non-deterministic runtime readouts
// ============================================================================

/**
 * The financial workspace footer (components/os-shell/bottom-status-bar.tsx)
 * reports LIVE cache counters - "<n> cached" and "<n>% hit rate" - read from the
 * in-page performance runtime. Those values depend on whatever requests the page
 * happened to make before the screenshot, so they differ on every run and on
 * every page. Diffing them makes the whole footer unstable: the recorded
 * baselines differ from every render by ~900-2400 pixels, all inside the footer
 * strip (verified - the diff bounding box is x in [196,1262], y in [485,716] on a
 * 1280x720 desktop capture and x in [194,366], y in [558,660] on a 375x667
 * mobile capture - the same element across all 18 affected snapshots).
 *
 * Playwright's `mask` is the mechanism for exactly this case: it paints the
 * matched elements with a solid block before capture, so the volatile readouts
 * are excluded from the pixel comparison while the REST of the footer - and the
 * whole page - is still compared. Masking two labels is deliberately narrower
 * than masking the footer or the screen, and it changes no assertion: the
 * stable content around the readouts is still verified pixel-for-pixel.
 *
 * The readouts are deliberately NOT removed from the product. An operator needs
 * to see cache health; only the *comparison* of a live counter is meaningless.
 */
function volatileRuntimeReadouts(page: import('@playwright/test').Page) {
  return [
    page.locator('footer span', { hasText: /cached$/ }),
    page.locator('footer span', { hasText: /% hit rate$/ }),
  ];
}

/**
 * A snapshot of a page that is still loading is not a snapshot of the page.
 *
 * `waitForPageReady` waits for `domcontentloaded` and for React to hydrate
 * (the root element having children). Neither means the page's async queries
 * have resolved, so a data-driven page can still be showing its loading state
 * when the screenshot is taken. Playwright's own stability check cannot catch
 * this either — "stable" means no layout shift, not "data arrived" — and it
 * reports "captured a stable screenshot" of a loading dashboard quite happily.
 *
 * That is what the home-page baseline was catching. On a cold CI container the
 * dashboard is still in its loading state when the capture happens: the panel
 * header renders, the body renders as two thin placeholder bars, and the whole
 * KPI row, analytics summary bar and chart panels are absent. Against a baseline
 * containing all of them, that is ~11% of all pixels differing, identically on
 * all three attempts including both retries — a signature of a deterministic
 * state, not a flake. The mobile-chrome job passed in the same run because its
 * layout and timing differ.
 *
 * Two loading affordances have to be covered, and an earlier version of this
 * helper only covered the first, which is why it did not work:
 *
 *   - `.animate-pulse` — the `Skeleton` primitive in components/ui/skeleton.tsx
 *     and the in-place placeholders in chart-container.tsx and financial-table.tsx
 *   - `.fin-loading` / `.fin-loading-pulse` — the `PanelBody loading` state in
 *     components/primitives/panel/panel.tsx, which is what the dashboard and
 *     every other panel-based page actually use. It renders no `.animate-pulse`
 *     element at all, so waiting on `.animate-pulse` alone returns immediately.
 *
 * This is deliberately an assertion, not a swallowed wait: if a page never
 * settles, `toHaveCount(0)` fails and the screenshot is never taken. A page
 * that cannot finish loading is a real defect and must fail the run. The
 * snapshot comparison itself is unchanged — same pages, same baselines, same
 * `maxDiffPixels`, same `threshold`.
 */
const LOADING_AFFORDANCES = [
  '.animate-pulse',
  '.fin-loading',
  '.fin-loading-pulse',
  '[class*="skeleton"]',
].join(', ');

async function waitForContentSettled(page: import('@playwright/test').Page) {
  await expect(page.locator(LOADING_AFFORDANCES)).toHaveCount(0, { timeout: 30000 });
}

// ============================================================================
// Full Page Screenshots
// ============================================================================

test.describe('Visual Regression - Full Pages', () => {
  test.beforeEach(async ({ page, captureErrors }) => {
    captureErrors(page);
    // M10-R3 (L7): the blanket setViewportSize({1280x720}) is REMOVED, not narrowed.
    //
    // It ran for every test in every project, so on `mobile-chrome` (Pixel 5 emulation)
    // it overwrote the device metrics before navigation. 19 of that project's 24 tests
    // therefore captured a 1280-wide DESKTOP screenshot and stored it under a
    // `-mobile-chrome-` baseline name. The baselines looked mobile and were not.
    //
    // The viewport is now owned by the project, which is the only place that knows the
    // intended device. Tests that genuinely need a specific viewport must declare it on
    // themselves — a suite-wide override cannot be reconciled with per-project devices.
  });

  for (const pageConfig of PAGES) {
    test(`should match ${pageConfig.name} page snapshot`, async ({ page, waitForPageReady }) => {
      await page.goto(pageConfig.path);
      await waitForPageReady(page);
      await waitForContentSettled(page);

      // Take full page screenshot
      await expect(page).toHaveScreenshot(`${pageConfig.name}-page.png`, {
        mask: volatileRuntimeReadouts(page),
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
    // Same reasoning as the full-page suite (see above): the device belongs to the
    // project, not to a suite-wide override.
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
      await waitForContentSettled(page);

      await expect(page).toHaveScreenshot(`${pageConfig.name}-mobile.png`, {
        mask: volatileRuntimeReadouts(page),
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
        mask: volatileRuntimeReadouts(page),
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
      mask: volatileRuntimeReadouts(page),
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
      mask: volatileRuntimeReadouts(page),
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
    await waitForContentSettled(page);

    await expect(page).toHaveScreenshot('dark-mode-dashboard.png', {
      mask: volatileRuntimeReadouts(page),
      maxDiffPixels: MAX_DIFF_PIXELS,
      threshold: DIFF_THRESHOLD,
      fullPage: true,
    });
  });
});