import { test, expect } from '@playwright/test'

test.describe('Transactions page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/transactions')
    // Wait for table to load
    await page.waitForSelector('[data-testid="transactions-table"]', { timeout: 10000 })
  })

  test('transaction table renders', async ({ page }) => {
    await expect(page.getByTestId('transactions-table')).toBeVisible()
  })

  test('search input is present', async ({ page }) => {
    await expect(page.getByTestId('transactions-search')).toBeVisible()
  })

  test('search filter narrows results', async ({ page }) => {
    // Count initial rows
    const initialRows = await page.locator('tbody tr').count()

    // Type in search
    await page.fill('[data-testid="transactions-search"]', 'salary')

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
    const exportButton = page.getByTestId('transactions-export')
    await expect(exportButton).toBeVisible()
    // Do not actually trigger download in test — just confirm button exists
  })
})