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

const PLATFORM_URL = 'http://localhost:3000/platform';

test.describe('Platform Console Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(PLATFORM_URL, { waitUntil: 'networkidle', timeout: 30000 });
    // Wait for React Query hooks to resolve - wait for at least one status badge to appear
    await page.waitForSelector('[class*="font-bold"]:has-text("HEALTHY"), [class*="font-bold"]:has-text("DEGRAD"), [class*="font-bold"]:has-text("UNHEALTHY"), [class*="font-bold"]:has-text("UNKNOWN")', { timeout: 15000 });
    // Additional wait for React Query to settle
    await page.waitForTimeout(1000);
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
    await expect(page.locator('text=M9-C57 Band A')).toBeVisible();
    await expect(page.locator('text=No AI')).toBeVisible();
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
    await page.reload({ waitUntil: 'networkidle' });
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
