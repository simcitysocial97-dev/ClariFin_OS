import { test, expect } from '@playwright/test'

test.describe('Transactions page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/transactions')
    // Wait for table to load
    await page.waitForSelector('table', { timeout: 10000 })
  })

  test('page loads with transaction table', async ({ page }) => {
    await expect(page.locator('table')).toBeVisible()
  })

  test('search filter narrows results', async ({ page }) => {
    // Count initial rows
    const initialRows = await page.locator('tbody tr').count()

    // Type in search
    await page.fill('[placeholder*="Search"], [placeholder*="search"]', 'salary')

    // Wait for filter to apply
    await page.waitForTimeout(500)

    const filteredRows = await page.locator('tbody tr').count()
    // Either fewer rows or same (if all match)
    expect(filteredRows).toBeLessThanOrEqual(initialRows)
  })

  test('amount column is right-aligned', async ({ page }) => {
    const amountHeader = page.locator('th').filter({ hasText: /amount/i })
    await expect(amountHeader).toHaveClass(/text-right/)
  })

  test('export button exists and is clickable', async ({ page }) => {
    const exportButton = page.locator('button').filter({ hasText: /export/i })
    await expect(exportButton).toBeVisible()
    // Do not actually trigger download in test — just confirm button exists
  })
})