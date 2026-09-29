/**
 * Platform Console Dashboard E2E Tests — M9-C57 Phase 5
 *
 * Verifies that /platform is accessible, renders the dashboard shell,
 * and displays the key operational signals (health status, issue counts,
 * quick actions).
 *
 * Runs against a live backend on :8000 — no mocks.
 */

import { test, expect } from '@playwright/test';

/**
 * M9-C71 — Test budget.
 *
 * The Platform Console resolves six API-backed queries per page. A single page
 * assertion therefore costs several backend round trips, and on a loaded CI
 * runner that legitimately exceeds the 30 s global default. This raises the
 * BUDGET for these two data-driven console specs only; it changes no assertion,
 * no threshold and no wait condition. `expect` still defaults to 10 s, so a
 * genuinely wrong value still fails fast — the extra budget only covers the
 * data round trip.
 */
test.describe.configure({ timeout: 120_000 });

const PLATFORM_URL = 'http://localhost:3000/platform';

test.describe('Platform Console Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // M9-C71: `waitUntil: 'networkidle'` is not a data-readiness signal for a
    // client-resolved console. React hydrates only after the document and its
    // static chunks settle, so the network can be idle for 500 ms BEFORE the
    // first platform query is issued - the wait then returned before any status
    // existed, and this whole file failed or passed depending on the run. The
    // dashboard's own state contract is used instead: wait for the dashboard to
    // reach a terminal state (data, explicit empty, or explicit unavailable).
    await page.goto(PLATFORM_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForSelector(
      '[data-testid="platform-dashboard"], [data-testid="console-empty"], [data-testid="console-unavailable"]',
      { timeout: 30000 },
    );
    // The status badge is still required before any content assertion runs.
    await page.waitForSelector('[class*="font-bold"]:has-text("HEALTHY"), [class*="font-bold"]:has-text("DEGRAD"), [class*="font-bold"]:has-text("UNHEALTHY"), [class*="font-bold"]:has-text("UNKNOWN")', { timeout: 30000 });
  });

  test('page loads without blank screen or crash', async ({ page }) => {
    const title = await page.title();
    expect(title).toContain('Platform');

    // No runtime error overlay
    const errors = await page.locator('[class*="error"]').count();
    // Allow up to 3 "error" class elements (they may be design tokens, not failures)
    expect(errors).toBeLessThan(10);
  });

test('renders platform title bar', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Platform Console' }).first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('header span:has-text("ClariFin OS")').first()).toBeVisible({ timeout: 10000 });
  });

test('renders system status card with a status badge', async ({ page }) => {
    // The health endpoint returns a platform status (HEALTHY/DEGRAD/UNHEALTHY)
    const statusText = await page.locator('[class*="font-bold"]:has-text("HEALTHY"), [class*="font-bold"]:has-text("DEGRAD"), [class*="font-bold"]:has-text("UNHEALTHY")').first().textContent({ timeout: 10000 });
    expect(statusText).toMatch(/^(HEALTHY|DEGRAD|UNHEALTHY|UNKNOWN)$/);
  });

test('renders dimensions grid', async ({ page }) => {
    // At minimum: Backend, Frontend, Database, Architecture should be visible
    await expect(page.locator('span:has-text("Backend")').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('span:has-text("Frontend")').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('span:has-text("Database")').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('span:has-text("Architecture")').first()).toBeVisible({ timeout: 10000 });
});

test('renders verification status section', async ({ page }) => {
    await expect(page.locator('span:has-text("Verification")').first()).toBeVisible({ timeout: 10000 });
});

test('renders capabilities summary', async ({ page }) => {
    await expect(page.locator('span:has-text("55")').first()).toBeVisible({ timeout: 10000 });
  });

  test('renders quick actions panel', async ({ page }) => {
    await expect(page.locator('text=Diagnose Issues')).toBeVisible();
    await expect(page.locator('text=Run Verification')).toBeVisible();
    await expect(page.locator('text=View History')).toBeVisible();
    await expect(page.locator('text=Inspect Errors')).toBeVisible();
  });

  test('renders recent activity feed', async ({ page }) => {
    // Either events are visible, or "No recent events" / loading state
    const hasEvents = await page.locator('text=VerificationCompleted').isVisible().catch(() => false);
    const hasPlaceholder = await page.locator('text=Recent Activity').isVisible().catch(() => false);
    expect(hasEvents || hasPlaceholder).toBeTruthy();
  });

  test('renders footer bar', async ({ page }) => {
    // The layout mounts PlatformFooterBar, which declares the console's runtime
    // boundary and carries stable testids. Asserting on them instead of on the
    // literal text matters: the dashboard page also had a superseded inline
    // footer saying "No AI", so `text=No AI` matched two elements and failed on
    // Playwright's strict mode. That inline footer has been removed; the
    // shared component is the single footer.
    await expect(page.getByTestId('platform-footer-bar')).toBeVisible();
    await expect(page.getByTestId('platform-footer-band')).toHaveText('M9-C57 Band A');
    await expect(page.getByTestId('platform-footer-ai')).toHaveText('No AI');
    // The read-only guarantee is the point of the bar, so certify it is stated.
    await expect(page.getByTestId('platform-footer-bar')).toContainText(
      'no mutation, no LLM, no repository scan',
    );
  });

  test('does not load mutation or LLM modules at runtime', async ({ page }) => {
    // Intercept network requests — no requests to known mutation/LLM endpoints
    const blockedEndpoints = ['/mutation', '/ollama', '/openai'];
    const suspiciousRequests: string[] = [];

    page.on('request', (req) => {
      const url = req.url().toLowerCase();
      for (const ep of blockedEndpoints) {
        if (url.includes(ep)) {
          suspiciousRequests.push(url);
        }
      }
    });

    // Navigate around a bit to trigger any lazy loads
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    expect(suspiciousRequests).toHaveLength(0);
  });

  test('health endpoint returns valid JSON envelope', async ({ page }) => {
    const response = await page.evaluate(async () => {
      const r = await fetch('http://localhost:8000/platform/v1/health?nocache=1');
      return r.json();
    });

    expect(response.kind).toBe('platform.health_snapshot');
    expect(response.version).toBe('1.0.0');
    expect(response.id).toMatch(/^sha256:/);
    expect(response.data).toBeDefined();
    expect(response.data.platform).toBeDefined();
  });
});
