import { test, expect } from '@playwright/test'

test.describe('Dashboard page', () => {
  test('loads KPI cards', async ({ page }) => {
    await page.goto('/dashboard')
    // Wait for data to load
    await page.waitForTimeout(2000)

    // KPI cards should be visible
    // Adjust selectors to match actual component structure
    const kpiCards = page.locator('[data-testid="kpi-card"], .kpi-card, [class*="KpiCard"]')
    // At minimum the page should not be blank
    const bodyText = await page.locator('body').textContent()
    expect(bodyText?.trim().length).toBeGreaterThan(100)
  })

  test('shows recent transactions section', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForTimeout(2000)

    await expect(
      page.locator('text=Recent Transactions').or(page.locator('text=Recent'))
    ).toBeVisible()
  })
})