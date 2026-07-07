import { test, expect } from '@playwright/test'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
    // Wait for data to load
    await page.waitForSelector('[data-testid="dashboard-kpi-row"]', { timeout: 10000 })
  })

  test('KPI row renders all four cards', async ({ page }) => {
    await expect(page.getByTestId('dashboard-kpi-row')).toBeVisible()
    await expect(page.getByTestId('kpi-net-cash-flow')).toBeVisible()
    await expect(page.getByTestId('kpi-savings-rate')).toBeVisible()
    await expect(page.getByTestId('kpi-emi-ratio')).toBeVisible()
    await expect(page.getByTestId('kpi-buffer-days')).toBeVisible()
  })

  test('cashflow chart section renders', async ({ page }) => {
    const chartSection = page.getByTestId('cashflow-chart-section')
    await expect(chartSection).toBeVisible()
    // Chart uses Recharts SVG
    await expect(chartSection.locator('svg')).toBeVisible({ timeout: 5000 })
  })

  test('behavior score section renders', async ({ page }) => {
    await expect(page.getByTestId('behavior-score-section')).toBeVisible()
  })

  test('insights section renders', async ({ page }) => {
    await expect(page.getByTestId('insights-section')).toBeVisible()
  })

  test('recent transactions section renders', async ({ page }) => {
    await expect(page.getByTestId('recent-transactions-section')).toBeVisible()
  })

  test('no console errors on load', async ({ page }) => {
    const errors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text())
    })
    await page.goto('/dashboard')
    await page.waitForTimeout(2000)
    expect(errors.filter(e => !e.includes('favicon'))).toHaveLength(0)
  })
})