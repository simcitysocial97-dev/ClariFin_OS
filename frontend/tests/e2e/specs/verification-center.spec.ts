/**
 * Verification Center E2E — M9-C57 Phase 6
 *
 * Requires live backend on :8000. No mocks.
 */

import { test, expect } from '@playwright/test';

const PLATFORM_VERIFICATION = 'http://localhost:3000/platform/verification';

test.describe('Verification Center', () => {
  test('renders capabilities table', async ({ page }) => {
    await page.goto(PLATFORM_VERIFICATION, { waitUntil: 'networkidle', timeout: 30_000 });
    await expect(page.getByRole('heading', { name: 'Verification Center' })).toBeVisible();
    // At least one capability row should appear
    await expect(page.locator('table tbody tr').first()).toBeVisible({ timeout: 10_000 });
  });

  test('Run capability produces a result message', async ({ page }) => {
    await page.goto(PLATFORM_VERIFICATION, { waitUntil: 'networkidle', timeout: 30_000 });
    await page.waitForSelector('table tbody tr', { timeout: 10_000 });
    await page.getByRole('button', { name: 'Run' }).first().click();
    await expect(page.locator('text=platform.verification_run_result')).toBeVisible({ timeout: 15_000 });
  });

  test('Run affected button produces a result', async ({ page }) => {
    await page.goto(PLATFORM_VERIFICATION, { waitUntil: 'networkidle', timeout: 30_000 });
    await page.getByRole('button', { name: 'Run affected' }).click();
    await expect(page.locator('text=platform.verification_run_result')).toBeVisible({ timeout: 15_000 });
  });

  test('Recent runs appear when present', async ({ page }) => {
    await page.goto(PLATFORM_VERIFICATION, { waitUntil: 'networkidle', timeout: 30_000 });
    await page.waitForSelector('table tbody tr', { timeout: 10_000 });
    await expect(page.locator('text=Recent runs')).toBeVisible({ timeout: 10_000 });
  });
});
